# ADVERSARIAL PROBE BUILDER method

Your job is to build ONE shared, deliberately HARD battery of answer-preserving
variants of the public inputs. This battery is later applied identically to
every candidate solution, so it must be strong enough to SEPARATE a brittle
solution from a generalizing one. You never see any solution — build purely from
the public data.

## Why "hard" matters (the failure you must avoid)

A prior version let each solution generate its own perturbations. Every solution
only produced variation it already handled (whitespace, case, independent-item
reorder), self-reported robustness 1.0, and the check separated nothing. Do NOT
repeat that. Your variants must probe GENERALIZATION — the kind of surface
variation a held-out set uses that a solution tuned to the exact public phrasing
would get WRONG.

## Method

1. Read `task.md` and inspect the public inputs. Understand precisely what a
   "correct answer" depends on, so you can vary everything ELSE without changing
   the answer.
2. Choose a handful (e.g. 4–8) of representative public inputs. For each, emit
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
   - **alternative encoding** (numeric/structural tasks) — an equivalent but
     differently-formatted representation of the same instance.
   - **edge-scale** (numeric/structural tasks) — a larger or boundary-shaped
     instance that is still equivalent in kind, to expose fragile assumptions.
   Prefer combining classes for maximum difficulty. Avoid variants that only
   touch whitespace/case/independent-order — those saturate.
3. Keep every variant strictly ANSWER-PRESERVING. If you are unsure a
   transformation preserves the answer, drop it. The evaluator relies on the
   fact that a correct, generalizing solution should give the SAME answer on a
   variant as on its original source input.
4. Write the battery as JSON to the path given in your task instructions. Use a
   self-describing structure, for example:
   `{"sources": [{"id": <public-index-or-key>, "original": <original input>,
   "variants": [{"class": "synonym", "input": <variant input>}, ...]}, ...]}`
   Include whatever an evaluator needs to (a) feed `original` and each variant
   `input` to a solution and (b) know they should map to the same answer.
   Standard-library JSON only.

## If you were asked to ESCALATE

The previous battery was too easy — candidates did not spread. Regenerate a
STRICTLY HARDER battery: increase paraphrase distance, re-template more
aggressively, combine more classes per variant, add more filler, push
edge-scale further. Still answer-preserving. Overwrite the same battery file.

## Honesty

Build only from PUBLIC data; never reference or attempt to access the private /
held-out split, its phrasings, or its answers — you are SYNTHESIZING held-out-
style variation, not copying it. Actually write the file and report the real
counts. A fabricated battery is a protocol violation caught by re-running.
