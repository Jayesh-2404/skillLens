"""Built-in opencode skills: no SKILL.md on disk, so scan.py indexes these directly.

Source "builtin", path "opencode:<name>". Stdlib only.
"""

BUILTINS = [
    {
        "name": "caveman",
        "description": "Ultra-compressed communication mode. Cuts token usage by dropping filler while keeping technical accuracy. Use when user says caveman mode or be brief.",
    },
    {
        "name": "code-review",
        "description": "Review changes since a commit or branch for standards compliance and spec match. Use when user wants a branch or PR reviewed.",
    },
    {
        "name": "diagnose",
        "description": "Disciplined diagnosis loop for hard bugs and performance regressions. Reproduce, minimise, hypothesise, instrument, fix, regression-test. Use when user reports something broken or slow.",
    },
    {
        "name": "diagnosing-bugs",
        "description": "Diagnosis loop for hard bugs and performance regressions. Use when user says debug this or reports something failing.",
    },
    {
        "name": "domain-modeling",
        "description": "Build and sharpen a project's domain model. Use when discussing codebase terminology, glossaries, or ADRs.",
    },
    {
        "name": "find-skills",
        "description": "Discover and install agent skills. Use when user asks how to do X or looks for installable skills.",
    },
    {
        "name": "git-guardrails-claude-code",
        "description": "Set up hooks blocking dangerous git commands. Use when user wants git safety hooks.",
    },
    {
        "name": "grill-me",
        "description": "Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan or says grill me.",
    },
    {
        "name": "grilling",
        "description": "Grill the user relentlessly about a plan, decision, or idea. Use when user wants to stress-test thinking or uses any grill trigger phrase.",
    },
    {
        "name": "migrate-to-shoehorn",
        "description": "Migrate test files from as assertions to total-typescript shoehorn. Use for shoehorn or replacing as in tests.",
    },
    {
        "name": "opencode",
        "description": "Questions about OpenCode itself, config, providers, models, plugins, CLI, TUI, SDK. Use for any OpenCode usage question.",
    },
    {
        "name": "playwright-cli",
        "description": "Automate browser interactions and work with Playwright tests. Use for browser automation or web testing.",
    },
    {
        "name": "poteto-help",
        "description": "Answer questions about pstack-mode, picking the right skill or playbook for a task. Type at-poteto-help with a question. Does not start the work itself.",
    },
    {
        "name": "pr",
        "description": "Writing a PR body. Use when user wants a PR description written.",
    },
    {
        "name": "prototype",
        "description": "Build a throwaway prototype to answer a design question. Use to sanity-check a state model or explore UI shape.",
    },
    {
        "name": "report",
        "description": "Report an opencode issue or bug. Collect diagnostics and publish the issue with GitHub CLI.",
    },
    {
        "name": "research",
        "description": "Investigate a question against high-trust primary sources and capture findings as Markdown. Use when user wants a topic researched.",
    },
    {
        "name": "setup-pre-commit",
        "description": "Set up Husky pre-commit hooks with lint-staged, type checking, tests. Use when user wants pre-commit hooks.",
    },
    {
        "name": "tdd",
        "description": "Test-driven development. Build features or fix bugs test-first, red-green-refactor. Use when user wants tests first.",
    },
    {
        "name": "to-issues",
        "description": "Break a plan, spec, or PRD into independently-grabbable tracker issues. Use to convert a plan into issues.",
    },
    {
        "name": "to-prd",
        "description": "Turn conversation context into a PRD and publish it to the tracker. Use to create a PRD from context.",
    },
    {
        "name": "wizard",
        "description": "Generate an interactive bash wizard walking a human through steps only they can perform. Use for provisioning, credentials, dashboards, migrations.",
    },
    {
        "name": "write-a-skill",
        "description": "Create new agent skills with proper structure. Use when user wants to create a new skill.",
    },
    {
        "name": "writing-for-agents",
        "description": "Writing documents for agents. Use when creating skills or editing AGENTS.md or CLAUDE.md.",
    },
]
