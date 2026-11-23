# Learnings

Stages append here.

- grill: The knowledge base (`../knowledge-base/03 Playbooks/`, `01 Topics/`) holds the playbooks and notes behind each stage. Read the linked notes before you recommend an answer: they changed 4 of 20 answers in the build-stage grill.
- requirements: Task files have a 1500-token budget (`docs/tasks/*/*.md`). A grill with 20 decisions passes it; write each decision in one or two sentences.
- design: `checks.grounded_problems` reads a backticked branch name with a slash, such as `feat/x`, as a file path. Write branch names without backticks.
- build: `uv run pytest` fails when a new stage file or template is not in `plugin/release-hashes.json`. Run `uv run python scripts/release_hashes.py --write` after each change to a file init installs.
- build: `plugin/stages/DESIGN.md` is at its 500-token budget. A new step there needs a cut elsewhere in the file.
- build: A stub `claude` that picks its action from words in the prompt breaks when a prompt shares the word. The fix-round prompt said "reviewer findings" and the stub took it for a reviewer call.
