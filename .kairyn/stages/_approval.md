# Approval

A stage that ends with "Then follow `_approval.md`" waits for the user here. It names its next `stage`.

- Until the user approves in chat: keep `Approval: pending`, set `status: blocked`, ask for approval. Never approve for the user.
- Other replies are not approval. A reply that does not approve and that the stage does not name changes nothing.
- When the user approves: replace the line with `Approval: <git config user.name>, <timestamp>, "<the user's words>"`. Set the next `stage` and `status: in-progress`.
- Then end your message with the exact command for the user to type: `/kairyn:<next stage> <task folder>`. Never run it yourself: a skill you start runs on your model, not on its own.
