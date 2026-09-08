# Tone Mapping

## Description

The second version keeps the Retinex branch and adds local face adjustment, tone-shape control, and semantic candidates. Qwen3.8-27B is also introduced to improve semantic quality judgment and candidate selection.

This week mainly focused on validating whether the V2 candidate pool and automatic selector can provide reliable pseudo-GT for Tone Mapping training.

## Work This Week

### 1. Manual Validation

A subset of source scenes was manually reviewed instead of checking the full dataset.

The validation focuses on:

* whether V2 provides better candidates than V1;
* whether the automatically selected PGT matches human preference;
* whether failures come from **candidate generation** or **candidate selection**.

Main review dimensions include:

* face brightness;
* face tone structure;
* face/background balance;
* overall tone naturalness.

### 2. Current Findings

The V2 candidate pool provides better coverage than V1, especially after adding semantic region adjustment.

However, several problems remain:

* Some backlit and low-light scenes still lack a good candidate.
* Retinex candidates dominate the pool and may affect pool-based selection.
* Qwen is currently underused and mainly works as a rejection checker.
* Similar candidate scores may indicate low selection confidence, but do not necessarily mean poor image quality.
* Generative candidates may introduce changes beyond Tone Mapping and need source-preservation checking.

## Results

The current validation is mainly used to identify failure cases and confirm whether the V2 selection process agrees with human judgment.

Recommended evaluation:

| Item               | Evaluation                             |
| ------------------ | -------------------------------------- |
| Candidate quality  | V1 vs. V2                              |
| Selection accuracy | Automatic result vs. manual preference |
| Difficult scenes   | Backlight / low light                  |
| PGT reliability    | Human approval of selected PGT         |

Representative results should show:

**Source → V1 selected result → V2 selected result → Human-preferred result**

## Analysis

The current main limitation is no longer only the IQA score itself.

Two different problems need to be separated:

**Generation Gap**
No candidate provides a good enough result.

**Selection Error**
A good candidate exists, but the automatic selector does not choose it.

This distinction is important because the two problems require different improvements.

## One-Sentence Weekly Summary

Validated the V2 TM pseudo-GT pipeline with manual review and identified remaining gaps in candidate generation and automatic selection.

## Next Week’s Plan

1. **Improve candidate diversity.**
   Keep the effective Retinex branch while strengthening local face TM and tone-shape candidates for backlit and low-light scenes.

2. **Upgrade Qwen semantic judgment.**
   Extend Qwen3.8-27B from basic semantic checking to scene understanding, TM naturalness evaluation, TM-only validation, and Top-K pairwise ranking.

3. **Improve candidate selection logic.**
   Reduce Retinex-family bias in pool consistency and separate image quality from selection confidence.

4. **Add source-preservation checking.**
   Compare Source and Candidate to prevent non-TM changes such as face structure, texture, or background modification from entering the pseudo-GT set.

5. **Continue targeted manual validation.**
   Focus on difficult scenes and selection mismatches to confirm whether the updated method improves PGT reliability.
