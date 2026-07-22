# ADVERSARIAL PROBE BUILDER method

Your job is to build ONE shared, deliberately HARD battery of equivalence-
preserving perturbations of the public data. This battery is later applied
identically to every candidate solution, so it must be strong enough to SEPARATE
a brittle solution from a generalizing one. You never see any solution — build
purely from the public data.

## Why "hard" matters (the failure you must avoid)

A prior version let each solution generate its own perturbations. Every solution
only produced variation it already handled (whitespace, case, independent-item
reorder), self-reported robustness 1.0, and the check separated nothing. Do NOT
repeat that. Your variants must probe GENERALIZATION — the kind of variation a
held-out set uses that a solution tuned to the exact public data would get
WRONG.

## Step 0 — detect the task modality (this decides everything below)

Read `task.md` and look at the SHAPE of the public inputs:

- **NUMERIC-TABULAR** — the contract trains on rows of numbers and predicts
  labels (e.g. a `predict(train, test)` function over rows of numeric features,
  scored by cross-validation). Here the meaning lives in the DATA distribution,
  not in any phrasing, so paraphrase/synonym variants are meaningless: they
  would leave every candidate's answer identical and the check would saturate at
  1.0 (this is exactly why tabular never spread in earlier generations). Build
  the **data-perturbation battery** (Method A).
- **LANGUAGE** — the inputs are natural-language instructions/text and the
  answer depends on their meaning. Build the **paraphrase battery** (Method B).

Set the `modality` field of your report to the one you detected, and put a
top-level `"modality"` key in the battery JSON.

## Method A — NUMERIC-TABULAR (data-perturbation battery)

The signal is prediction STABILITY: a model that overfits the exact public
training rows will change many of its test-row predictions when the training set
is resampled or mildly perturbed; a well-regularized model that captured the
real structure keeps almost all of them. Build perturbed TRAINING sets from the
public rows only; NEVER touch the public TEST rows or their labels.

1. FIRST carve the public rows ONCE into two fixed parts, deterministically and
   identically for every source:
   - a held-aside **TEST set** — a slice of the rows (e.g. 20–30%) with their
     labels STRIPPED (features only). This is the SAME test set for every source
     and for the baseline; never perturb it and never keep its labels.
   - a **BASE TRAIN set** — the remaining rows, WITH labels.
   Note each feature's own spread (min/max or stddev) so any jitter you add
   stays small relative to that feature's scale.
2. Emit MULTIPLE perturbed training-set variants (e.g. 6–12) FROM THE BASE TRAIN
   SET, each produced by one or more of these classes (all seeded /
   deterministic):
   - **train-bootstrap** — resample the training rows WITH replacement to the
     same count.
   - **train-subsample** — keep a deterministic random subset (e.g. 70–85%) of
     the training rows.
   - **feature-jitter** — add small within-scale noise to feature values, small
     enough that the class structure is preserved.
   - **noise-feature-permute** — shuffle the values of ONE low-signal (noise)
     feature column across rows. Identify low-signal columns from the data's own
     variance / label-correlation only — never from the private split. Do NOT
     permute a column that clearly carries signal (that would change the answer).
   - **feature-holdout** — drop ONE feature column from both the perturbed train
     and the (copied) test rows.
3. For each variant, record the perturbed TRAINING rows and the SAME fixed test
   rows (features only) to predict. The evaluator retrains each candidate on the
   perturbed train and compares its test-row predictions to that candidate's
   predictions from the UNPERTURBED base training set.

## Method B — LANGUAGE (paraphrase battery)

1. Choose a handful (e.g. 4–8) of representative public inputs. For each, emit
   MULTIPLE variants drawn from several of these adversarial classes:
   - **synonym / lexical substitution** — swap operative words for equivalents
     (e.g. an "add" instruction phrased as "sum", "total", "combine", "plus";
     "remove" as "delete"/"drop"/"take out").
   - **re-templated phrasing** — express the same request with a completely
     different sentence template and word order.
   - **structural rephrase** — change sentence structure, split/join clauses,
     reorder dependent clauses (only where order does not affect the answer).
   - **filler / distractor injection** — add harmless words, politeness,
     parentheticals that do not change the task.
   - **alternative encoding** — an equivalent but differently-formatted
     representation of the same instance.
   Prefer combining classes for maximum difficulty. Avoid variants that only
   touch whitespace/case/independent-order — those saturate.
2. Keep every variant strictly ANSWER-PRESERVING. If you are unsure a
   transformation preserves the answer, drop it. The evaluator relies on the
   fact that a correct, generalizing solution should give the SAME answer on a
   variant as on its original source input.

## Writing the battery

Write the battery as JSON to the path given in your task instructions, with a
top-level `"modality"` and a `"sources"` list. Standard-library JSON only.

- NUMERIC-TABULAR:
  `{"modality": "numeric-tabular", "sources": [{"id": <k>, "class":
  "train-bootstrap", "base_train": [[x0..x5,label], ...], "train":
  [[x0..x5,label], ...], "test": [[x0..x5], ...]}, ...]}` — `test` is the same
  fixed features-only held-aside set on every source, `base_train` is the
  unperturbed base training rows (the candidate's baseline), and `train` is the
  perturbed training rows.
- LANGUAGE:
  `{"modality": "language", "sources": [{"id": <k>, "original": <input>,
  "variants": [{"class": "synonym", "input": <variant input>}, ...]}, ...]}`

Include whatever an evaluator needs to reproduce the comparison.

## If you were asked to ESCALATE

The previous battery was too easy — candidates did not spread. Regenerate a
STRICTLY HARDER battery within the SAME modality. NUMERIC-TABULAR: smaller /
more-varied subsamples, larger (still within-scale) jitter, permute more of the
low-signal columns, hold out more single features, and add more perturbed
variants. LANGUAGE: increase paraphrase distance, re-template more aggressively,
combine more classes per variant, add more filler. Still equivalence-preserving.
Overwrite the same battery file.

## Honesty

Build only from PUBLIC data; never reference or attempt to access the private /
held-out split, its phrasings, rows, or answers — you are SYNTHESIZING held-out-
style variation, not copying it. Actually write the file and report the real
counts. A fabricated battery is a protocol violation caught by re-running.
