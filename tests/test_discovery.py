"""Discovery tests: roots, recursive scan, and override precedence."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skilllens import scan


def _write_skill(dirpath, name, desc):
    os.makedirs(dirpath, exist_ok=True)
    with open(os.path.join(dirpath, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(f"---\nname: {name}\ndescription: {desc}\n---\n\nBody for {name}.\n")


def test_discover_roots_returns_existing():
    roots = scan.discover_roots()
    existing = [(p, s) for p, s in roots if os.path.isdir(p)]
    assert len(existing) >= 2, f"expected >=2 existing roots, got {existing}"


def test_recursive_scan_finds_nested():
    with tempfile.TemporaryDirectory() as tmp:
        _write_skill(os.path.join(tmp, "root", "shallow"), "shallow-skill", "shallow desc here")
        _write_skill(os.path.join(tmp, "root", "nested", "deep", "deep-skill"), "deep-skill", "deep nested desc here")
        recs = scan.scan_roots([(os.path.join(tmp, "root"), "custom")])
        keys = {r["key"] for r in recs}
        assert "shallow-skill" in keys, f"missing shallow: {keys}"
        assert "deep-skill" in keys, f"missing nested: {keys}"
        for r in recs:
            assert os.path.isabs(r["path"]), f"path not absolute: {r['path']}"


def test_dedupe_prefers_local_and_project_over_pstack():
    with tempfile.TemporaryDirectory() as tmp:
        pstack = os.path.join(tmp, "pstack")
        local = os.path.join(tmp, "local")
        project = os.path.join(tmp, "project")
        _write_skill(os.path.join(pstack, "dup"), "dup", "pstack upstream versionAAA")
        _write_skill(os.path.join(local, "dup"), "dup", "local override versionBBB")
        recs = scan.scan_roots([(pstack, "pstack"), (local, "local")])
        assert len(recs) == 1, f"expected 1 after dedupe, got {len(recs)}"
        assert recs[0]["source"] == "local", f"local should win: {recs[0]}"
        assert "versionBBB" in recs[0]["description"], f"wrong winner: {recs[0]}"
        _write_skill(os.path.join(project, "dup"), "dup", "project override versionCCC")
        recs2 = scan.scan_roots([(pstack, "pstack"), (project, "project")])
        assert len(recs2) == 1 and recs2[0]["source"] == "project", f"project should win: {recs2}"


if __name__ == "__main__":
    test_discover_roots_returns_existing()
    print("PASS test_discover_roots_returns_existing")
    test_recursive_scan_finds_nested()
    print("PASS test_recursive_scan_finds_nested")
    test_dedupe_prefers_local_and_project_over_pstack()
    print("PASS test_dedupe_prefers_local_and_project_over_pstack")
    print("all tests passed")
