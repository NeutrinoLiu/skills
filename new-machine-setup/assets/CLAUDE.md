# Global instructions

## Working principles

Adapted from Andrej Karpathy's four rules for LLM coding agents.

1. **Think before coding.** State assumptions, surface tradeoffs, push back when
   warranted. If something is ambiguous, name the ambiguity instead of silently
   picking a branch.
2. **Simplicity first.** The minimum code that solves the problem. Nothing
   speculative — no abstraction for a second caller that does not exist yet.
3. **Surgical changes.** Touch only what you must. Clean up only your own mess;
   unrelated refactors are a separate request.
4. **Goal-driven execution.** Define the success criterion up front, then loop
   until it is actually verified — not until the code merely looks right.

## Temporary files

Write every scratch file, intermediate artifact, debug script, and one-off log to
`./_claude_tmp/` at the root of the project being worked on. Create it if it does
not exist.

- Never scatter temp files across the repo, `/tmp`, or the home directory.
- Add `_claude_tmp/` to the project's `.gitignore` if it is a git repo and the
  entry is missing.
- Files there are disposable — never put anything in `_claude_tmp/` that the
  project needs in order to build or run.
