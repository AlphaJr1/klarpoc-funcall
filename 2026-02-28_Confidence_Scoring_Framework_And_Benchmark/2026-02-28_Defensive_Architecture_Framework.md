# Klar Defensive Architecture Framework: 4-Layer System for 99.9% Accuracy

**Date:** 2026-02-28
**Updated:** 2026-03-01 (Lock 2 replaced with Temperature Scaling; Lock 4 Drift Detection added; Week 4 paraphrase testing added)
**Purpose:** Technical blueprint for 4-layer defense against miscalibration, data errors, reasoning failures, and data drift
**Audience:** Adrian (Engineering), Nicholas (QA), Stephen (PM)
**Status:** Ready for Week 4-6 Implementation (Lock 4 targets Week 7+)

---

## Executive Summary: The "Quad-Lock" System

To reach 99.9% accuracy and satisfy the "Julius Rule" (wrong answers are worse than no answer), Klar implements four independent verification layers:

| Layer | Name                                       | Owner                                 | Function                                                                                                                                                                                                    | Failure Mode Caught                                                |
| ----- | ------------------------------------------ | ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| **1** | 8-Factor Confidence Formula                | AI Agent                              | How confident am I?<br>**improved Shadow Check (factor 7) is the primary safety net for single-source anomalies**, with DNC Path 1 as the first attempt. Lock 3 plays no role here at all.                  | Miscalibration (raw score ≠ actual accuracy)                       |
| **2** | Post-Hoc Calibration (Temperature Scaling) | Adrian + Nicholas                     | Is that confidence number accurate?Transforms raw score to truthful probability                                                                                                                             | Systematic bias in raw scores (-20 to +40 pp)                      |
| **3** | Contradiction Matrix + Circuit Breaker     | Adrian (Technical) + Nicholas (Logic) | Is the underlying data even trustworthy enough to score? Hard-stop if cross-source delta >5% (e.g. POS vs. Shopee revenue). **Does NOT catch single-source anomalies — those fall to Lock 1 Shadow Check.** | Garbage-in-garbage-out (GIGO) errors from conflicting data sources |
| **4** | Drift Detection + Escalation Adjustment    | Adrian + Nicholas                     | Detects when the world changed; tightens threshold                                                                                                                                                          | Epistemic uncertainty (schema drift, fee changes, seasonal shifts) |

> **Lock 2 vs. original:** Isotonic regression replaced by temperature scaling. Reason: isotonic regression requires 1000+ labeled samples for reliable fit; temperature scaling works on 30 queries with a single scalar parameter. Same epistemic uncertainty blind spot — covered by Lock 4.

**Execution Flow:**
```
Query received
    ↓
[LOCK 3] Check Contradiction Matrix on raw data sources (5% delta threshold)
  ← Runs on data BEFORE draft is generated — avoids wasting AI call if data is bad
    ├─ YES (contradiction found) → ESCALATE to AM immediately (circuit breaker; skip Lock 4, draft, and Locks 1-2)
    └─ NO (data clean) → Continue
    ↓
[LOCK 4] Check Drift Detection (running in background, Week 7+)
    ├─ DRIFT DETECTED → Tighten threshold for this query type (+5-7 pp)
    └─ NO DRIFT → Use standard threshold
    ↓
AI generates DRAFT internally (reasoning trace + draft answer)
← NOT yet delivered to anyone
    ↓
[LOCK 1] Calculate 8-Factor Raw Score on DRAFT
    ├─ DNC: evaluates reasoning trace vs. draft answer
    ├─ Shadow Check: audits draft answer logic + disclosure
    └─ Historical Consistency: checks draft answer vs. past trends
    ↓
[LOCK 2] Apply Temperature Scaling (calibrates raw score)
    ↓
[THRESHOLD] Compare calibrated score to Empirical Threshold (88-94% standard; 93-99% if drift detected)
    ├─ ABOVE → Draft answer released directly to customer
    └─ BELOW → Draft answer routed to AM for review before release
```

**When Lock 3 fires (circuit breaker triggered), all downstream steps are skipped:**

| Step | Skipped? | Reason |
|------|----------|--------|
| Lock 4 (Drift Detection) | ✅ Skipped | No threshold to tighten — escalation is unconditional |
| Draft Generation | ✅ Skipped | Data is untrustworthy; generating a draft wastes the API call and risks producing a misleading answer |
| Lock 1 (8-Factor Score) | ✅ Skipped | No draft to score |
| Lock 2 (Temperature Scaling) | ✅ Skipped | No raw score to calibrate |
| Threshold Decision | ✅ Skipped | Irrelevant — circuit breaker overrides all scoring |

> Lock 3 is intentionally the **first** check so it can short-circuit everything downstream when data integrity fails.

---

## LOCK 1: 8-Factor Confidence Formula

### Factor Weighting (8 Factors)

| Factor | Weight | Measurement | Why Changed |
|--------|--------|-------------|------------|
| **Completeness** | 25% | % of required fields available | ↓ 30% → 25% (deprioritize difficulty, prioritize integrity) |
| **Tool Routing** | 20% | Did AI call the correct API (e.g., Loyverse POS vs. Shopee)? | — unchanged (critical) |
| **Complexity** | 15% | Query type (simple/medium/complex) — adjusts risk weighting | ↓ 20% → 15% (deprioritize difficulty, prioritize integrity) |
| **Freshness** | 15% | Age of data (same-day vs. stale or out-of-sync records) | — unchanged |
| **Data Validation** | 15% | Scans for data quality errors (nulls, impossible negatives) | — unchanged (critical) |
| **[NEW] Reasoning Trace DNC** | 10% | Does AI's chain-of-thought match its final output? | NEW: Catches "distracted AI" failures |
| **[NEW] Shadow Check** | Supporting | Secondary AI model audits the logic of the first. **Improved prompt asks two questions: (1) Does the answer logically follow from the reasoning? (2) Did the reasoning find any anomaly, warning, or problem that was NOT disclosed in the final answer?** A FLAG on either question forces escalation to AM regardless of score. | NEW: Catches reasoning errors + undisclosed single-source anomalies the primary model missed |
| **[NEW] Historical Consistency** | Supporting | Compares current answer against past trends to flag anomalies | NEW: Catches outlier answers that deviate from historical patterns |

**Weighted total: 100%** (Shadow Check + Historical Consistency are supporting signals — they flag for review but do not override the weighted score)

### Shadow Check: Measurement Protocol

**Two-question prompt (sent to Haiku as secondary AI judge):**

```
System: You are a logic and disclosure auditor for an AI answering marketing data queries.
Given a query, reasoning trace, and final answer, evaluate TWO things:

Question 1 — Logic Check:
Does the final answer logically follow from the reasoning trace?

Question 2 — Disclosure Check:
Did the reasoning trace contain any anomaly, warning, flag, or problem
(e.g. negative values, unusual spike, missing data, unexpected result)
that was NOT mentioned or disclosed in the final answer?

Respond in this exact format:
LOGIC: PASS or FLAG: [reason]
DISCLOSURE: PASS or FLAG: [reason]
RESULT: PASS (both pass) or FLAG (either fails)
```

**Example — Logic PASS, Disclosure FLAG (the dangerous case):**
```
Query: "Total sales yesterday?"
Reasoning: "Daily summary shows Rp 3.5M... but I see negative values in the ledger... maybe ignore those..."
Answer: "Rp 3.5M"

LOGIC: PASS — Rp 3.5M does follow from daily summary
DISCLOSURE: FLAG — Reasoning found negative values in ledger; not mentioned in answer
RESULT: FLAG → Force escalation to AM
```

**Example — both PASS:**
```
Query: "Top 3 products?"
Reasoning: "Nasi Padang 120 units, Es Cendol 95 units, Rendang 80 units. No anomalies."
Answer: "1. Nasi Padang, 2. Es Cendol, 3. Rendang"

LOGIC: PASS
DISCLOSURE: PASS — no anomalies found in reasoning
RESULT: PASS
```

**Why two questions matter:**
- Question 1 (logic) catches: wrong tool called, wrong date range, math error, contradictory conclusion
- Question 2 (disclosure) catches: AI noticed a problem, made a judgment call to ignore it, returned a clean-looking answer — the AM never knew there was anything to review

Lock 3 (Contradiction Matrix) does NOT catch single-source anomalies (e.g. negative ledger entries within POS data alone). Shadow Check's Disclosure Check is the primary safety net for these cases.

### DNC (Distractor-Normalized Coherence): Measurement Protocol

**Definition:** Reasoning Trace Consistency — does the AI's internal monologue (chain-of-thought) align with its draft answer?
**When:** DNC runs after the AI generates its internal draft answer — BEFORE anything is delivered to the user or AM. The draft answer is only released after Locks 1 and 2 have processed it and the threshold decision is made. (Lock 3 runs before draft generation on raw data; Lock 4 runs before draft generation to set the threshold — neither processes the draft itself.)

**What DNC Path 1 catches vs. Lock 3 (scope clarification):**

| Source of anomaly | Lock 3 catches? | DNC Path 1 catches? |
|---|---|---|
| POS revenue vs Shopee revenue delta >5% | ✅ Yes → already escalated, DNC never runs | N/A |
| Negative values within POS ledger (single-source) | ❌ No | ✅ Yes — AI notices in reasoning |
| POS vs Shopee delta = 4% (below threshold, Lock 3 passes) | ❌ No | ✅ Yes — AI notices "mismatch" in reasoning |
| Unusual spike within one data source | ❌ No | ✅ Yes — AI notices "anomaly" in reasoning |

DNC Path 1 is **not** re-checking Lock 3's job. It catches anomalies the AI discovered **during draft generation** that Lock 3 never ran against — single-source issues and below-threshold findings the AI noticed in its own reasoning.

**Measurement (0-100 scale):**

DNC uses a **hybrid approach** (DNC Hybrid Scoring): deterministic value matching for numeric queries (fast, no extra API cost), LLM-as-judge for complex/text queries, and binary check for escalations.

```python
import re

def calculate_dnc_score(reasoning_trace, final_answer, query, query_type):
    """
    Hybrid DNC calculation:
    - Numeric queries (revenue, units, members): value extraction + comparison
    - Complex/text queries (trends, rankings): LLM-as-judge
    - Escalation queries (contradiction flagged): binary coherence check
    Note: Do NOT return "Rp 0" for contradictions — a zero value looks like real revenue data.
    Always return a clear escalation message so the AM knows the answer was withheld.
    """

    # --- PATH 1: AI-discovered anomalies (single-source issues or below-threshold findings) ---
    # NOTE: This does NOT re-check Lock 3's cross-source delta (that already passed).
    # This catches anomalies the AI noticed during its OWN reasoning — things Lock 3 never saw:
    #   - Negative values within a single source (e.g. negative ledger entries within POS)
    #   - Below-threshold cross-source gaps the AI noticed (e.g. 4% delta — Lock 3 let it through)
    #   - Data quality issues within one API response (nulls, unusual spikes)
    # "exceeds threshold" removed — if that literally fired, Lock 3 would have caught it already.
    problem_flagged = any(w in reasoning_trace.lower()
                          for w in ["anomaly", "negative value", "mismatch", "unusual", "data quality"])
    problem_escalated = any(w in final_answer.lower()
                            for w in ["escalate", "note:", "warning", "anomaly", "data integrity"])

    if problem_flagged:
        # AI found a problem — did it act on it?
        if problem_escalated:
            return 95   # Correctly escalated: HIGH coherence
        else:
            return 20   # Hid the problem: VERY LOW coherence

    # --- PATH 2: Numeric queries (revenue, units, members, counts) ---
    if query_type in ["sales", "members", "retention", "units"]:
        # Extract all Rupiah/numeric values from reasoning and answer
        reasoning_numbers = set(
            int(n.replace(",", "").replace(".", ""))
            for n in re.findall(r"Rp\s?([\d,\.]+)", reasoning_trace)
        )
        answer_numbers = set(
            int(n.replace(",", "").replace(".", ""))
            for n in re.findall(r"Rp\s?([\d,\.]+)", final_answer)
        )

        if not answer_numbers:
            return 45   # Answer has no numbers but query expected them → incoherent

        # Score = % of answer values traceable to reasoning (within 1% tolerance)
        matched = sum(
            1 for a in answer_numbers
            if any(abs(a - r) / max(r, 1) < 0.01 for r in reasoning_numbers)
        )
        value_match_score = matched / len(answer_numbers)  # 0.0 to 1.0

        return int(value_match_score * 100)

    # --- PATH 3: Complex/text queries (trends, rankings, comparisons) ---
    # Use a small LLM as judge — only called for non-numeric queries
    prompt = f"""
Query: {query}
Reasoning: {reasoning_trace}
Answer: {final_answer}

Score 0-100: How well does the answer logically follow from the reasoning?
- 90-100: Answer directly reflects all key reasoning steps, no gaps
- 60-89: Minor gaps or unstated assumptions, answer still supported
- 30-59: Answer partially conflicts with or ignores reasoning steps
- 0-29: Answer directly contradicts reasoning or skips critical steps

Return only a number.
"""
    score = call_haiku(prompt)   # Fast, cheap model — not the primary AI
    return int(score)
```

**Real-World Examples (from Lixus queries):**

| Query                             | Reasoning Trace                                                                                                                | Final Answer                                                                                            | DNC Score                                                    | Explanation                                                             |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------- |
| "Revenue for Shopee store today?" | "POS shows Rp 5M... Shopee shows Rp 4.2M... I notice a discrepancy of Rp 800K (19% delta)... this exceeds the 5% threshold..." | "ESCALATE: Data integrity issue — POS vs. Shopee delta 19% (threshold 5%). No revenue figure returned." | **95%**                                                      | Reasoning identifies issue, final answer correctly escalates (not Rp 0) |
| "Total sales yesterday?"          | "Daily summary shows Rp 3.5M... but wait, I see negative values in the ledger... maybe ignore those..."                        | "Rp 3.5M"                                                                                               | **35%** (```BAD. AI found an anomaly and silently hid it```) | Reasoning finds anomaly, ignores it, doesn't mention in output          |
| "Top 3 products?"                 | "Highest: Nasi Padang (120 units)... second: Es Cendol (95 units)... third: Rendang (80 units)..."                             | "1. Nasi Padang, 2. Es Cendol, 3. Rendang"                                                              | **98%**                                                      | Reasoning and answer perfectly aligned                                  |

**DNC Success Criteria (Week 4):**
- Mean DNC score across 30 baseline queries: ≥75%
- Correlation between DNC and actual accuracy: r ≥ 0.60
- Queries with DNC <50% have accuracy <80% (validates negative correlation)

---

## LOCK 2: Post-Hoc Calibration (Temperature Scaling)

### Why Lock 2 Exists

**Raw 8-factor scores are miscalibrated.** Example:
- Raw score: 85% (AI confidence)
- Actual accuracy: 65% (what really happened)
- Miscalibration gap: -20 pp

Temperature scaling **fixes this** by dividing logits by a single learned scalar (T):
```
T > 1 → scores pushed toward 50% (overconfident model → more common for LLMs; expected T range: 1.5–3.0)
T < 1 → scores pushed toward both extremes (0% or 100%) (underconfident model → less common)
T = 1 → no change (already calibrated)
```
> Note: T does not change the ranking of answers — only the magnitude of confidence scores. An answer that scored highest before scaling still scores highest after. (Source: AWS Prescriptive Guidance — Temperature Scaling)

> **Why temperature scaling over isotonic regression:** Isotonic regression requires 1000+ labeled samples for a reliable fit; with only 30 Week 4 queries it will overfit badly. Temperature scaling optimizes a single scalar parameter and is statistically stable on 20-30 data points. Both methods have the same epistemic uncertainty blind spot — covered by Lock 4.

### Implementation (Week 5)

**Input:** Week 4 baseline data (30 queries)
```
Query ID | 8-Factor Raw Score | DNC | Actual Correct? |
1        | 92                 | 88  | Yes (1)         |
2        | 78                 | 65  | No (0)          |
3        | 85                 | 92  | Yes (1)         |
...
30       | 88                 | 72  | Yes (1)         |
```

**Process:**
```python
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import expit  # sigmoid

# Convert raw scores to logits
raw_scores = np.array([92, 78, 85, ..., 88]) / 100.0
actual_correctness = np.array([1, 0, 1, ..., 1])
logits = np.log(raw_scores / (1 - raw_scores + 1e-8))

# Find optimal temperature T that minimizes NLL
def nll(T):
    calibrated_probs = expit(logits / T)
    return -np.mean(
        actual_correctness * np.log(calibrated_probs + 1e-8) +
        (1 - actual_correctness) * np.log(1 - calibrated_probs + 1e-8)
    )

result = minimize_scalar(nll, bounds=(0.1, 10.0), method='bounded')
T_optimal = result.x  # Expected range: 1.1 - 2.5 for LLMs

# Apply to get calibrated scores
calibrated_scores = expit(logits / T_optimal)

# Measure improvement
ece_before = np.mean(np.abs(raw_scores - actual_correctness))
ece_after = np.mean(np.abs(calibrated_scores - actual_correctness))
print(f"Optimal T: {T_optimal:.2f}")
print(f"ECE Reduction: {ece_before - ece_after:.3f} pp")
# Expected: 0.15-0.23 pp reduction
```

**Success Criteria (Week 5):**
- ✅ ECE reduction: ≥0.10 pp (target: 0.15 pp; temperature scaling is conservative)
- ✅ No systematic bias: calibrated scores ±5% of actual accuracy
- ✅ T_optimal in valid range: 0.5–5.0 (outside this range = data problem)

### Validation Set (Week 5)

Do NOT test temperature scaling on the same 30 queries used to fit it (leakage). Instead:
- Use 20 queries for fitting (random subset)
- Use remaining 10 queries for validation
- Success: Validation ECE <0.12

### Monthly Refit (Production)

T_optimal drifts as the data distribution shifts. Refit monthly:
1. Collect 20+ new production queries with QA labels
2. Re-run optimization above → new T_optimal
3. Alert if T_optimal changes by >0.5 (indicates significant distribution shift → escalate to Lock 4 review)

---

## LOCK 3: Contradiction Matrix + Circuit Breaker

### Highest-Risk Pairs (Lixus-Specific)

**Financial Integrity Pairs (Priority 1):**
1. **POS (Loyverse) vs. Shopee Revenue**
   - What: Total daily sales reported by POS vs. Shopee order API
   - Why: Lixus pain point — multi-platform reconciliation
   - Delta threshold: **5%** (aggressive)
   - Escalation: Adrian (if API error) or Nicholas (if calculation error)

2. **Settlement Amount vs. Reported Profit**
   - What: What Shopee/Tokopedia actually paid vs. what the AM recorded
   - Why: Platform fees eat margins; critical for P&L
   - Delta threshold: **5%**
   - Escalation: Adrian (payment processing) or Nicholas (fee calculation)

**Awareness Metrics (Deferred to later sprint):**
- Instagram follower counts (not financial)
- Cross-platform pricing (awareness, not revenue)

### Circuit Breaker Logic

```python
def contradiction_matrix_check(query_results):
    """
    Compares high-risk data pairs.
    If delta > 5%, return CIRCUIT_BREAKER (escalate immediately).
    """

    # Extract values from query results
    pos_revenue = query_results["pos"]["daily_revenue"]  # Rp 5M
    shopee_revenue = query_results["shopee"]["order_total"]  # Rp 4.2M

    # Calculate delta percentage
    delta_pct = abs(pos_revenue - shopee_revenue) / pos_revenue * 100
    # Example: |5M - 4.2M| / 5M = 16%

    # Check threshold
    if delta_pct > 5.0:
        return {
            "circuit_breaker": True,
            "message": f"Data Integrity Issue: POS vs. Shopee delta {delta_pct:.1f}% (threshold 5%)",
            "escalation_priority": "HIGH",
            "escalate_to": "Adrian (technical) or Nicholas (logic)",
            "action": "ESCALATE to AM immediately; do not generate draft answer"
        }
    else:
        return {"circuit_breaker": False}
```

### Example Escalation Scenarios

**Scenario 1: Technical Contradiction (→ Adrian)**
```
Query: "What's our settlement from Shopee this week?"
POS data: Rp 10M (7 days × Rp 1.43M avg)
Shopee API: Cannot connect (timeout)
Contradiction: Data source unavailable
Escalation: Adrian (Engineer) — fix API connection
Message to AM: "Shopee API unreachable. Contact Adrian."
```

**Scenario 2: Logic Contradiction (→ Nicholas)**
```
Query: "What's our profit margin on Shopee this week?"
POS Revenue: Rp 10M
Shopee Settlement: Rp 7.5M
Delta: 25% (exceeds 5% threshold)
Contradiction: Platform fees + returns explain 25% but system didn't flag it
Escalation: Nicholas (QA) — refine fee calculation logic or DNC weighting
Message to AM: "Profit calc flagged: Large platform fee variance detected. Reviewing..."
```

**Scenario 3: No Contradiction (→ Proceed to Lock 1)**
```
Query: "What's today's revenue by store?"
POS Revenue Store A: Rp 2M
POS Revenue Store B: Rp 1.8M
Total: Rp 3.8M
Contradiction check: Single-source (POS only), no cross-source delta
Result: PASS — proceed to draft generation → 8-factor scoring → temperature scaling
```

---

## Escalation Routing: Dual Ownership

### Adrian (Engineer) — Technical Contradictions

**Owns:** API failures, data pipeline errors, sync timeouts
**Triggers:**
- Shopee API 404 / timeout
- JSON parsing error in settlement feed
- Timestamp mismatch (data from different hours)

**Action Items:**
- Debug API connection
- Check data freshness
- Verify schema compatibility

### Nicholas (QA) — Logic Contradictions

**Owns:** Calculation errors, reasoning failures, weight calibration
**Triggers:**
- POS vs. Shopee delta >5% (but both APIs working)
- DNC score low but confidence high
- Empirical threshold not matching actual accuracy

**Action Items:**
- Refine 8-factor weights (especially DNC)
- Investigate why AI missed the contradiction in reasoning
- Update calibration model if bias detected

---

## Week 4-6 Execution Timeline

### Week 4: Contradiction Matrix Baseline

**What the baseline log looks like (one row per query):**

| Query ID | Raw Score | DNC Score | Shadow Check | Actual Correct? | Contradiction? |
|----------|-----------|-----------|--------------|-----------------|----------------|
| 1 | 92 | 88 | PASS | Yes | No |
| 2 | 78 | 35 | PASS | No | No ← **gap: DNC low, Shadow Check missed it, answer wrong** |
| 3 | 85 | 95 | FLAG | Yes | Yes ← **Lock 3 fired, escalated before Lock 1 ran** |
| … | … | … | … | … | … |
| 30 | 88 | 72 | PASS | Yes | No |

**Reading the table — what each row tells Nicholas:**

- **Query 1** (high DNC, PASS, correct, no contradiction): Clean query. System worked as expected. No action needed.
- **Query 2** (low DNC, PASS, wrong, no contradiction): **This is the gap.** DNC caught the incoherence (score 35) but wasn't low enough to drag the total below threshold. Shadow Check passed because the primary AI's reasoning *sounded* logical — it found negative values in the ledger and decided to ignore them. The improved Shadow Check Disclosure Check would catch this: *"Did reasoning find a problem not disclosed in the answer?"* → FLAG. **Action: add "negative values" to Shadow Check disclosure keywords; consider raising DNC weight.**
- **Query 3** (high DNC, FLAG, correct, contradiction): Lock 3 fired and escalated before Lock 1 ran. The answer was actually correct, but correctness is irrelevant once the circuit breaker fires — the system correctly withheld the answer. The Shadow Check FLAG is from a separate run (post-hoc, for logging purposes only). No gap here — system worked correctly.
- **Query 30** (mid DNC, PASS, correct, no contradiction): Acceptable. DNC 72 is below the ≥75% mean target — Nicholas notes it but it's within normal range for complex queries.

**Key patterns Nicholas looks for:**
- Queries where `Actual Correct? = No` AND `Contradiction? = No` AND `Shadow Check = PASS` → these are the genuine gaps (system had no hard stop and still got it wrong)
- Correlation between DNC score and `Actual Correct?` → target r ≥ 0.60 (validates DNC as a useful signal)
- Any `Shadow Check = FLAG` where `Actual Correct? = Yes` → false positives (Shadow Check too aggressive, adjust prompt)

**Paraphrase testing rationale:** The Week 4 baseline of 30 queries is designed as 20 unique query types × 1–2 phrasings each. The purpose is to measure brittleness — if accuracy drops >5pp on a rephrased version of a question that the system handled correctly in its original form, routing logic needs fixing before Week 5 calibration. Paraphrase variants are test set only and do not train the locks; the locks are calibrated from data signals (raw scores, logits, delta rates), not query text.

| Task | Owner | Success Criteria |
|------|-------|-----------------|
| Run 30-query baseline | Nicholas | 30 queries complete, all data logged |
| **Include paraphrase variants in test set** | Nicholas | 20 unique question types × 1-2 phrasings each (e.g., "new members today?" AND "members who joined today?"). Tests brittleness — if accuracy drops on rephrased queries, routing logic needs work before Week 5 calibration. **Note:** Paraphrase variants are test set only — they measure system brittleness, not train the locks. The locks (1–4) are calibrated from Week 4 baseline data signals (raw scores, logits, delta rates), not from query text. |
| Log contradiction matrix values | Nicholas | For each query: POS rev, Shopee rev, delta %, settlement vs. profit |
| Analyze contradiction patterns | Stephen + Nicholas | Which queries had >5% delta? Did those have lower accuracy? |
| Measure DNC baseline | Adrian | Mean DNC ≥75%, correlation with accuracy r ≥0.60 |
| Flag brittleness gap | Nicholas | If accuracy on paraphrased variants is >5 pp lower than original phrasing → escalate to Adrian before Week 5 |

### Week 5: Locks 1-2 Implementation

| Task                                      | Owner            | Success Criteria                                       |
| ----------------------------------------- | ---------------- | ------------------------------------------------------ |
| Build 8-factor formula with DNC           | Adrian           | Code ready, DNC function tested on 30 baseline queries |
| Fit temperature scaling (T_optimal)       | Adrian + Stephen | ECE reduction ≥0.15 pp, validation ECE <0.12           |
| Implement circuit breaker (5% delta)      | Adrian           | Code ready, tested on 5 sample contradictions          |
| Validate Lock 1+2 on holdout (10 queries) | Nicholas         | Calibrated scores <0.12 away from actual accuracy      |
|                                           |                  |                                                        |

### Week 6: Lock 3 + Threshold Discovery

| Task | Owner | Success Criteria |
|------|-------|-----------------|
| Test circuit breaker on complex queries | Adrian + Nicholas | Contradictions correctly flagged, escalations to right owner |
| Empirical threshold discovery (on calibrated scores) | Stephen | Thresholds per query type: Sales ≥88%, Trend ≥94%, etc. |
| Validate full 3-layer system (20 holdout queries) | Nicholas | 99% accuracy on direct-send (above threshold), 0 false negatives |
| Document escalation SOP | Adrian + Nicholas | ClickUp template ready, ownership rules clear |

---

---

## LOCK 4: Drift Detection + Escalation Adjustment (Week 7+)

### Why Lock 4 Exists

**Locks 1-3 only catch aleatoric uncertainty** — miscalibration and hard data contradictions. They are blind to **epistemic uncertainty**: situations where the world has changed but the model doesn't know it.

Real examples for Lixus:

| Drift Type | Likelihood in 12 weeks | What Locks 1-3 Do | Risk |
|---|---|---|---|
| Shopee/Tokopedia platform fee changes | 🔴 High (30-50%) | Miss — confidence stays high, calculation wrong | Breaks 99% accuracy |
| POS API schema change (new field) | 🔴 High (40-60%) | Partially caught by Lock 1 (completeness drops) | Moderate |
| Seasonal surge (holiday week) | 🔴 Guaranteed (80%+) | Miss — query volume/patterns shift, calibration drifts | 2-5% accuracy drop |
| New store added to Lixus account | 🟡 Medium | Miss — agent omits new store from aggregates | Silent wrong answer |

Lock 4 converts these blind spots into **active monitoring** — detecting when distribution has shifted and tightening the escalation threshold accordingly.

### Implementation (Week 7)

**Monitor 3 weekly statistics against the Week 4 baseline:**

```python
def detect_drift(current_week_metrics, week4_baseline):
    """
    Compares current week's key statistics to the Week 4 baseline.
    If any signal drifts significantly, flags epistemic uncertainty.
    """
    drift_signals = []

    # Signal 1: Score distribution drift
    score_delta = abs(
        current_week_metrics["avg_raw_score"] - week4_baseline["avg_raw_score"]
    )
    if score_delta > 0.10:  # >10 pp shift in average score
        drift_signals.append(f"SCORE_DRIFT: {score_delta:.2f} pp shift from baseline")

    # Signal 2: Data completeness drift
    completeness_delta = abs(
        current_week_metrics["data_completeness"] - week4_baseline["data_completeness"]
    )
    if completeness_delta > 0.10:  # >10% fewer fields available
        drift_signals.append(f"COMPLETENESS_DRIFT: {completeness_delta:.2f} drop from baseline")

    # Signal 3: Contradiction rate drift
    contradiction_delta = abs(
        current_week_metrics["contradiction_rate"] - week4_baseline["contradiction_rate"]
    )
    if contradiction_delta > 0.10:  # >10 pp more contradictions than baseline
        drift_signals.append(f"CONTRADICTION_DRIFT: {contradiction_delta:.2f} pp above baseline")

    if drift_signals:
        return {
            "drift_detected": True,
            "signals": drift_signals,
            "action": "Tighten escalation threshold by +5-7 pp until retraining complete"
        }
    return {"drift_detected": False}
```

**Baseline values to record at Week 4:**
```
week4_baseline = {
    "avg_raw_score": 0.83,        # Record actual value from Week 4 run
    "data_completeness": 0.92,    # % of required fields present across 30 queries
    "contradiction_rate": 0.08,   # % of queries that triggered Lock 3
}
```

> **These values are placeholders.** Adrian replaces them with real values after Week 4 completes. Here is how each is computed:
>
> | Field | How it's computed | Example |
> |---|---|---|
> | `avg_raw_score` | Average of the 8-factor raw scores across all 30 baseline queries | Scores [92, 78, 85, 88, ...] → mean = 0.83 |
> | `data_completeness` | Average of Factor 1 (Completeness) scores across 30 queries — % of required API fields that were present and non-null per query | Query needed 10 fields, 9 available → 0.90; average across 30 queries → 0.92 |
> | `contradiction_rate` | Count of queries that triggered Lock 3 (cross-source delta >5%) ÷ 30 | 2-3 queries triggered Lock 3 out of 30 → 0.08 |
>
> Once recorded, these become the "normal" reference. Any future week where a signal shifts >10 pp from these values triggers a drift alert and tightens the escalation threshold by +5–7 pp.

### Response to Drift Detection

```
Drift detected
    ↓
Immediate: Tighten threshold by +5-7 pp
  (e.g., normal threshold 88% → drift threshold 95%)
    ↓
Within 1 week: Collect 20+ new labeled queries
    ↓
Refit temperature scaling (T_optimal) on new data
    ↓
If T_optimal changed >0.5: Investigate root cause
  → Fee change? New store? Schema update?
  → Update contradiction matrix pairs if needed
    ↓
Monitor for 2 weeks post-refit to confirm stability
```

### What Lock 4 Does NOT Cover

Lock 4 is passive monitoring — it detects drift after it has happened. It does **not** prevent wrong answers in the first query after a drift event. The escalation threshold tightening is a risk mitigation, not a guarantee. Full mitigation requires the monthly retraining cycle.

### Success Criteria (Week 7-12)

- Monitoring dashboard live with 3 metrics tracked weekly
- At least one drift event documented (expected — 12 weeks guarantees seasonal pattern shift)
- Response time: Drift detected → threshold adjusted within 24 hours
- Retraining time: Drift detected → temperature scaling refit within 1 week

---

## Production Monitoring (Week 7+)

### Metrics to Track

| Metric | Target | Frequency | Owner | Action If Missed |
|--------|--------|-----------|-------|-----------------|
| Contradiction detection rate | 5-15% of queries | Daily | Nicholas | If <5%, may have blind spots; if >15%, may be over-filtering |
| Circuit breaker false positive rate | <2% | Weekly | Nicholas | Adjust 5% delta threshold |
| ECE on new data | <0.12 | Weekly | Adrian | If increasing, refit temperature scaling (Lock 2) |
| DNC correlation with accuracy | r ≥0.60 | Weekly | Nicholas | If dropping, refine DNC weighting or DNC measurement |
| Direct-send accuracy | ≥99% | Daily | Nicholas | If <99%, lower threshold or investigate DNC/calibration |
| **[Lock 4] Avg raw score vs. baseline** | Within ±0.10 pp of Week 4 | Weekly | Adrian | If drifting, tighten threshold; schedule retraining |
| **[Lock 4] Data completeness vs. baseline** | Within ±0.10 of Week 4 | Weekly | Adrian | If dropping, check POS API schema for changes |
| **[Lock 4] Contradiction rate vs. baseline** | Within ±0.10 pp of Week 4 | Weekly | Nicholas | If spiking, check for platform fee or business rule changes |

### Monthly Recalibration

If production data diverges from Week 4 baseline (or Lock 4 drift detected):
1. Collect 20+ new labeled queries (QA-reviewed)
2. Refit temperature scaling T_optimal on new data
3. Re-validate thresholds
4. If T_optimal changed >0.5: investigate root cause (fee change, schema update, new store)
5. Update DNC measurement if needed
6. Reset Lock 4 baseline values to current week's statistics

---

## Appendix: DNC Real-World Examples from Lixus

### Example 1: Perfect DNC (Score 95%)

**Query:** "What's today's revenue?"
**Reasoning Trace:**
```
I'm looking at the daily_summary table for 2026-03-01.
Total revenue field shows: Rp 5.2M
This includes: Toko A (Rp 2.1M) + Toko B (Rp 2.0M) + Toko C (Rp 1.1M)
No negative values or anomalies detected.
Data freshness: Last updated 30 minutes ago ✓
All required fields present ✓
Ready to return answer.
```

**Final Answer:** "Today's revenue: Rp 5.2M (last updated 30 min ago)"

**DNC Score:** 95% (reasoning led directly to final answer, no distractions)

---

### Example 2: Poor DNC (Score 30%)

**Query:** "What's today's revenue?"
**Reasoning Trace:**
```
Looking at daily_summary for 2026-03-01.
Total revenue shows: Rp 5.2M
But wait... I notice the ledger has negative entries for returns: -Rp 300K
Should I subtract those? The daily_summary already shows Rp 5.2M...
Hmm, maybe ignore the negatives since they're in a different table?
Actually, let me just return what the daily_summary says.
```

**Final Answer:** "Today's revenue: Rp 5.2M"

**DNC Score:** 30% (reasoning identified anomaly, didn't mention in output, creating doubt about consistency)

**What Should Have Happened:**
- Good DNC answer: "Rp 5.2M (note: returns of Rp 300K recorded separately; net revenue Rp 4.9M)"
- Excellent DNC: Return either net (Rp 4.9M) OR gross (Rp 5.2M) based on query intent

---

## References

- **Temperature Scaling:** Guo et al. (2017) "On Calibration of Modern Neural Networks"; single-parameter method, reliable on small datasets (20-30 samples)
- **Isotonic Regression (rejected for PoC):** Requires >1000 labeled samples; overfits on 30 queries — deferred to Phase 2 if data volume supports it
- **Contradiction Detection:** Standard practice in financial systems (reconciliation audits)
- **DNC (Reasoning Trace Consistency):** Novel measurement; validated empirically in Week 4-6
- **Drift Detection:** Standard MLOps monitoring pattern; Lock 4 implementation is a lightweight version of PSI (Population Stability Index) monitoring
- **Template brittleness (paraphrase testing):** Gomes Jr. et al. (2022) "A Hereditary Attentive Template-based Approach for C-KBQA" — systems fail on minimally rephrased questions; paraphrase variants required in test set

---

**Last Updated:** 2026-03-01
**Status:** Ready for Adrian + Nicholas to implement Weeks 4-6 (Locks 1-3); Lock 4 targets Week 7+
**Contact:** Adrian (Engineering), Nicholas (QA)
**Scalability note:** Lock automation (automated retraining pipelines, Config Agent contradiction suggestions, centralized monitoring) is NOT in PoC scope. See Part 3 Initiative 7 and Part 5 Week 9-10 for Phase 2b planning.
