"""Grill-prompt regression: builtin grill skills must surface via synonyms."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skilllens import search

GRILL_PROMPT = (
    "i want the agent to ask me the question based on the codebase "
    "and architecture of the project unless i understand the project completly"
)


def _keys(top):
    return [(s["skill"].get("key") or s["skill"]["name"]) for s in top]


def test_grill_prompt_ranks_grill_top3():
    top = _keys(search.suggest(GRILL_PROMPT, top_k=3))
    assert "grill-me" in top or "grilling" in top, f"no grill skill in top 3: {top}"


def test_grill_prompt_ranks_grill_me_first():
    top = search.suggest(GRILL_PROMPT, top_k=3)
    keys = _keys(top)
    assert keys[0] == "grill-me", f"grill-me not first: {keys}"
    assert "[grill-intent boost]" in top[0]["reason"], f"missing boost reason: {top[0]['reason']}"


def test_plain_explain_does_not_boost_grill():
    top = search.suggest("explain how auth works", top_k=3)
    keys = _keys(top)
    assert keys[0] != "grill-me" and keys[0] != "grilling", f"false grill boost: {keys}"
    assert "[grill-intent boost]" not in top[0]["reason"]


def test_debug_prompt_ranks_diagnose_top3():
    top = _keys(search.suggest("debug this failing test", top_k=3))
    assert set(top) & {"diagnose", "diagnosing-bugs", "tdd"}, f"no diagnose skill in top 3: {top}"


def test_index_has_builtin_grill_me():
    skills = search.load_index()
    rec = next((s for s in skills if (s.get("key") or s.get("name")) == "grill-me"), None)
    assert rec is not None, "index missing 'grill-me'"
    assert rec.get("source") == "builtin", f"grill-me wrong source: {rec.get('source')}"


if __name__ == "__main__":
    test_grill_prompt_ranks_grill_top3()
    print("PASS test_grill_prompt_ranks_grill_top3")
    test_grill_prompt_ranks_grill_me_first()
    print("PASS test_grill_prompt_ranks_grill_me_first")
    test_plain_explain_does_not_boost_grill()
    print("PASS test_plain_explain_does_not_boost_grill")
    test_debug_prompt_ranks_diagnose_top3()
    print("PASS test_debug_prompt_ranks_diagnose_top3")
    test_index_has_builtin_grill_me()
    print("PASS test_index_has_builtin_grill_me")
    print("all tests passed")
