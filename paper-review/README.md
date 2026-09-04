# paper-review

A Claude Code skill for refereeing a research paper: related-work grounding ·
page-image verification · a rating and a concise referee report · optionally an
explainer page.

Built from a run of five AAAI submissions whose reviews were then audited by a
second model. Most of what's here is the corrections that audit produced.

## How it works

One paper, one working directory, one context. With several papers you dispatch
one subagent each and run them one at a time; `REVIEWER-PROMPT.md` is the prompt
template, and it points the subagent back at this skill rather than restating it.

The parts that carry their weight:

**Read the pages, not the text dump.** `pdftotext -layout` interleaves two-column
layouts and scrambles tables. A number read only from the text may belong to a
different row, column, or table. The skill renders every page to PNG and treats
the image as the source of truth for anything tabular. This caught real errors —
transposed columns in a copied baseline block, and a table where the extraction
had spliced two columns together.

**Hunt internal contradictions first.** They need no external source and survive
rebuttal. An ablation row that beats the full model; the same configuration
reported twice with different numbers; one metric identical across architectures
that share nothing; per-class counts that sum to the total and so bound what the
method can ever touch. `SKILL.md` carries the full list. Across five papers these
were consistently the most defensible findings, and several were sitting in plain
sight inside tables the authors printed themselves.

**Say only what the evidence supports.** `EVIDENCE.md` is the audit's output: keep
what the paper states, what other papers state, and what you computed in separate
registers; absent uncertainty analysis means the paper hasn't established
reproducibility, not that the effect is noise; ask about provenance rather than
asserting it. It ends with a table of overreaching phrasings and their defensible
replacements.

**Verify the subagent.** Re-derive every rating-relevant number yourself. And when
a check comes back empty, confirm the check was right before concluding the claim
was wrong — an acronym absent from the text may still be cited by author and
title.

## Files

```
SKILL.md             the procedure, the report format, the rating scale
EVIDENCE.md          what a criticism may claim (read before writing)
REVIEWER-PROMPT.md   subagent prompt template, one paper per agent
EXPLAINER.md         the explainer page: series identity, build, render-and-look
```

## Output

`review.md` in six fixed headings, 700–900 words, with one fundamental weakness
leading the weakness section rather than a numbered list of eight, and a rating
plus confidence on the standard 1–10 conference scale. Alongside it: `notes.md`,
a filled `related_works/`, and cropped figures.

If [`humanizer`](https://github.com/blader/humanizer) is installed, the skill runs
it over the finished review.
