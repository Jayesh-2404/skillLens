"""20-prompt accuracy eval for SkillLens search. Measurement only — do not tune scoring here."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skilllens import search

PROMPTS = [
    # (prompt, expected_key)
    ("How does the auth subsystem work? I need a walkthrough before I change the session handling.",
     "how"),
    ("Why is the retry logic shaped this way? I need the design rationale and tradeoffs behind picking exponential backoff.",
     "why"),
    ("My new test is failing on the checkout path — write the failing test first, then fix the bug so it passes.",
     "tdd"),
    ("I want to build this feature test-first with red-green-refactor: start with a failing unit test.",
     "tdd"),
    ("Please review my branch against our coding standards and check whether it matches the spec.",
     "code-review"),
    ("This refactor is nontrivial — I need rigorous repro-first verification with small diffs and parallel subagents.",
     "poteto-mode"),
    ("This SQL query got slow after the last deploy — help me measure the regression properly before I tune it.",
     "benchmark-checklist"),
    ("I need to design the module structure for the new billing service — sketch the types and signatures before we write code.",
     "architect"),
    ("Write the PR body describing what this change does for reviewers.",
     "pr"),
    ("Write README docs for this library following a proper docs structure and style guide.",
     "technical-writing"),
    ("Break this implementation plan into independently-grabbable tracker issues for the team.",
     "to-issues"),
    ("Turn everything we discussed in this conversation into a PRD and publish it to the tracker.",
     "to-prd"),
    ("Research the best rate-limiting approaches against primary sources and capture the findings as Markdown.",
     "research"),
    ("Automate a browser test that clicks through the signup flow and verifies it with Playwright.",
     "playwright-cli"),
    ("Set up Husky pre-commit hooks with lint-staged, type checking, and tests for this repo.",
     "setup-pre-commit"),
    ("Teach me how this subsystem works — explain it plainly in plain English so I really understand it.",
     "teach"),
    ("Grill my design relentlessly — stress-test my plan and interrogate each decision until we share understanding.",
     "grill-me"),
    ("How do I configure providers and models in OpenCode? Question about the CLI and plugin setup.",
     "opencode"),
    ("Rewrite this draft to cut the AI tells and de-slop the prose so it sounds human.",
     "unslop"),
    ("Strip the redundant comments from this diff and kill the noise without touching behavior.",
     "no-comments"),
]


def main():
    skills = search.load_index()
    valid_keys = {search.skill_key(s) for s in skills}
    for _prompt, expected in PROMPTS:
        if expected not in valid_keys:
            print(f"FATAL: expected key '{expected}' missing from index", file=sys.stderr)
            sys.exit(2)
    assert len(PROMPTS) == 20, f"expected 20 prompts, got {len(PROMPTS)}"

    top1_hits = 0
    top3_hits = 0
    print(f"{'n':>2}  {'expected':<18} {'top1':<18} {'top3?':<5} {'top1?':<5}")
    for i, (prompt, expected) in enumerate(PROMPTS, 1):
        res = search.suggest(prompt, skills=skills, top_k=3)
        top3 = [search.skill_key(r["skill"]) for r in res]
        top1 = top3[0] if top3 else "<none>"
        h1 = expected == top1
        h3 = expected in top3
        top1_hits += h1
        top3_hits += h3
        print(f"{i:>2}  {expected:<18} {top1:<18} {'Y' if h3 else 'N':<5} {'Y' if h1 else 'N':<5}")
    print(f"top1 accuracy {top1_hits}/20")
    print(f"top3 accuracy {top3_hits}/20")
    if top3_hits < 12:
        sys.exit(1)


if __name__ == "__main__":
    main()
