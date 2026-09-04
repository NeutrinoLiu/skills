---
name: paper-review
description: Review a research paper as a rigorous conference referee — ground it in related work, verify every load-bearing number against the rendered pages, and deliver a rating with a concise report. Use when asked to review, referee, or critique a paper or PDF submission, when asked whether a paper's evaluation supports its claims, or when writing a rebuttal-facing critique.
---

# Paper review

One paper, one working directory, one context. With several papers, dispatch one subagent per paper and run them one at a time; hand each the prompt in `REVIEWER-PROMPT.md`.

A **load-bearing** claim is one that moves the rating. Those are the claims you verify yourself and the only ones that belong in the report.

## Setup

```bash
mkdir -p <dir>/related_works <dir>/pages
cp <paper>.pdf <dir>/paper.pdf
pdftotext -layout <paper>.pdf <dir>/paper.txt
pdftoppm -png -r 110 <paper>.pdf <dir>/pages/page
```

Read `paper.txt` for prose and `pages/page-N.png` for everything else. `pdftotext` interleaves two-column layouts and scrambles tables, so a number read only from the text may belong to a different row, a different column, or a different table. Read every table off the page image.

## Ground it in related work

Fill `related_works/` with one short markdown file per prior work and baseline: what it does, its reported numbers on the benchmarks in play, its URL, and how it relates to or challenges this submission. Ten to sixteen files. Where a fact resists verification, write that it resisted verification. Never invent a number or a citation.

Aim this at the paper's own claims of novelty and superiority. The comparison the paper omits is usually the one that decides the review.

## Find the fundamental weakness

Work the paper in the order a referee actually thinks: the problem it targets, the observation motivating it, the method as implemented, then whether the evaluation can support what is claimed. Ask of the evaluation whether this protocol *could* establish this claim even in principle, before asking whether the numbers are good.

**Internal contradictions outrank everything else you will find.** They need no external source, survive rebuttal, and cannot be argued away. Hunt them first:

- An ablation row that beats the full model.
- The same configuration reported twice with different numbers.
- A configuration adopted against the paper's own stated selection criterion.
- Per-class or per-subset counts that sum to the total, bounding what the method can ever touch.
- One metric identical across architectures that share nothing, which is what a collapsed or degenerate predictor looks like.
- An anomaly present in exactly the rows copied from another paper and absent from the authors' own.
- A method whose protocol or split the paper adopts, absent from the paper's comparison table.
- The paper conceding that a trivial policy reaches its headline number.

Then size the effect against the paper's own variance: the spread its ablations produce, gaps between its own reported values for one model, protocol-choice ranges. An effect smaller than the paper's internal spread is the finding.

Read `EVIDENCE.md` before writing a word of the report. It is the discipline that separates a criticism that survives an audit from one that does not.

## Write the review

`review.md`, these headings verbatim:

```
# Title
# Summary
# Strengths
# Weakness
# Justification of Recommendation
# Specific Points of Feedback for Rebuttal
```

700 to 900 words. `# Weakness` opens with one bold sentence naming the single fundamental weakness, develops it over two to four short paragraphs on concrete evidence, and closes with one paragraph opening `Also worth noting:` that carries the rest compactly. A numbered list of eight weaknesses buries the finding that matters.

Strengths are real strengths, stated plainly, including the ones that complicate your rating. Justification names which findings drove the number and what would have raised it, and raises nothing new. Rebuttal questions are five to seven, each answerable on paper without new experiments.

Close with `**Rating: N.** <label>` and `**Confidence: N/5**`:

`10` seminal · `9` strong accept · `8` clear accept · `7` accept · `6` marginally above threshold · `5` marginally below · `4` ok but not good enough, reject · `3` clear rejection · `2` strong rejection · `1` trivial or wrong

Calibrate honestly. A sound paper gets a sound number; harshness is not rigour.

Run the `humanizer` skill over the finished file if it is installed.

## Verify before you hand it over

Re-derive every load-bearing number from `pages/*.png` yourself, including any produced by a subagent. State separately, in the report, what the paper says, what other papers say, and what you computed.

When a check comes back empty, confirm the check was right before concluding the claim is wrong. An acronym absent from the text may still be cited by author and title; a number missing from `paper.txt` may sit in a table the extraction dropped. A failed grep is evidence about your grep.

## Explainer page

When the deliverable includes a page explaining the paper, read `EXPLAINER.md`.
