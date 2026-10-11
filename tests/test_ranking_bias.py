"""Ranking-bias regression tests: routers must not dominate generic prompts."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skilllens import search


def norm(name):
    return re.sub(r"[\s_]+", "-", (name or "").strip().lower())


def key_of(skill):
    return skill.get("key") or norm(skill.get("name"))


ROUTERS = {"poteto-help", "poteto-mode"}


def test_perf_query_excludes_routers():
    top = [key_of(s["skill"]) for s in search.suggest("speed up slow database query", top_k=3)]
    assert not (set(top) & ROUTERS), f"router in top 3: {top}"


def test_index_has_no_duplicate_keys():
    skills = search.load_index()
    keys = [key_of(s) for s in skills]
    dupes = sorted({k for k in keys if keys.count(k) > 1})
    assert not dupes, f"duplicate keys: {dupes}"


def test_help_intent_surfaces_router():
    top = [key_of(s["skill"]) for s in search.suggest("which skill should I use for this task", top_k=3)]
    assert "poteto-help" in top, f"'poteto-help' not in top 3: {top}"


if __name__ == "__main__":
    test_perf_query_excludes_routers()
    print("PASS test_perf_query_excludes_routers")
    test_index_has_no_duplicate_keys()
    print("PASS test_index_has_no_duplicate_keys")
    test_help_intent_surfaces_router()
    print("PASS test_help_intent_surfaces_router")
    print("all tests passed")
