# CLAUDE.md

@AGENTS.md

## Claude Code specifics

Everything above applies unchanged. These notes cover only Claude Code.

- Run a roadmap step with `/roadmap-step <phase> <step>`. It checks the
  step's Status and Settings before Stage 1.
- On Windows, the Bash tool runs Git Bash and the PowerShell tool runs Windows
  PowerShell 5.1. Use one shell's syntax per call.
- Put personal, machine-specific instructions in `CLAUDE.local.md`, which is
  git-ignored. Never commit it, `.claude/settings.local.json` or session
  memory.
- Merges, branch-protection changes, secret writes and tag pushes may need the
  maintainer's approval in auto mode. Ask for them together, once, at the start
  of the step.
- If `gh pr edit` fails for lack of the `read:org` scope, update the pull
  request body through REST:
  `gh api -X PATCH repos/pyeconomics-dev/pyeconomics/pulls/<n> -F body=@<file>`.
