"""SkillLens CLI shim: delegates to the skilllens package."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from skilllens.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
