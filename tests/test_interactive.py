"""Interactive smoke tests: suggest count + module entrypoint."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skilllens import interactive
from skilllens import search


def test_suggest_returns_3():
    skills = search.load_index()
    out = search.suggest("how does login work", skills, top_k=3)
    assert len(out) == 3, f"expected 3, got {len(out)}"


def test_interactive_main_callable():
    assert callable(getattr(interactive, "main", None)), "interactive.main missing"


if __name__ == "__main__":
    test_suggest_returns_3()
    print("PASS test_suggest_returns_3")
    test_interactive_main_callable()
    print("PASS test_interactive_main_callable")
    print("all tests passed")
