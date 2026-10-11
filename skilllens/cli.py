"""Suggest-only CLI: rank local skills for a prompt, never auto-invoke."""
import argparse
import os
import sys

from skilllens import scan
from skilllens import search

try:
    from skilllens.builtin_skills import BUILTINS
except ImportError:  # pragma: no cover
    BUILTINS = []

try:
    from skilllens.brand import NAME, TAGLINE
except ImportError:  # pragma: no cover
    try:
        from brand import NAME, TAGLINE
    except ImportError:
        NAME = "SkillLens"
        TAGLINE = "Prompt in, ranked skills out"


def _count_skills(root):
    n = 0
    for _dirpath, _dirnames, filenames in os.walk(root):
        if "SKILL.md" in filenames:
            n += 1
    return n


def _color_enabled():
    if os.environ.get("NO_COLOR") is not None:
        return False
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="SkillLens",
        description=f"{NAME} - {TAGLINE} Suggest skills for a prompt (suggest-only).",
    )
    ap.add_argument("--prompt", default=None, help="User prompt to match skills against.")
    ap.add_argument("--rebuild-index", action="store_true", help="Re-run the scan first.")
    ap.add_argument("--roots", action="append", default=[], metavar="DIR",
                    help="Extra skill root to include (repeatable, source 'custom').")
    ap.add_argument("--list-roots", action="store_true",
                    help="Print discovered roots and SKILL.md counts, then exit.")
    ap.add_argument("--top", type=int, default=3, help="How many suggestions to show.")
    ap.add_argument("--interactive", action="store_true", help="Enter interactive terminal loop.")
    args = ap.parse_args(argv)

    extra = [(r, "custom") for r in args.roots]
    roots = scan.discover_roots() + extra

    if args.list_roots:
        for path, source in roots:
            if source == "builtin":
                n = len(BUILTINS)  # why: virtual root has no SKILL.md files to count
            else:
                n = _count_skills(path) if os.path.isdir(path) else 0
            print(f"{path} [{source}] ({n} skills)")
        print(f"total roots: {len(roots)}")
        return 0

    if args.rebuild_index:
        scan.main(roots=roots)
    elif args.interactive or args.prompt:
        # why: new skills in opencode/global config must surface without manual rescan
        scan.ensure_fresh_index(roots=roots)

    if args.interactive:
        from skilllens import interactive
        return interactive.main(top_k=args.top, roots=roots)

    if not args.prompt:
        ap.error("--prompt is required (or use --rebuild-index alone to refresh index).")

    skills = search.load_index()
    suggestions = search.suggest(args.prompt, skills, top_k=args.top)
    if not suggestions:
        print("No skills indexed. Run: python -m skilllens.cli --rebuild-index")
        return 1
    from skilllens import interactive
    use_color = _color_enabled()
    if use_color:
        interactive.render(suggestions, args.prompt, use_color=True)
    else:
        interactive.render(suggestions, args.prompt, use_color=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
