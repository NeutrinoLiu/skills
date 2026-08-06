---
name: new-machine-setup
description: Set up a freshly installed Linux machine to the user's baseline. Applies the user's global Claude memory directly, then generates numbered shell scripts for the user to run themselves — packages, oh-my-zsh, Miniconda, HF_HOME, Hugging Face + GitHub logins, and an NVIDIA driver installer. Use when the user says they are on a new machine, a fresh install, a new box/server/workstation, or asks to "set up this machine".
---

# New machine setup

## The division of labour

This skill does **not** run system setup. It splits the work in two:

| Lane | Who does it | What |
| --- | --- | --- |
| **Agent-side** | You, directly, now | Anything living under `~/.claude` — the global `CLAUDE.md`. No sudo, no reboot, nothing interactive. |
| **System-side** | The user, by running generated scripts | Packages, shells, Miniconda, drivers, logins. |

Everything system-side becomes a **numbered script the user runs in a real
terminal**. This is not a stylistic preference — it is the only thing that
works:

- `sudo` reads its password from a tty. A tool call has none (`tty` prints
  "not a tty"), so `sudo` hangs. And `sudo -v` cannot help: sudo's default
  `timestamp_type=tty` keys the cached credential to the authenticating
  terminal, which a tool call can never match. **Verified on stock Ubuntu — do
  not suggest it.**
- `hf auth login` and `gh auth login` are interactive prompts. Driving them from
  a tool call hangs, and any token pasted into the conversation is then in the
  transcript forever.
- The NVIDIA driver needs a reboot, which no agent can sit through.

Never accept a typed-out password to feed `sudo -S`. Decline and point at the
scripts.

## Step 1 — Agent-side: global CLAUDE.md

Do this yourself, right away.

Install `assets/CLAUDE.md` from this skill directory to **`~/.claude/CLAUDE.md`**
(`mkdir -p ~/.claude` first):

- Not present → copy it.
- Present → diff, and append only the missing sections. Never clobber a
  CLAUDE.md the user has edited.

It applies from their next session, not this one. Say so.

## Step 2 — Detect the environment

```bash
. /etc/os-release 2>/dev/null; echo "$PRETTY_NAME"
echo "shell=$SHELL  arch=$(uname -m)"
for c in apt-get zsh git curl wget tmux htop conda gh hf python3; do
  command -v "$c" >/dev/null 2>&1 && echo "  have $c" || echo "  need $c"
done
lspci 2>/dev/null | grep -i 'nvidia' || echo "  no nvidia gpu"
df -h --output=target,size,avail -x tmpfs -x devtmpfs | head
```

Two things drive what you generate:

- **GPU present?** Decides whether `4-nvidia.sh` is generated at all.
- **Disk layout?** Informs the two path questions — if `/home` is small and
  there is a big data mount, say so when you ask.

The templates target **Debian/Ubuntu**. On another distro, swap the package
manager in `1-packages.sh` (`dnf install -y` / `pacman -S --noconfirm`, and
`build-essential` → `@development-tools` / `base-devel`) and tell the user you
adapted it.

## Step 3 — Ask the three questions

Ask all of them in one batch. These are the only decisions; do not interview the
user about anything else.

1. **Miniconda prefix** — default `~/miniconda3`. Override for a bigger disk.
2. **`HF_HOME`** — default `~/.cache/huggingface`. This is the single root for
   hub downloads, datasets, *and* the auth token, so it is the only HF variable
   worth setting. Model weights get large; offer a data mount if one exists.
3. **Git identity** — name and email for commits. If they only give an email,
   leave `GIT_NAME` empty; `3-logins.sh` adopts the name from their GitHub
   account after login.

## Step 4 — Generate the scripts

Create `~/Desktop/init_setup/` and copy each file from `templates/`,
substituting the `@@PLACEHOLDER@@` tokens. Then `chmod +x` all of them.

| Script | sudo | Generate when |
| --- | --- | --- |
| `1-packages.sh` | yes | always |
| `2-shell-and-conda.sh` | only the `chsh` prompt | always |
| `3-logins.sh` | no | always |
| `4-nvidia.sh` | yes, **ends in a reboot** | **only if Step 2 found an NVIDIA GPU** |
| `_env-report.sh` | — | always — sourced by all of the above |

`_env-report.sh` is a sourced helper, not a step. It must be copied alongside the
others or every script fails at startup. It provides two functions:

- `env_block_write <rc> VAR=value ...` — rewrites the marked block in an rc file,
  deleting the old one first so re-runs never stack duplicates. A `PATH+=<dir>`
  argument prepends instead of assigning, guarded on membership so sourcing an
  rc file twice in one shell cannot stack duplicate entries either.
- `env_report` — **called at the end of every script**, so any run that touches
  the environment shows the consolidated result rather than making the user go
  read `.bashrc`. It prints each managed variable with its value, which rc files
  carry it, whether it is live in the current shell, and whether the path it
  names exists. It flags a `CONFLICT` when rc files disagree — that means a
  half-applied edit, and it must never be hidden behind a last-wins read.

Placeholders: `@@CONDA_PREFIX_DIR@@`, `@@HF_HOME_DIR@@`, `@@GIT_NAME@@`,
`@@GIT_EMAIL@@`, and `@@NEXT_STEP@@` in `3-logins.sh` — set that last one to
`./4-nvidia.sh    # driver install, then reboot` when a GPU was found, otherwise
`nothing — setup is complete`.

Verify every generated script before handing it over:

```bash
grep -rn '@@' ~/Desktop/init_setup/ && echo "UNSUBSTITUTED PLACEHOLDERS" || echo "all substituted"
for f in ~/Desktop/init_setup/*.sh; do bash -n "$f" || echo "SYNTAX ERROR: $f"; done
```

Both checks must pass. A script that fails halfway through leaves a
half-configured machine.

### Why this split into four

The numbering is the run order, and the boundaries are real:

1. **Packages first** — everything downstream needs `zsh`, `git`, `curl`.
2. **Shell and conda second** — oh-my-zsh *replaces* `~/.zshrc` (moving any
   existing one to `.zshrc.pre-oh-my-zsh`), so it must land before conda's init
   block, the `HF_HOME` export, and the `~/.local/bin` PATH entry, or those are
   silently orphaned. This is why they share one script, in that order.

   `~/.local/bin` is not incidental: it is where the Claude Code native
   installer puts `claude`. Ubuntu's stock `.bashrc` adds that directory, but
   the `.zshrc` oh-my-zsh writes has the equivalent line **commented out** — so
   `claude` works in bash and vanishes on the first `exec zsh`. The script
   therefore manages the PATH entry for both rc files; the membership guard
   makes it a no-op wherever it is already present. If no `claude` binary is
   found the script wires PATH anyway and prints the install one-liner rather
   than installing anything itself.
3. **Logins third** — needs `gh` and a `pip` from step 1–2, and needs a human.
4. **NVIDIA last** — it is the only reboot. Putting it at the end means the user
   reboots once, at the end, instead of in the middle.

## Step 5 — Hand off

Tell the user to run them in order, and that each script prints its own `NEXT:`
line so they never have to come back here to know what follows:

```bash
cd ~/Desktop/init_setup
./1-packages.sh          # sudo — base packages
./2-shell-and-conda.sh   # oh-my-zsh, miniconda, HF_HOME
exec zsh                 # load the new shell and environment
./3-logins.sh            # interactive: hugging face, github
./4-nvidia.sh            # sudo — driver, then: sudo reboot
```

Then report:

- **Done by you**: the `~/.claude/CLAUDE.md` write (and whether it was a fresh
  copy or a merge).
- **Generated**: each script, with the values baked into it — the conda prefix,
  `HF_HOME`, the git identity. Show the actual values; do not make the user open
  the files to find out what you decided.
- **Skipped**: `4-nvidia.sh` when there is no GPU. Say it explicitly rather than
  silently omitting it.

Every script is idempotent — re-running one is safe, and skipped work is
reported as `-- already ...`. Say that too, so a failure midway is not scary.
