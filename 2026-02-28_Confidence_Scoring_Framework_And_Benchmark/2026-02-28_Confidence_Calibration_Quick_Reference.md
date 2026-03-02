# Confidence Calibration & Tool Calling: Quick Reference Tables (2024-2026)

**For:** Adrian, Ahmad, Ahmad Jr, Nicholas (engineering team)
**Purpose:** One-page lookup tables for decisions during Weeks 4-7

---

## Table 0: The "Quad-Lock" Defensive Architecture (4-Layer System for 99% Accuracy)

**Quick Summary:** Klar uses 4 independent verification layers to catch different failure modes. Locks 3 and 4 run on raw data BEFORE draft generation; Locks 1 and 2 run on the draft AFTER it is generated.

| Lock | Layer | Component | Owner | When It Runs | What It Does | Failure Mode Caught |
|------|-------|-----------|-------|-------------|-------------|-------------------|
| **3** | Circuit Breaker | Contradiction Matrix | Adrian | Before draft (on raw data) | Hard-stop if cross-source delta >5% | GIGO — data from two sources disagree before AI even drafts an answer |
| **4** | Drift Detection | Baseline Comparator | Adrian | Before draft (on raw data) | Tightens threshold if score distribution drifts from Week 4 baseline | Silent degradation — system was accurate but world has changed |
| **1** | Formula | 8-Factor Weighting (inc. DNC) | AI Agent | After draft generated | Generates raw confidence score (0-100) | Miscalibration (raw score ≠ actual accuracy) |
| **2** | Calibration | Temperature Scaling | Adrian + Nicholas | After Lock 1 | Transforms raw score → truthful probability | Systematic overconfidence (LLMs typically score 15-30 pp above actual accuracy; T range 1.5–3.0) |

**Execution Order:**
```
Query → [LOCK 3] Contradiction Matrix (cross-source delta >5%?)
  ├─ YES → ESCALATE immediately (circuit breaker; skip Lock 4, draft, Locks 1-2)
  └─ NO  → [LOCK 4] Drift Detection (score distribution shifted vs. Week 4 baseline?)
               ├─ DRIFTED → Tighten threshold for this session; continue
               └─ STABLE  → Use standard threshold; continue
                    → AI generates DRAFT internally (reasoning trace + answer)
                         → [LOCK 1] 8-Factor Score (on draft)
                              → [LOCK 2] Temperature Scaling (on raw score)
                                   → [COMPARE] Empirical Threshold
                                       ├─ ABOVE → SEND (+ DNC check)
                                       └─ BELOW → ESCALATE to AM
```

**Lock 3 Skip Logic — when Lock 3 fires, ALL subsequent steps are skipped:**

| Step Skipped | Reason |
|---|---|
| Lock 4 (Drift Detection) | No threshold to tighten — escalation is unconditional |
| Draft Generation | Data is untrustworthy; generating a draft would waste an AI call |
| Lock 1 (8-Factor Score) | No draft to score |
| Lock 2 (Temperature Scaling) | No raw score to calibrate |
| Threshold Decision | Irrelevant — circuit breaker overrides all scoring |

**Key Metrics:**
- **Lock 3 (Circuit Breaker):** Contradiction detection rate 5-15%, false positive <2%
- **Lock 4 (Drift Detection):** Monitors avg_raw_score, data_completeness, contradiction_rate vs. Week 4 baseline
- **Lock 1 (Formula):** Mean DNC ≥75%, 8-factor correlation r ≥0.70
- **Lock 2 (Calibration):** ECE reduction ≥0.15 pp, validation ECE <0.12

**DNC vs Shadow Check — they are NOT the same thing:**
- **DNC (Reasoning Trace Coherence):** Core factor inside Lock 1 — 10% weight in 8-factor formula. Numeric score (0-100) measuring whether AI's reasoning is internally consistent.
- **Shadow Check:** Supporting signal OUTSIDE the 8-factor formula — not weighted. Two-question LLM audit (Logic Check + Disclosure Check). Binary veto: FLAG overrides confidence score regardless of how high it is.

**See:** `2026-02-28_Defensive_Architecture_Framework.md` for full technical specification

---

## Table 1: Confidence Calibration Methods (Decision Matrix)

| Method                                            | How It Works                                                                      | Accuracy Gain                                             | Implementation                                      | Time to Deploy                   | Retraining? | Recommended for Klar?                    |
| ------------------------------------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------- | --------------------------------------------------- | -------------------------------- | ----------- | ---------------------------------------- |
| **Temperature Scaling**<br>⭐ **PRIMARY**          | Post-hoc calibration: divide logits by scalar T (fit on 30-query baseline). T > 1 = overconfident model (pushes toward 50%). T range for LLMs: 1.5–3.0. Does not change answer rankings. | ~20 pp ECE reduction; works on 30 samples | 2-3 lines of code; single scalar T_optimal | 1 day (Week 5) | No | ✅ **YES, Week 5 — USE THIS** (30-query constraint; isotonic needs 1000+) |
| **Isotonic Regression**<br>⚠️ **ALTERNATIVE**     | Post-hoc calibration: fit monotonic function to fix raw LLM miscalibration. Requires 1000+ samples for stable fit — too many for Week 4 baseline of 30 queries. | +23.6 pp ECE reduction (Amazon: 46%, biomedical: 23.6 pp) | sklearn.isotonic_regression | 1 week | No | ⚠️ **Only if 1000+ calibration samples available (Phase 2+)** |
| **Empirical Threshold Discovery** ⭐ **SECONDARY** | AFTER post-hoc calibration: find confidence % where calibrated accuracy ≥99%      | Variable (depends on calibration quality)                 | Histogram + threshold analysis on calibrated scores | 1 week (Week 6)                  | No          | ✅ **YES, Week 6** (CRITICAL SECOND STEP) |
| **Reinforcement Learning**                        | Fine-tune model with scoring rule rewards                                         | +20-30%                                                   | Needs labeled data + RL infra                       | 4-8 weeks                        | Yes         | ❌ No (too expensive)                     |
| **Distractor Normalization (DINCO)**              | Generate distractors; compare confidence across them                              | +10-20%                                                   | Multiple forward passes + normalization             | 2 weeks                          | No          | ⚠️ Maybe (complex implementation)        |
| **Steering Prompts (SteerConf)**                  | Prompt engineering to elicit better confidence                                    | +5-10%                                                    | Modify prompt                                       | 1 week                           | No          | ✅ **Low-effort, try first**              |
| **Selective Prediction (SelectLLM)**              | Fine-tune model to decline uncertain queries                                      | +15-25% (coverage-accuracy tradeoff)                      | Needs fine-tuning                                   | 4-8 weeks                        | Yes         | ❌ No (too expensive)                     |

**Klar's Two-Step Path (Research-Backed Production Methodology):**
- **Week 2-3:** Add steering prompts to improve baseline confidence (+5-10%)
- **Week 5 (CRITICAL - Post-Hoc Calibration FIRST):** Apply **temperature scaling** to fix raw LLM miscalibration
  - Problem: Claude assigns 95% confidence but is only 75% correct (±20 pp miscalibration typical; LLMs are systematically overconfident)
  - Solution: Use Week 4 baseline data (30 queries) to fit T_optimal (single scalar). T > 1 pushes scores toward 50%; typical LLM range T = 1.5–3.0
  - Result: ~20 pp ECE reduction; confidence now accurately reflects reality
  - Why not isotonic regression? Isotonic needs 1000+ samples for a stable fit — not available at Week 5. Use in Phase 2+ when data accumulates.
  - Production validation: MIT/IBM Thermometer (temperature scaling); Amazon (46% ECE reduction with isotonic at scale)
- **Week 6 (Empirical Threshold Discovery SECOND):** Test CALIBRATED confidence to find threshold where accuracy ≥99%
  - Input: Post-hoc calibrated confidence scores from Week 5
  - Process: Histogram analysis per query type
  - Output: Threshold per type (e.g., "Sales: 88% → 100% accuracy; Trend: 94% → 100% accuracy")
  - Production validation: Pyramid MoA (70% threshold), SQL generation (85% threshold)
- **Week 6+:** Self-consistency for complex queries (optional enhancement)

---

## Table 2: Expected Accuracy Ranges by Query Type & Approach

| Query Type | Baseline (No Klar) | +Prompt Eng | +State Machine | +Validation Layer | +Human Review | Industry Case Study |
|------------|-------------------|------------|---------------|------------------|----------------|-------------------|
| **Sales Metrics** | 60-70% | 75-85% | 80-90% | 88-96% | 95-99%+ | Parcha: 99% |
| **Campaign Performance** | 55-70% | 72-82% | 78-88% | 85-94% | 93-98% | (Not found) |
| **Trend Analysis** | 50-65% | 70-80% | 75-85% | 83-91% | 90-97% | ClimateAligned: 99% |
| **Retention Metrics** | 50-60% | 68-78% | 73-83% | 80-88% | 88-95% | (Not found) |
| **Cohort Analysis** | 45-60% | 65-75% | 70-80% | 77-85% | 85-92% | (Not found) |

**Reading Guide:** Row = query type. Column = cumulative accuracy gain. Example: Sales Metrics with prompt engineering + state machine = 80-90% accuracy expected.

**Klar Target (Week 7):**
- Simple queries (Sales, Members): 95%+ (achievable; target 99% with human review if needed)
- Complex queries (Trend, Retention, Cohort): 90-95% (realistic; 99% requires extensive review)

**Validation Plan:** Test prediction vs. actual on Week 4 baseline (30 queries). Measure accuracy by query type.

---

## Table 3: Confidence Calibration Error (ECE) Standards

| Level | ECE Value | Meaning | Industry Benchmark | Acceptable for Klar? |
|-------|-----------|---------|-------------------|----------------------|
| **Excellent** | <0.05 | Confidence = actual accuracy | High-stakes systems (medical, financial) | ❌ Unlikely (requires RL) |
| **Good** | 0.05-0.10 | Confidence ±5-10% from actual accuracy | Standard production systems | ✅ **Target this** |
| **Acceptable** | 0.10-0.15 | Confidence ±10-15% from actual accuracy | Current Claude baseline + some calibration | ✅ Achievable |
| **Poor** | 0.15-0.25 | High overconfidence; cannot trust confidence | Uncalibrated LLM | ❌ Not acceptable |
| **Unusable** | >0.25 | Confidence meaningless | Raw LLM output | ❌ Not acceptable |

**Klar's Plan:** Measure ECE per query type in Week 6. Target <0.12 per query type (align threshold so observed ECE matches this).

**Measurement (Week 6):**
```python
predicted_confidence = [0.92, 0.88, 0.85, 0.78, ...]  # From Klar's 8-factor formula
actual_accuracy = [1.0, 1.0, 0.0, 1.0, ...]  # Verified by human
ECE = mean(|predicted_confidence - actual_accuracy|)  # Should be <0.12
```

---

## Table 4: Tool Calling Accuracy by Tool Count & Architecture

| Tool Count | Flat Routing (All Tools) | State Machine (Grouped Tools) | Improvement | Notes |
|-----------|------------------------|-----------------------------|------------|-------|
| 3-5 | 94-96% | 95-97% | +1-2% | Minor difference; both work |
| 5-10 | 88-92% | 91-94% | +3-4% | State machine advantage emerges |
| 10-15 | 85-89% | 89-92% | +5-7% | Clear advantage |
| 15-20 | 80-85% | 87-91% | +7-10% | **Klar's zone** (16-20 tools) |
| 20-30 | 75-82% | 85-90% | +10-15% | State machine highly advantageous |
| 30+ | 65-75% | 80-88% | +15-25% | Use Tool Search (Anthropic) if this large |

**Klar's Design:** 5 sub-bots × 3-5 tools each = 16-20 tools total. Expected improvement: +7-10% vs. flat routing = ~89-94% tool accuracy (vs. 82-85% flat).

**Validation Plan (Week 2-3):** Test intent classification on 10 random queries. Measure:
- % routed to correct sub-bot (target ≥95%)
- % tool selected correctly within sub-bot (target ≥92%)

---

## Table 5: Data Quality Impact on Accuracy

| Data Factor | Optimal | Degraded | Critical Threshold | Accuracy Impact if Violated |
|------------|---------|----------|-------------------|---------------------------|
| **Freshness** | Hourly or real-time | >4 hours old | 2 hours | -15% to -40% accuracy |
| **Completeness** | >95% fields populated | 75-95% complete | <80% complete | -10% to -30% accuracy |
| **Schema Consistency** | Same field names/types across sources | 50-75% consistent | <50% consistent | -8% to -25% accuracy |
| **Documentation** | Complete data dictionary | Partial or absent | Missing | -5% to -15% accuracy |
| **Validation** | Source data already validated | Unvalidated | Multiple errors | -5% to -20% accuracy |

**Klar Week 1 Checklist (with Ben):**
- [ ] Confirm freshness SLA (target: hourly or real-time)
- [ ] Audit data completeness (sample 100 records; target >95%)
- [ ] Confirm schema consistency (all brands use same POS fields)
- [ ] Request data dictionary (needed for model context)
- [ ] Identify validation rules already in place (or plan to add)

**Risk:** If POS is >4 hours stale, expect accuracy -20% to -40%. Add disclaimer to all answers ("as of [timestamp]").

---

## Table 6: Empirical Threshold Calibration (Week 5-6 Template)

**For Each Query Type, Fill This Table:**

| Query Type | Threshold (%) | Queries at This Confidence | Correct at This Threshold | Accuracy % | Direct-Send Rate | Decision |
|-----------|---------------|--------------------------|--------------------------|-----------|-----------------|----------|
| **Sales Query** | 80 | 25/30 | 24/25 | 96% | 83% | ✓ Meet 99% |
| | 85 | 24/30 | 24/24 | 100% | 80% | ✓ Exceed 99% |
| | 88 | 22/30 | 22/22 | 100% | 73% | ✓ Use this? |
| | 90 | 19/30 | 19/19 | 100% | 63% | ⚠️ Good but too conservative |
| | 95 | 15/30 | 15/15 | 100% | 50% | ❌ Too conservative |
| **Campaign** | 85 | 22/30 | 21/22 | 95% | 73% | ❌ <99% |
| | 88 | 20/30 | 20/20 | 100% | 67% | ✓ Use? |
| | 90 | 18/30 | 18/18 | 100% | 60% | ✓ Use this |
| | 92 | 15/30 | 15/15 | 100% | 50% | ✓ Conservative alternative |
| **Trend** | 92 | 18/30 | 18/18 | 100% | 60% | ✓ Use? |
| | 94 | 16/30 | 16/16 | 100% | 53% | ✓ Conservative |
| | 96 | 12/30 | 12/12 | 100% | 40% | ❌ Too conservative |

**How to Fill:**
1. For each confidence threshold (70%, 75%, ..., 100%), count:
   - Queries with confidence ≥ threshold
   - How many of those are actually correct?
2. Calculate: Accuracy % = (Correct / Total at threshold) × 100%
3. Select threshold where accuracy ≥ 99% and direct-send rate is acceptable (60-80%)

**Example Decision:** Sales Query → use 88% (100% accuracy, 73% direct-send). Trend Analysis → use 94% (100% accuracy, 53% direct-send, more conservative due to complexity).

---

## Table 6a: Lock 3 — Contradiction Matrix Implementation Checklist (Week 5-6, Adrian)

**What Lock 3 does:** Compares values across two data sources (e.g., POS vs. Shopee) on the same field. If delta >5%, fires circuit breaker and escalates immediately — no draft is generated.

**Lock 3 is novel (no direct academic precedent). It requires empirical validation during the PoC.**

### Fields to Monitor (POS vs. Shopee)

| Field | POS Source | Shopee Source | Delta Formula | Escalation Trigger |
|---|---|---|---|---|
| Revenue (Rp) | `pos.revenue_today` | `shopee.gross_revenue` | `abs(POS - Shopee) / POS` | >5% |
| Settlement vs. Profit | `pos.net_profit` | `shopee.settlement_amount` | `abs(POS - Shopee) / POS` | >5% |
| Order count | `pos.order_count` | `shopee.order_count` | `abs(POS - Shopee) / POS` | >5% |

**Note:** Lock 3 only checks cross-source deltas on specific fields. It does NOT catch single-source anomalies (e.g., negative values within POS ledger) — those are caught by DNC Path 1.

### Scope: What Lock 3 Catches vs. What It Does Not

| Scenario | Lock 3 Catches? | Who Catches It Instead? |
|---|---|---|
| POS revenue vs. Shopee revenue delta >5% | ✅ Yes → escalate | N/A |
| Negative values within POS ledger (single-source) | ❌ No | DNC Path 1 (keyword: "negative value") |
| POS vs. Shopee delta = 4% (below threshold) | ❌ No | DNC Path 1 (keyword: "mismatch") |
| Unusual spike within one data source | ❌ No | DNC Path 1 (keyword: "anomaly") |

### Implementation Checklist (Adrian, Week 5)

```python
def contradiction_matrix_check(pos_data, shopee_data):
    """Lock 3: Run BEFORE draft generation. Returns (passed, escalation_reason)."""
    checks = [
        ("revenue", pos_data["revenue"], shopee_data["gross_revenue"]),
        ("settlement_vs_profit", pos_data["net_profit"], shopee_data["settlement"]),
        ("order_count", pos_data["orders"], shopee_data["orders"]),
    ]
    for field, pos_val, shopee_val in checks:
        if pos_val == 0:
            return False, f"Division by zero on field: {field}"
        delta = abs(pos_val - shopee_val) / pos_val
        if delta > 0.05:  # 5% threshold
            return False, f"Cross-source delta {delta:.1%} on {field} exceeds 5% threshold"
    return True, None
```

**Week 5 Test Cases (Nicholas):**

| Test | POS Value | Shopee Value | Expected | Pass? |
|---|---|---|---|---|
| Revenue delta = 3% (below threshold) | 10,000,000 | 9,700,000 | PASS (no escalation) | |
| Revenue delta = 6% (above threshold) | 10,000,000 | 9,400,000 | ESCALATE | |
| Revenue delta = exactly 5% | 10,000,000 | 9,500,000 | PASS (boundary — 5% is not >5%) | |
| Order count delta = 8% | 100 | 92 | ESCALATE | |
| POS value = 0 (division by zero) | 0 | 500,000 | ESCALATE (edge case) | |

**Success Criteria (Week 5):** All 5 test cases pass. No false positives on 10 real queries from Week 4 baseline that had no actual contradiction.

---

## Table 6b: Lock 4 — Drift Detection Monitoring Dashboard (Week 7+, Adrian)

**What Lock 4 does:** Compares current session's score distribution against the Week 4 baseline. If scores have drifted significantly, it tightens the escalation threshold for that session — preventing silent accuracy degradation.

**Lock 4 runs BEFORE draft generation** (alongside Lock 3, on raw data). It does not block answers like Lock 3 — it adjusts the threshold used in the Lock 2 comparison.

### Baseline Values (Recorded at Week 4 — Fill These In)

```python
week4_baseline = {
    "avg_raw_score": 0.83,       # Mean of 8-factor raw scores across 30 baseline queries
    "data_completeness": 0.92,   # Average of Factor 1 (Completeness) scores across 30 queries
    "contradiction_rate": 0.08,  # Count of Lock 3 triggers ÷ 30
}
# Note: These are placeholder values computed from Week 4 run.
# Replace with actual values after Nicholas runs the 30-query baseline.
```

### Drift Detection Logic

| Metric | Baseline | Drift Alert Threshold | Action if Drifted |
|---|---|---|---|
| `avg_raw_score` | 0.83 | Drop >0.10 from baseline (i.e., <0.73) | Tighten threshold by +5 pp |
| `data_completeness` | 0.92 | Drop >0.10 (i.e., <0.82) | Tighten threshold by +5 pp; add "data may be incomplete" disclaimer |
| `contradiction_rate` | 0.08 | Rise >0.15 (i.e., >15% of queries hitting Lock 3) | Flag to Stephen; may indicate data source issue |

**Threshold tightening rule:** If any metric drifts, add +5 pp to the empirical threshold discovered in Week 6. Example: if Sales threshold = 88%, tighten to 93% for that session.

### Weekly Monitoring Checklist (Adrian + Nicholas, Week 7+)

| Check | Frequency | Owner | Alert If |
|---|---|---|---|
| `avg_raw_score` vs. baseline | Weekly | Adrian | Drops >0.10 from baseline |
| `data_completeness` vs. baseline | Weekly | Adrian | Drops >0.10 from baseline |
| `contradiction_rate` | Weekly | Nicholas | Rises above 15% |
| ECE on new queries | Bi-weekly | Nicholas | ECE >0.12 per query type |
| Direct-send rate | Weekly | Stephen | Drops below 50% (over-escalating) or rises above 85% (under-escalating) |

### Response Procedures

| Scenario | Response |
|---|---|
| `avg_raw_score` drifts (system less confident than baseline) | Tighten threshold +5 pp; investigate if data quality degraded |
| `contradiction_rate` rises >15% | Alert Ben — likely POS or Shopee data source issue |
| ECE >0.12 for 2+ consecutive weeks | Re-fit T_optimal using new data; rerun temperature scaling calibration |
| Direct-send rate <50% for 1+ week | Review threshold — may need to loosen slightly; check if query types have shifted |

---

## Table 7: Escalation Strategy by Confidence Band

**Recommended Multi-Level Escalation (optional; can start simpler):**

| Confidence Band | Decision | Workflow | Time to AM Review | Trust Level |
|-----------------|----------|----------|------------------|------------|
| **≥95%** | Send directly (no review) | Query → AI → Customer | 0 min | Very High |
| **88-94%** | Send with light review flag | Query → AI → AM flag "review if time" → Customer | 1-2 min (optional) | High |
| **70-87%** | Route to AM for review | Query → AI → AM review → Customer | 3-5 min (mandatory) | Medium |
| **<70%** | Escalate to specialist (Ben) | Query → AI → Ben (complex data question) | 10+ min | Low (needs expertise) |

**For Lixus PoC:** Start simple (binary: ≥threshold send, <threshold escalate). Promote to multi-level only if Week 6 shows persistent "medium confidence" cluster.

**Measurement (Week 7):**
- % of queries sent directly (target 50-70%)
- AM time saved per week (target 3+ hours/day)
- Trust score from AMs (target 8/10 comfort level on direct-send)

---

## Table 8: Compound Reliability Risk (Multi-Step Queries)

**For Complex Queries with Sequential Steps:**

| # Steps | Per-Step Accuracy | Overall System Accuracy | Risk Level | Mitigation |
|---------|------------------|----------------------|-----------|-----------|
| 1 | 95% | 95% | Low | None needed |
| 2 | 95% | 90% | Low | Log step confidence |
| 3 | 95% | 86% | Medium | ⚠️ Verify mid-chain |
| 4 | 95% | 82% | Medium | ⚠️ Add validation |
| 5 | 95% | 77% | **High** | ❌ Add step-level checks |
| 10 | 99% | 90% | **High** | ❌ Verify high-confidence queries only |

**Klar Application:**
- **Trend Analysis** (3-4 steps: fetch → validate → analyze → format): At 95% per step = 82-86% overall. **Add explicit validation at step 2.**
- **Cohort Analysis** (4-5 steps: define segment → fetch → analyze → validate → summarize): At 95% per step = 77-82% overall. **Add validation at steps 2 and 4. Escalate if any step <90%.**

**Week 7 Implementation:**
```python
# Pseudo-code for multi-step validation
def analyze_retention_cohorts(query):
    confidence = []

    # Step 1: Define cohort
    cohort_def, conf1 = define_cohort(query)
    confidence.append(conf1)
    if conf1 < 0.85:  # Threshold per step
        escalate(f"Cohort definition unclear: {conf1}")

    # Step 2: Fetch data
    data, conf2 = fetch_cohort_data(cohort_def)
    confidence.append(conf2)
    if conf2 < 0.85:
        escalate(f"Data quality issue: {conf2}")

    # Step 3: Analyze
    analysis, conf3 = analyze_retention(data)
    confidence.append(conf3)

    # Final confidence = compound
    final_confidence = min(confidence)
    if final_confidence < THRESHOLD[query_type]:
        escalate(analysis, min_step=confidence.index(min(confidence)))
```

---

## Table 9: Week-by-Week Calibration Checklist

| Week | Task | Success Criteria | Owner | Research Alignment |
|------|------|-----------------|-------|-------------------|
| **1** | Data validation with Ben | 4/4 checks passed (freshness, completeness, schema, docs) | Ben + Stephen | Section 5 (Data Quality) |
| **2-3** | Sub-bot design + tool grouping | 5 sub-bots, 16-20 tools, <5 per sub-bot | Adrian + Ahmad | Table 4 (Tool Calling) |
| **3** | Intent classification testing | 95%+ routed to correct sub-bot on 10 test queries | Ahmad Jr | Routing research |
| **4** | Baseline test (30 queries) | Record confidence, actual accuracy; calculate correlation r >0.70 | Nicholas (QA) | Table 6 (Calibration) |
| **4** | Confidence-accuracy analysis | Spearman correlation >0.70; no systematic bias | Stephen + Adrian | Calibration research |
| **5** | Post-Hoc Calibration (Temperature Scaling) ⭐ CRITICAL | Fit T_optimal on Week 4 baseline (30 queries); measure ECE reduction. **Use temperature scaling, not isotonic regression** — isotonic needs 1000+ samples; temperature scaling works on 30. | Adrian + Stephen | MIT/IBM Thermometer; production methodology |
| **5** | Validate calibration quality | ECE <0.20 on calibration set; no systematic bias in calibrated scores | Nicholas (QA) | Calibration research |
| **6** | Empirical Threshold Discovery (on CALIBRATED scores) | Fill Table 6 per query type using calibrated confidence; identify threshold for each | Stephen | Escalation research (production validation) |
| **6** | Validate 8-factor weights | Regression: measure β₁,...,β₈ vs. hypothesis (0.25, 0.15, 0.15, 0.20, 0.15, 0.10) | Adrian | Confidence research |
| **6** | Hold-out test (10-15 queries) | Apply thresholds to new queries; validate accuracy target | Nicholas (QA) | Validation |
| **7** | Escalation logic implementation | Code + AM training on threshold interpretation | Ahmad + Stephen | Escalation research |
| **7** | Lock 4 Drift Detection — record baseline values | Record week4_baseline (avg_raw_score, data_completeness, contradiction_rate) from Week 4 data. Set drift alert thresholds (see Table 6b). | Adrian | DAF Lock 4 specification |
| **7** | Final measurement (30 new queries) | Accuracy ≥99% simple, ≥95% complex; ECE <0.12 per type | Nicholas (QA) | Accuracy research |
| **9-11** | Weekly drift monitoring | Check avg_raw_score, data_completeness, contradiction_rate vs. baseline weekly. Tighten threshold if drift >0.10. | Adrian + Nicholas | Table 6b monitoring checklist |

---

## Table 10: When to Use Each Confidence Method (Decision Tree)

```
START: Need better confidence calibration?
  |
  ├─→ Have 30+ baseline examples (from Week 4)?
  |    YES → Continue (you do!)
  |    NO → Collect more data
  |
  ├─→ STEP 1: Apply post-hoc calibration (Week 5)
  |    ├─→ Have 30 queries (Week 4 baseline)?
  |    |    YES → Use temperature scaling [PRIMARY — 2-3 lines of code, works on 30 samples]
  |    |    Have 1000+ queries (Phase 2+)?
  |    |    YES → Use isotonic regression [BETTER ECE reduction at scale - 23.6 pp]
  |    |    Result: ~20 pp ECE (confidence now reflects actual accuracy)
  |    |
  |    └─→ Success Criteria: ECE <0.20 on validation set
  |
  ├─→ STEP 2: Empirical threshold discovery (Week 6, on CALIBRATED scores)
  |    ├─→ Use histogram analysis: At what calibrated confidence = 99% accuracy?
  |    |    Result per query type: Sales (88%), Trend (94%), Retention (90%), etc.
  |    |
  |    └─→ Success Criteria: Threshold identified per query type; direct-send rate 60-80%
  |
  ├─→ STEP 3 (optional): Advanced methods (Week 6+)
  |    ├─→ Self-consistency for complex queries (40% cost reduction)
  |    ├─→ Distractor normalization (DINCO) for edge cases
  |    ├─→ Do NOT use: RL (expensive), Selective Prediction (expensive)
  |
  └─→ KLAR'S PRODUCTION PATH (Research-Backed):
      Week 2-3: Add steering prompts (+5-10%)
      Week 4: Baseline test (30 queries) + correlation analysis
      Week 5: ⭐ Post-hoc calibration with temperature scaling (~20 pp ECE; isotonic deferred to Phase 2+)
      Week 6: ⭐ Empirical threshold discovery on CALIBRATED scores
      Week 6+: Self-consistency (optional, if time permits)
      RESULT: Raw confidence (60% accuracy on 95% confident) → Calibrated confidence (95% accurate on 95% confident)
              +99% accuracy on direct-send queries
              3+ hours/day AM time savings
```

---

## References & Full Methodology

For detailed methodology, academic citations, and case studies, see:
- **Full Analysis:** `/Users/stephenhau/Documents/Work/Klar_Lixus/2026-02-28_LLM_Research_Benchmark_Analysis.md`
- **Executive Summary:** `/Users/stephenhau/Documents/Work/Klar_Lixus/2026-02-28_Research_Benchmark_Executive_Summary.md`

---

**Last Updated:** 2026-03-01 — Updated: Triple-Lock → Quad-Lock (Lock 4 Drift Detection added); Lock 2 changed from Isotonic Regression → Temperature Scaling (30-query constraint); Lock 3 implementation checklist added (Table 6a); Lock 4 monitoring dashboard added (Table 6b); DNC vs Shadow Check clarification added to Table 0; Table 9 and Table 10 updated to reflect Temperature Scaling + Lock 4
**For Questions:** Contact Stephen (PM) or Adrian (Lead Engineer)
