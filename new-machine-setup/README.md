# new-machine-setup

A Claude Code skill for provisioning a fresh Linux box: oh-my-zsh · global
`CLAUDE.md` · tmux/htop · Miniconda · `HF_HOME` · Hugging Face + GitHub logins ·
NVIDIA driver.

Assumes Claude Code is already installed — it's the first thing on the box, and
it's what runs this skill.

## How it works

The skill splits the work in two, because an agent genuinely cannot do half of it:

**Agent-side** — the skill writes `~/.claude/CLAUDE.md` itself. No sudo, no
reboot, nothing interactive.

**System-side** — the skill *generates* numbered scripts into `~/Desktop/init_setup/`
and you run them. It never runs them for you:

- `sudo` needs a tty to read a password; a tool call has none, so it hangs.
  (`sudo -v` doesn't help — sudo keys its credential cache to the authenticating
  terminal.)
- `hf auth login` and `gh auth login` are interactive, and a token pasted into a
  chat lives in the transcript forever.
- The NVIDIA driver ends in a reboot.

## Install

This skill lives in [NeutrinoLiu/skills](https://github.com/NeutrinoLiu/skills),
which is laid out one directory per skill — so the whole repo clones straight in
as your skills directory:

```bash
git clone https://github.com/NeutrinoLiu/skills.git ~/.claude/skills
```

If `~/.claude/skills` already exists, clone elsewhere and symlink just this one:

```bash
git clone https://github.com/NeutrinoLiu/skills.git ~/src/claude-skills
ln -s ~/src/claude-skills/new-machine-setup ~/.claude/skills/new-machine-setup
```

On a box so bare that `git` is missing — this is the chicken-and-egg case, since
`1-packages.sh` is what installs git:

```bash
mkdir -p ~/.claude/skills
curl -fsSL https://github.com/NeutrinoLiu/skills/archive/refs/heads/main.tar.gz \
  | tar xz --strip-components=1 -C ~/.claude/skills
```

## Run

Start Claude Code and say **"set up this new machine"**, or `/new-machine-setup`.

It asks three questions (Miniconda prefix, `HF_HOME`, git identity), writes your
global `CLAUDE.md`, and generates the scripts. Then:

```bash
cd ~/Desktop/init_setup
./1-packages.sh          # sudo — base packages
./2-shell-and-conda.sh   # oh-my-zsh, miniconda, HF_HOME
exec zsh                 # load the new shell and environment
./3-logins.sh            # interactive: hugging face, github
./4-nvidia.sh            # sudo — driver, then: sudo reboot
```

Each script prints its own `NEXT:` line, so the terminal tells you what follows.
All are idempotent — re-running one is safe, and already-done work is reported
as `-- already ...`.

`4-nvidia.sh` is generated **only if an NVIDIA GPU is detected**, and it
re-checks the hardware at run time anyway.

## Layout

```
SKILL.md                        the procedure Claude follows
assets/CLAUDE.md                installed to ~/.claude/CLAUDE.md
templates/1-packages.sh         \
templates/2-shell-and-conda.sh   |  copied to ~/Desktop/init_setup/ with
templates/3-logins.sh            |  @@PLACEHOLDER@@ values filled in
templates/4-nvidia.sh           /   (4-nvidia only when a GPU is present)
templates/_env-report.sh        sourced helper — must ship with the others
```

`_env-report.sh` is not a step. It owns writing the `# >>> new-machine-setup >>>`
block in your rc files, and the environment summary every script prints when it
finishes. If it is missing, the numbered scripts fail at startup.

Edit `assets/CLAUDE.md` to change the global instructions that land on every
machine. Edit the templates to change what the scripts do.
