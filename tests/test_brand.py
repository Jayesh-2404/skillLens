"""Brand tests: SkillLens name, interactive commands, cli --help."""
import io
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skilllens import brand
from skilllens import interactive


def test_brand_name():
    assert brand.NAME == "SkillLens", f"expected SkillLens, got {brand.NAME!r}"
    assert getattr(brand, "TAGLINE", ""), "TAGLINE missing/empty"


def test_interactive_command_parsing():
    assert callable(getattr(interactive, "render", None)), "interactive.render missing"
    parser = getattr(interactive, "parse_command", None) or getattr(
        interactive, "handle_command", None)
    assert callable(parser), "no command parser (parse_command/handle_command) found"
    # help / clear / top handling via parse_command
    parse = getattr(interactive, "parse_command", None)
    if parse is not None:
        assert parse("help")[0] == "help", f"help not parsed: {parse('help')}"
        assert parse("clear")[0] == "clear", f"clear not parsed: {parse('clear')}"
        act, arg = parse("top 5")
        assert act == "top_set" and arg == 5, f"top 5 not parsed: {(act, arg)}"
    # handle_command drives top state
    if getattr(interactive, "handle_command", None) is not None:
        state = {"top_k": 3}
        interactive.handle_command("top_set", 5, state)
        assert state["top_k"] == 5, f"top not applied: {state}"


def test_cli_help_mentions_skilllens():
    out = subprocess.run(
        [sys.executable, "cli.py", "--help"],
        capture_output=True, text=True, timeout=30,
    )
    combined = (out.stdout or "") + (out.stderr or "")
    assert "SkillLens" in combined, f"--help missing SkillLens:\n{combined}"


if __name__ == "__main__":
    test_brand_name()
    print("PASS test_brand_name")
    test_interactive_command_parsing()
    print("PASS test_interactive_command_parsing")
    test_cli_help_mentions_skilllens()
    print("PASS test_cli_help_mentions_skilllens")
    print("all tests passed")
