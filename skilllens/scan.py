"""Walk skill roots, parse SKILL.md frontmatter, write skills.json."""
import json
import os
import re
import sys

try:
    from skilllens.builtin_skills import BUILTINS
except ImportError:  # pragma: no cover - fallback when package path is missing
    from builtin_skills import BUILTINS

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DEFAULT_ROOTS = [
    (r"C:\Users\jayes\.config\opencode\pstack-upstream\pstack\skills", "pstack"),
    (r"C:\Users\jayes\.config\opencode\skills", "local"),
]
# why: spec typo says "skil-sources.json"; accept it plus both intended names
CONFIG_FILENAMES = ("skill-sources.json", "skillsources.json", "skil-sources.json")
PSTACK_ROOT = r"C:\Users\jayes\.config\opencode\pstack-upstream\pstack\skills"
# why: index lives at the repo root (next to cli.py) so it resolves from any cwd
OUTPUT = os.path.join(ROOT_DIR, "skills.json")

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
STOPWORDS = {
    "the", "a", "an", "and", "or", "for", "in", "on", "of", "to", "with",
    "this", "that", "these", "those", "it", "its", "is", "are", "be",
    "before", "then", "while", "use", "using", "into", "from",
    "your", "work", "does", "what", "when", "need", "want", "help",
    "question", "task", "code", "file",
    "my", "me", "i", "should", "which",
}

# why: later discovery stage wins on key collision (builtin loses to every file copy)
SOURCE_RANK = {"builtin": 0, "pstack": 1, "local": 2, "project": 3, "custom": 4}
BUILTIN_SOURCE = "builtin"
BUILTIN_PATH_PREFIX = "opencode:"


def normalize_key(name):
    """Canonical key: lowercase, whitespace/underscores -> hyphen (why: dedupe + scoring)."""
    return re.sub(r"[\s_]+", "-", (name or "").strip().lower())


def parse_frontmatter(text, fallback_name):
    """Extract name/description from YAML frontmatter; fall back gracefully."""
    m = FRONTMATTER_RE.match(text)
    name, desc, body = fallback_name, "", text
    if m:
        fm, body = m.group(1), text[m.end():]
        n = re.search(r"^name:\s*(.+?)\s*$", fm, re.MULTILINE)
        d = re.search(r'^description:\s*["\']?(.*?)["\']?\s*$', fm, re.MULTILINE)
        if n:
            name = n.group(1).strip().strip("\"'")
        if d:
            desc = d.group(1).strip()
    if not desc:  # missing frontmatter: first non-empty line
        for line in body.splitlines():
            line = line.strip().lstrip("# ").strip()
            if line:
                desc = line[:200]
                break
    return name, desc, body


def derive_triggers(description):
    """Keywords: distinctive lowercase words from description (why: cheap recall)."""
    words = re.findall(r"[a-z0-9-]+", description.lower())
    seen, out = set(), []
    for w in words:
        if len(w) > 3 and w not in STOPWORDS and w not in seen:
            seen.add(w)
            out.append(w)
    return out[:15]


def _expand(p):
    """Expand %VARS%, ~, and root-relative paths (why: Windows config portability)."""
    p = os.path.expandvars(os.path.expanduser(p))
    if not os.path.isabs(p):
        p = os.path.join(ROOT_DIR, p)
    return os.path.normpath(p)


def discover_roots(cwd=None):
    """Return [(path, source)]; later entries override earlier on key collision.

    First entry is always the virtual ("builtin", "builtin") root: built-in
    opencode skills have no SKILL.md on disk (see _builtin_records).
    """
    # 0. virtual builtin root (no directory; scan_roots expands it from BUILTINS)
    roots = [("builtin", "builtin")]
    seen = set()

    def add(path, source):
        ap = os.path.normcase(os.path.abspath(path))
        if ap in seen:
            return  # why: USERPROFILE path dupes the hardcoded local path
        if os.path.isdir(path):
            seen.add(ap)
            roots.append((os.path.abspath(path), source))
        else:
            print(f"skip missing root: {path}", file=sys.stderr)

    # 1. pstack upstream (keep for compat, skip if missing)
    add(_expand(PSTACK_ROOT), "pstack")
    # 2. global config (any that exist, source "local")
    userprofile = os.environ.get("USERPROFILE", "")
    appdata = os.environ.get("APPDATA", "")
    candidates = []
    if userprofile:
        candidates.append(os.path.join(userprofile, ".config", "opencode", "skills"))
    if appdata:
        candidates.append(os.path.join(appdata, "opencode", "skills"))
    candidates.append(r"C:\Users\jayes\.config\opencode\skills")
    for c in candidates:
        add(os.path.normpath(os.path.expandvars(os.path.expanduser(c))), "local")
    # 3. project: walk up from cwd (max 4 levels), source "project"
    base = os.path.abspath(cwd or os.getcwd())
    cur = base
    for _ in range(5):  # why: cwd + 4 parents bounds IO on deep trees
        for sub in (os.path.join(".opencode", "skills"), "skills"):
            cand = os.path.join(cur, sub)
            if os.path.isdir(cand):
                add(cand, "project")
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    # 4. config file at the repo root (or next to scan.py for compat):
    # list of {"path","source"} or plain strings
    for fname in CONFIG_FILENAMES:
        cfg = None
        for cand in (os.path.join(ROOT_DIR, fname), os.path.join(SCRIPT_DIR, fname)):
            if os.path.isfile(cand):
                cfg = cand
                break
        if cfg is None:
            continue
        try:
            with open(cfg, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"skip bad config {cfg}: {e}", file=sys.stderr)
            continue
        if isinstance(data, dict):  # why: tolerate {"roots": [...]} wrappers
            for k in ("roots", "sources", "paths", "skill-sources"):
                if isinstance(data.get(k), list):
                    data = data[k]
                    break
            else:
                print(f"skip bad config {cfg}: expected a list", file=sys.stderr)
                continue
        if not isinstance(data, list):
            print(f"skip bad config {cfg}: expected a list", file=sys.stderr)
            continue
        for entry in data:
            if isinstance(entry, str):
                p, src = entry, "custom"
            elif isinstance(entry, dict) and entry.get("path"):
                p, src = entry["path"], entry.get("source", "custom")
            else:
                print(f"skip bad entry in {cfg}: {entry!r}", file=sys.stderr)
                continue
            p = _expand(p)
            if os.path.isdir(p):
                add(p, src)
            else:
                print(f"skip missing config root: {p}", file=sys.stderr)
    # 5. env override SKILL_SEARCH_ROOTS (os.pathsep-separated, source "custom")
    env = os.environ.get("SKILL_SEARCH_ROOTS", "")
    if env:
        for part in env.split(os.pathsep):
            part = part.strip().strip('"').strip("'")
            if not part:
                continue
            p = _expand(part)
            if os.path.isdir(p):
                add(p, "custom")
            else:
                print(f"skip missing env root: {p}", file=sys.stderr)
    return roots


def _parse_skill_file(md, source):
    with open(md, encoding="utf-8", errors="replace") as f:
        text = f.read()
    fallback = os.path.basename(os.path.dirname(md))
    name, desc, body = parse_frontmatter(text, fallback)
    key = normalize_key(name)
    name = key  # why: "Poteto Mode"/"Make Bot UI" caps -> lowercase-hyphen like the rest
    summary = "\n".join(
        l for l in body.strip().splitlines()[:20]
    )[:1000]
    return {
        "id": key,
        "name": name,
        "key": key,
        "description": desc,
        "triggers": derive_triggers(desc),
        "summary": summary,
        "path": os.path.abspath(md),
        "source": source,
    }


def _builtin_records():
    """SkillRecords for built-in opencode skills (no SKILL.md on disk)."""
    recs = []
    for b in BUILTINS:
        key = normalize_key(b["name"])
        desc = b["description"]
        recs.append({
            "id": key,
            "name": key,  # why: lowercase-hyphen like the rest
            "key": key,
            "description": desc,
            "triggers": derive_triggers(desc),
            "summary": desc,
            "path": BUILTIN_PATH_PREFIX + key,
            "source": BUILTIN_SOURCE,
        })
    return recs


def _merge_record(rec, source, records, by_key, where=""):
    """Insert rec with rank dedupe; later/higher-rank source wins, ties keep first."""
    key = rec["key"]
    prev = by_key.get(key)
    if prev is None:
        by_key[key] = rec
        records.append(rec)
        return
    pr, nr = SOURCE_RANK.get(prev["source"], 0), SOURCE_RANK.get(source, 0)
    if nr > pr:
        # why: file copies override builtin/upstream docs on collision
        print(f"dedupe: replace {prev['source']} '{key}' with {source} from {where}", file=sys.stderr)
        records[records.index(prev)] = rec
        by_key[key] = rec
    else:
        print(f"dedupe: skip {source} '{key}' from {where} (kept {prev['source']})", file=sys.stderr)


def scan_roots(roots=None):
    """Walk each root recursively for SKILL.md at any depth; later/higher-rank wins."""
    if roots is None:
        roots = discover_roots()
    records = []
    by_key = {}
    for root, source in roots:
        if source == BUILTIN_SOURCE or root == BUILTIN_SOURCE:
            # why: virtual root, expanded from BUILTINS so grill/diagnose/etc. are indexed
            for rec in _builtin_records():
                _merge_record(rec, BUILTIN_SOURCE, records, by_key,
                              where=BUILTIN_PATH_PREFIX + rec["key"])
            continue
        if not os.path.isdir(root):
            print(f"skip missing root: {root}", file=sys.stderr)
            continue
        found = []
        for dirpath, _dirnames, filenames in os.walk(root):
            if "SKILL.md" in filenames:
                found.append(os.path.join(dirpath, "SKILL.md"))
        for md in sorted(found):
            rec = _parse_skill_file(md, source)
            _merge_record(rec, source, records, by_key, where=md)
    return records


def _iter_skill_files(roots):
    for root, source in roots:
        if source == BUILTIN_SOURCE or root == BUILTIN_SOURCE:
            continue  # why: virtual root has no mtime to compare
        if not os.path.isdir(root):
            continue
        for dirpath, _dirnames, filenames in os.walk(root):
            if "SKILL.md" in filenames:
                yield os.path.join(dirpath, "SKILL.md")


def index_is_fresh(index_path=OUTPUT, roots=None):
    """True if index exists and is newer than every SKILL.md under roots."""
    if not os.path.isfile(index_path):
        return False
    if roots is None:
        roots = discover_roots()
    try:
        idx_mtime = os.path.getmtime(index_path)
    except OSError:
        return False
    newest = 0.0
    found_any = False
    for md in _iter_skill_files(roots):
        try:
            m = os.path.getmtime(md)
        except OSError:
            continue
        found_any = True
        if m > newest:
            newest = m
    if not found_any:
        return True  # why: nothing to index means existing index is not stale
    return newest <= idx_mtime


def ensure_fresh_index(index_path=OUTPUT, roots=None):
    """Rescan + rewrite index if missing or stale; returns records or None."""
    if roots is None:
        roots = discover_roots()
    if index_is_fresh(index_path, roots):
        return None
    records = scan_roots(roots)
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    print(f"index refreshed: {len(records)} skills", file=sys.stderr)
    return records


def main(output=OUTPUT, roots=None):
    if roots is None:
        roots = discover_roots()
    records = scan_roots(roots)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    print(f"wrote {len(records)} skills -> {output}")
    return records


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else OUTPUT
    main(out)
