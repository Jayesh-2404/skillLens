"""Interactive terminal loop: load index once, suggest per prompt. Stdlib only."""
import os
import shutil
import subprocess
import sys
import textwrap

from skilllens import scan
from skilllens import search

try:
    from skilllens.brand import NAME, TAGLINE
except ImportError:  # pragma: no cover - fallback if run oddly
    try:
        from brand import NAME, TAGLINE
    except ImportError:
        NAME = "SkillLens"
        TAGLINE = "Prompt in, ranked skills out"

BANNER = f"{NAME} - {TAGLINE}\nType a prompt. 1-3 copies a result. help shows commands. exit quits."

HELP_TEXT = """commands:
  <prompt>   search skills for this prompt
  1-9        copy result N as '@skill <prompt>' via clip
  top N      set result count live (e.g. `top 5`); `top` shows current
  roots      print discovered roots inline
  clear      clear screen
  help       show this help
  exit/quit  quit (also Ctrl-C)"""

# ANSI codes (guarded by _color_enabled).
_BOLD = "\x1b[1m"
_CYAN = "\x1b[36m"
_DIM = "\x1b[2m"
_GREEN = "\x1b[32m"
_RESET = "\x1b[0m"


def _color_enabled():
    """True when ANSI color is allowed: NO_COLOR unset and stdout is a tty."""
    if os.environ.get("NO_COLOR") is not None:
        return False
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def _paint(code, text, use_color):
    if use_color:
        return f"{code}{text}{_RESET}"
    return text


def _term_width():
    try:
        size = shutil.get_terminal_size(fallback=(80, 24))
        cols = getattr(size, "columns", None)
        if cols is None:  # pragma: no cover - tolerate tuple mocks
            cols = size[0]
        return int(cols) if int(cols) > 0 else 80
    except Exception:
        return 80


def _trunc_end(text, w):
    if len(text) <= w:
        return text
    if w <= 3:
        return text[:w]
    return text[: w - 3] + "..."


def _trunc_middle(text, w):
    if len(text) <= w:
        return text
    if w <= 4:
        return text[:w]
    n = w - 3
    head = (n + 1) // 2
    tail = n - head
    return text[:head] + "..." + text[-tail:] if tail > 0 else text[:head] + "..."


def _wrap(text, w):
    rows = textwrap.wrap(text, width=w, break_long_words=True, break_on_hyphens=False)
    return rows if rows else [""]


def format_card(i, s, prompt, use_color=True):
    """Return one boxed ASCII card for a suggestion.

    Same info in plain and color modes; only ANSI codes differ.
    Box width is capped to the terminal so no line exceeds it.
    """
    sk = s["skill"]
    name = sk.get("name", "?")
    header = f"{i}. {name} (score {s['score']:.2f}) [{sk.get('source', '?')}]"
    desc_line = f"desc: {sk.get('description', '')}"
    path_line = f"path: {sk.get('path', '')}"
    reason_line = f"reason: {s.get('reason', '')}"
    use_line = f"use: @{name} {prompt}"
    term_width = _term_width()
    needed = max((len(l) for l in (header, desc_line, path_line, reason_line, use_line)), default=0)
    width = min(needed, max(40, term_width - 4))
    # hard guard: box adds "| " + " |" (4 chars); never exceed term_width - 1
    if width + 4 > term_width - 1:
        width = max(20, term_width - 5)
    top = "+" + "-" * (width + 2) + "+"

    def box(visible, painted=None):
        text = painted if painted is not None else visible
        pad = width - len(visible)
        if pad < 0:
            pad = 0
        return f"| {text}{' ' * pad} |"

    header_rows = [_trunc_end(header, width)]
    desc_rows = _wrap(desc_line, width)
    path_rows = [_trunc_middle(path_line, width)]
    reason_rows = _wrap(reason_line, width)
    use_rows = _wrap(use_line, width)

    lines = [top]

    def add(rows, color=None):
        for r in rows:
            if use_color and color:
                lines.append(box(r, _paint(color, r, True)))
            else:
                lines.append(box(r))

    add(header_rows, _BOLD + _CYAN)
    add(desc_rows)
    add(path_rows, _DIM)
    add(reason_rows)
    add(use_rows, _GREEN)
    bottom = "+" + "-" * (width + 2) + "+"
    lines.append(bottom)
    return "\n".join(lines)


def render(suggestions, prompt, use_color=None):
    """Print boxed cards, one per suggestion."""
    if use_color is None:
        use_color = _color_enabled()
    for i, s in enumerate(suggestions, 1):
        print(format_card(i, s, prompt, use_color=use_color))


def _prompt_box_width():
    """Inner width for prompt headers/rules, terminal-capped like cards."""
    term_width = _term_width()
    width = max(40, term_width - 4)
    # hard guard: header/rule lines are width + 4 chars; never exceed term_width - 1
    if width + 4 > term_width - 1:
        width = max(20, term_width - 5)
    return width


def prompt_header_text(n):
    """Framed header line for prompt turn n (box width matches cards)."""
    label = f"prompt #{n}"
    width = _prompt_box_width()
    dashes = width - len(label) - 2
    if dashes < 2:
        dashes = 2
    return f"+-- {label} " + "-" * dashes + "+"


def print_prompt_header(n, use_color=None):
    """Print the divider header for prompt turn n (numbered from 1 per session).

    Plain `--- prompt #N ---` when color is off (NO_COLOR/non-tty, grep-able);
    framed box + hint line otherwise. Returns the header line.
    """
    if use_color is None:
        use_color = _color_enabled()
    if not use_color:
        header = f"--- prompt #{n} ---"
        print(header)
        return header
    header = prompt_header_text(n)
    print(_paint(_BOLD + _CYAN, header, True))
    print("Type below. Results appear in the next box.")
    return header


def print_closing_rule(use_color=None):
    """Print a thin rule after results so the next prompt header never touches boxes."""
    width = _prompt_box_width()
    rule = "-" * (width + 4)
    print(rule)
    return rule


def parse_command(text):
    """Parse one interactive input line.

    Returns (action, arg) where action is one of:
    'empty' | 'quit' | 'help' | 'clear' | 'roots' | 'top' | 'top_set' | 'copy' | 'search'.
    """
    t = text.strip()
    if not t:
        return ("empty", None)
    low = t.lower()
    if low in ("exit", "quit"):
        return ("quit", None)
    if low in ("help", "?"):
        return ("help", None)
    if low in ("clear", "cls"):
        return ("clear", None)
    if low == "roots":
        return ("roots", None)
    if low == "top":
        return ("top", None)
    if low.startswith("top "):
        rest = t[3:].strip()
        try:
            n = int(rest)
            return ("top_set", n)
        except ValueError:
            return ("top", None)
    if t.isdigit():
        return ("copy", int(t))
    return ("search", t)


def handle_command(action, arg, state):
    """Execute a non-search command. Returns True if the loop should continue.

    `state` is a dict with keys: top_k, last_results, last_prompt.
    Factored out so tests can drive help/clear/top without a tty.
    """
    if action == "help":
        print(HELP_TEXT)
    elif action == "clear":
        os.system("cls" if os.name == "nt" else "clear")
    elif action == "top":
        print(f"top: showing {state.get('top_k', 3)} result(s). Use `top N` to change.")
    elif action == "top_set":
        n = arg
        if isinstance(n, int) and 1 <= n <= 20:
            state["top_k"] = n
            print(f"top: now showing {n} result(s).")
        else:
            print(f"Invalid number: {arg}. Use `top N` with 1-20.")
    elif action == "roots":
        print_roots(state.get("roots"))
    return True


def print_roots(roots=None):
    """Print discovered roots inline with SKILL.md counts."""
    try:
        roots = roots if roots is not None else scan.discover_roots()
    except Exception as e:
        print(f"roots lookup failed: {e}")
        return
    if not roots:
        print("no roots discovered.")
        return
    for path, source in roots:
        if source == "builtin":
            try:
                from skilllens.builtin_skills import BUILTINS as _B
            except ImportError:
                try:
                    from builtin_skills import BUILTINS as _B
                except ImportError:
                    _B = []
            n = len(_B)
        else:
            try:
                n = sum(1 for _dp, _dn, fn in os.walk(path) if "SKILL.md" in fn)
            except OSError:
                n = 0
        print(f"{path} [{source}] ({n} skills)")
    print(f"total roots: {len(roots)}")


def copy_to_clipboard(text):
    # why: clip.exe is built into Windows, keeps stdlib-only clipboard support
    try:
        subprocess.run(["clip"], input=text.encode("utf-8"), check=True)
        return True
    except Exception:
        return False


def main(top_k=3, roots=None):
    # why: pick up new skills added since the last scan without manual rebuild
    try:
        if roots is not None:
            scan.ensure_fresh_index(roots=roots)
        else:
            scan.ensure_fresh_index()
    except Exception as e:
        print(f"index refresh skipped: {e}")
    skills = search.load_index()
    if not skills:
        print("No skills indexed. Run: python -m skilllens.cli --rebuild-index")
        return 1
    last_results = []
    last_prompt = ""
    state = {"top_k": top_k, "last_results": last_results, "last_prompt": last_prompt, "roots": roots}
    print(BANNER)
    turn = 1
    while True:
        print_prompt_header(turn)
        turn += 1
        try:
            raw = input(">> ").strip()
        except (KeyboardInterrupt, EOFError):
            # why: Ctrl-C / Ctrl-Z should leave without traceback on Windows
            print("\nBye.")
            break
        action, arg = parse_command(raw)
        if action == "empty":
            continue
        if action == "quit":
            print("Bye.")
            break
        if action in ("help", "clear", "roots", "top", "top_set"):
            if action == "top_set":
                handle_command(action, arg, state)
                top_k = state["top_k"]
            elif action == "top":
                handle_command(action, arg, state)
            else:
                handle_command(action, arg, state)
            # keep state refs fresh
            state["last_results"] = last_results
            state["last_prompt"] = last_prompt
            continue
        # why: number shortcut acts on previous results without re-searching
        if action == "copy":
            n = arg
            if last_results and 1 <= n <= len(last_results):
                sk = last_results[n - 1]["skill"]
                line = f"@{sk['name']} {last_prompt}"
                if copy_to_clipboard(line):
                    print(f"copied: {line}")
                else:
                    print(f">>> use: {line} <<<")
            elif last_results:
                print(f"Pick 1-{len(last_results)}.")
            else:
                # no results yet: treat bare number as a search prompt
                last_prompt = raw
                last_results = search.suggest(raw, skills, top_k=top_k)
                state["last_results"] = last_results
                state["last_prompt"] = last_prompt
                if not last_results:
                    print("No matches.")
                    continue
                render(last_results, raw)
                print_closing_rule()
            continue
        # search
        prompt = arg
        last_prompt = prompt
        state["last_prompt"] = prompt
        last_results = search.suggest(prompt, skills, top_k=top_k)
        state["last_results"] = last_results
        if not last_results:
            print("No matches.")
            continue
        render(last_results, prompt)
        print_closing_rule()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
