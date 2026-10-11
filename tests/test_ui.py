"""Card rendering tests: width caps, full description, use line."""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skilllens import interactive


def _fake(prompt_len=200):
    return (
        {
            "skill": {
                "name": "demo-skill",
                "description": "Does demo things for testing card rendering",
                "path": "/some/long/path/to/SKILL.md",
                "source": "builtin",
            },
            "score": 1.23,
            "reason": "matched 1 desc token(s): demo",
        },
        "x" * prompt_len,
    )


def test_long_prompt_no_line_over_80():
    s, prompt = _fake(200)
    card = interactive.format_card(1, s, prompt, use_color=False)
    lines = card.splitlines()
    assert lines, "card is empty"
    assert max(len(l) for l in lines) <= 80, [len(l) for l in lines]


def test_narrow_terminal_caps_width(monkeypatch):
    monkeypatch.setattr(shutil, "get_terminal_size", lambda fallback=None: os.terminal_size((60, 24)))
    s, prompt = _fake(200)
    card = interactive.format_card(1, s, prompt, use_color=False)
    lines = card.splitlines()
    assert max(len(l) for l in lines) <= 59


def test_card_contains_description():
    s, prompt = _fake(20)
    card = interactive.format_card(1, s, prompt, use_color=False)
    for word in ("Does", "demo", "things"):
        assert word in card


def test_use_line_contains_at_name():
    s, prompt = _fake(20)
    card = interactive.format_card(1, s, prompt, use_color=False)
    assert "@demo-skill" in card


def test_prompt_header_plain_mode_grepable():
    # NO_COLOR/non-tty path: plain text header with the turn number
    header = interactive.print_prompt_header(7, use_color=False)
    assert header == "--- prompt #7 ---"


def test_prompt_header_framed_contains_number():
    header = interactive.print_prompt_header(3, use_color=True)
    assert "#3" in header
    assert header.startswith("+") and header.endswith("+")
    assert len(header) <= interactive._term_width() - 1


def test_prompt_header_narrow_terminal(monkeypatch):
    monkeypatch.setattr(shutil, "get_terminal_size", lambda fallback=None: os.terminal_size((60, 24)))
    header = interactive.prompt_header_text(12)
    assert "#12" in header
    assert len(header) <= 59
    rule = interactive.print_closing_rule()
    assert set(rule) == {"-"}
    assert len(rule) <= 59


def test_closing_rule_is_thin_dashes():
    rule = interactive.print_closing_rule()
    assert set(rule) == {"-"}
    assert len(rule) <= interactive._term_width() - 1


if __name__ == "__main__":
    test_long_prompt_no_line_over_80()
    print("PASS test_long_prompt_no_line_over_80")
    test_card_contains_description()
    print("PASS test_card_contains_description")
    test_use_line_contains_at_name()
    print("PASS test_use_line_contains_at_name")
    test_prompt_header_plain_mode_grepable()
    print("PASS test_prompt_header_plain_mode_grepable")
    test_prompt_header_framed_contains_number()
    print("PASS test_prompt_header_framed_contains_number")
    test_closing_rule_is_thin_dashes()
    print("PASS test_closing_rule_is_thin_dashes")
    print("all tests passed")
