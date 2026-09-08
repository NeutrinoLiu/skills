# skills

Claude Code skills, one directory per skill.

## Install

Clone the whole collection as your personal skills directory:

```bash
git clone https://github.com/NeutrinoLiu/skills.git ~/.claude/skills
```

Already have a `~/.claude/skills`? Clone elsewhere and symlink the ones you want:

```bash
git clone https://github.com/NeutrinoLiu/skills.git ~/src/claude-skills
ln -s ~/src/claude-skills/<skill-name> ~/.claude/skills/<skill-name>
```

Claude picks them up on the next session. Invoke by name (`/<skill-name>`) or
just describe the task — each skill's `description` says when it applies.

## Skills

| Skill | What it does |
| --- | --- |
| [`new-machine-setup`](new-machine-setup/) | Provisions a fresh Linux box: oh-my-zsh, global `CLAUDE.md`, tmux/htop, Miniconda, `HF_HOME`, Hugging Face + GitHub logins, NVIDIA driver. Writes the Claude-side config directly and generates numbered shell scripts for you to run for everything needing sudo, a tty, or a reboot. |
| [`paper-review`](paper-review/) | Referees a research paper: fills a `related_works/` dir, verifies every rating-relevant number against rendered page images rather than the scrambled text dump, hunts internal contradictions first, and writes a 700–900 word report with a rating and confidence. Carries an evidence-discipline reference derived from an audit of its own earlier reviews. |
| [`bangya-poster`](bangya-poster/) | Builds a conference poster as one HTML sheet at 1 CSS px = 1 mm: styleboard and ranked layout candidates to choose from, a hand-maintained `PLACEHOLDERS.md` canvas, figures rendered by script from the paper's data, `feedback_N.md` rounds verified by render and overflow probe, then a Chrome → Ghostscript export to a CMYK, bled, crop-marked, font-outlined print PDF. Distilled from the ECCV 2026 ByteLOOM poster. |
| [`bangya-video`](bangya-video/) | Builds a five-minute paper presentation video from an HTML deck: cuts planned in markdown, a `deck.html` checkpoint with hold time and script per cut for the user to approve, assets rendered by script (Chrome frames, Blender turntables, dataset condition streams), `edge-tts` narration measured to set the timings, ffmpeg assembly with a reserved one-line caption strip. Distilled from the ECCV 2026 ByteLOOM video. |

## Layout

```
<skill-name>/
  SKILL.md      required — frontmatter (name, description) + the procedure
  ...           whatever else the skill needs (assets, templates, scripts)
```

`SKILL.md`'s `description` is what Claude matches against to decide whether a
skill applies, so it should name the triggering situation, not just the topic.
