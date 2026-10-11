"""Smoke tests: index loads, 'how' and 'architect' rank top for known prompts."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skilllens import search


def test_index_loads():
    skills = search.load_index()
    assert isinstance(skills, list) and len(skills) >= 50, f"expected >=50, got {len(skills)}"


def test_how_ranks_top():
    top = [s["skill"]["name"] for s in search.suggest("how does X work", top_k=3)]
    assert "how" in top, f"'how' not in top 3: {top}"


def test_architect_ranks_top():
    top = [s["skill"]["name"] for s in search.suggest("design this", top_k=3)]
    assert "architect" in top, f"'architect' not in top 3: {top}"


if __name__ == "__main__":
    test_index_loads()
    print("PASS test_index_loads")
    test_how_ranks_top()
    print("PASS test_how_ranks_top")
    test_architect_ranks_top()
    print("PASS test_architect_ranks_top")
    print("all tests passed")
