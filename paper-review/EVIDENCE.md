# Evidence discipline

Rules for what a criticism may claim, derived from auditing referee reports that overreached. Every one of these was a real correction to a real review.

## Keep three registers separate

Say which of these each claim is, in the sentence itself:

- **The paper states** — transcribed from this submission.
- **For context** — from another paper, under that paper's protocol.
- **Reviewer-computed** — your arithmetic, with the inputs shown.

Blurring them is how a review acquires claims it cannot defend.

## Absent uncertainty is absent uncertainty

No seeds, no confidence interval and no significance test means the paper does not establish that its effect reproduces. It does not mean the effect is proven to be noise. Write the first.

Seed spreads published for other models, tasks or backends do not bound the paired variance of the delta in front of you. They are context for what this literature treats as noise, and they belong in the review as context.

## Cross-paper numbers are context, not comparison

When backbone, split, protocol or sensor input differ, another paper's number cannot be set against this one as a head-to-head result. Report it as context and say what differs. A method that consumes an extra modality is not beaten by a number from one that does not.

## Ask about provenance, never assert it

You can see that a table matches another paper's table and that a row is missing. You cannot see anyone remove it. Write *omitted*, not *deleted*; *unstated provenance*, not *fabricated*. Put the accusation to the authors as a question and let the rebuttal answer it.

The same holds for reconstructing what the authors did. An inference about subsampling, tuning or reuse is a request for the missing accounting, not proof of it.

## Match the test to the design

Paired results get a paired test. Leading with an unpaired Fisher on data that is paired or clustered within units invites the correction that the test was wrong, and the correction costs you the finding.

Where a comparison cannot reach significance under any arrangement of the observed counts, say that: it is stronger than a p-value and it is not a claim about this run's luck. Label a power calculation that assumes independence as the approximation it is.

## Respect what a theorem actually guarantees

A guaranteed event is the one in the statement. A secondary metric falling below the nominal level is not a coverage violation, because it was never the guaranteed quantity. Say that the guaranteed event is weaker or more easily satisfied than the one a reader assumes, and show what satisfies it trivially.

Credit the part of a construction that works even while you attack the evaluation.

## Word choice that survives audit

| Overreach | Defensible |
|---|---|
| indistinguishable from noise | does not establish that the gain reproduces |
| rows were deleted | omitted from an otherwise reproduced block |
| unattributed re-runs | numbers of unstated provenance |
| this is majority-class collapse | consistent with majority-class collapse |
| the gap is caused by the capture protocol | the protocol does not isolate modality from acquisition |
| the control does literally nothing | shows no gain at the reported precision |
| mandatory baseline | standard and important baseline |
| unverifiable | insufficiently self-contained |
| structurally identical to X | closely analogous to X |

## Round from the source

Recompute shares and percentages from the paper's final values, not from a draft. State the basis of the calculation. A share presented as exact and rounded from stale inputs is a gift to the authors.
