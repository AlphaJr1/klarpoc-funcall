# Klar LLM Research Benchmark: Executive Summary (2024-2026)

**Prepared for:** Julius, Stephen, Adrian
**Date:** 2026-02-28
**Purpose:** Quick reference—how Klar's framework compares to latest industry research

---

## The Bottom Line

Klar's approach to confidence calibration and escalation routing is **aligned with 2024-2026 industry research**. We have a clear path to 99% accuracy on simple queries and 95-98% on complex queries. Success depends on:
1. **Rigorous data validation (Week 1)** — with Ben, confirm freshness, completeness, schema
2. **Post-hoc calibration (Week 5)** — isotonic regression to fix raw LLM miscalibration (non-negotiable)
3. **Empirical threshold discovery (Week 6)** — find confidence threshold where accuracy ≥99.9%

This two-step calibration approach (post-hoc + empirical threshold) is production-standard across Amazon, biomedical NLP, and MIT/IBM research (2024-2026). Do not skip post-hoc calibration.

---

## 1. Confidence Calibration: Industry Finds No Magic Bullet

**The Problem:** LLMs express confidence poorly. Even GPT-4 and Claude assign high confidence to incorrect answers.

**Industry Approaches (2024-2026):**
| Method | Accuracy Gain | Cost | Feasibility for Klar |
|--------|---------------|------|----------------------|
| Reinforcement Learning (RL) | Best (ECE→0.08) | High (retrain model) | No—too expensive for PoC |
| Isotonic Regression (post-hoc) | Good (ECE→0.10-0.12) | Low | **Yes—use if 30+ examples per query type** |
| Distractor Normalization (DINCO) | Good | Medium | Maybe—requires multiple forward passes |
| Steering Prompts (SteerConf) | Modest | Low | Yes—easy to implement |
| Selective Prediction (SelectLLM) | Good (confidence-aware tuning) | High | No—requires fine-tuning |

**Klar's Approach (Research-Backed Two-Step):**
1. **Week 5: Post-Hoc Calibration (Isotonic Regression) — PRIMARY**
   - Use Week 4 baseline (30 queries) to fix raw LLM miscalibration
   - Isotonic regression: -23.6 pp ECE reduction (production-proven: Amazon 46%, biomedical NLP 23.6 pp)
   - CRITICAL because raw Claude confidence is off by 10-40 pp

2. **Week 6: Empirical Threshold Discovery — SECONDARY**
   - On CALIBRATED scores: find threshold where accuracy ≥99.9%
   - Example: "When CALIBRATED confidence = 88%, are answers 99.9% accurate?"
   - Varies per query type (sales vs. trend vs. cohort)

**Assessment:** ✅ Two-step approach is production-standard (Amazon, MIT/IBM, biomedical research). Target ECE <0.12 after post-hoc calibration. Week 5 post-hoc calibration is non-negotiable—do not skip to empirical threshold discovery without it.

---

## 2. Accuracy: 99% Achievable; 99.9% Aspirational

**Research Findings:**

| Query Type | Single LLM | With Prompt + RAG | With Validation | With Human Review | Industry Case Study |
|------------|-----------|-------------------|-----------------|------------------|-------------------|
| **Simple (sales, members)** | 60-70% | 85-95% | 92-97% | 98-99%+ | Parcha: 99% |
| **Complex (trends, cohorts)** | 50-65% | 75-85% | 85-95% | 95-98% | ClimateAligned: 99% (RAG-only) |

**How 99% is Achieved in Production:**
1. Prompt engineering + few-shot examples: +30% accuracy
2. RAG (high-quality retrieval): +15-20% accuracy
3. Validation checks (schema, business rules): +8-12% accuracy
4. Human review on low-confidence: +2-5% accuracy

**Total Impact: 60% → 99%**

**Klar's Gaps (Today):** No explicit validation layer or human-in-the-loop flagging. Plan for Week 7.

**Assessment:** ✅ 99% on simple queries is achievable. ⚠️ 99% on complex queries requires ALL layers. ❌ 99.9% unlikely without prohibitive review burden.

---

## 3. Tool Calling: State Machines Beat Flat Routing

**The Problem:** As tool count increases, accuracy drops.

| Tools | Linear Routing (flat) | State Machine (grouped) | Improvement |
|-------|----------------------|------------------------|-------------|
| 5 tools | 92% | 94% | +2% |
| 10 tools | 88% | 91% | +3% |
| 20 tools | 80% | 87% | +7% |
| 30+ tools | 70% | 85% | +15% |

**Why:** Scoping tools per sub-bot = two-stage routing (intent → sub-bot → tool selection). Reduces cognitive load on LLM.

**Klar's Design:** 5 sub-bots (Sales Query, Campaign, Trend, Retention, Cohort) × 3-5 tools each = 16-20 tools total. Two-stage routing.

**Assessment:** ✅ State machine architecture is optimal for Lixus's scope. Estimated accuracy gain: +5-10% vs. flat routing.

---

## 4. Escalation: The Real Bottleneck

**Key Finding:** If 70% of queries handled confidently by AI, operational cost drops 70%. Threshold calibration is empirical, not universal.

**What Companies Do:**
```
If Confidence >= Threshold:
    Send directly
Else:
    Route to human (AM) for review
```

**Calibration Example (from Week 5-6):**
- Sales Query: Threshold 88% → 99.5% accuracy, 82% direct-send
- Retention: Threshold 93% → 99.2% accuracy, 55% direct-send
- Cohort: Threshold 95% → 98.8% accuracy, 40% direct-send

**No Universal Threshold.** Varies by query complexity.

**Klar's Plan:** Empirical discovery in Week 5-6. Align with industry practice.

**Assessment:** ✅ Klar's approach is correct. Spend Week 5-6 on this, not new features.

---

## 5. Data Quality: Massive Lever for Accuracy

**Research (2025):** If data is stale (>1 hour old), accuracy drops -15% to -40%.

**Critical Validations (Before Week 2):**
- [ ] Data freshness: How often updated? (Confirm with Ben)
- [ ] Completeness: % of records with all fields? (Target >95%)
- [ ] Schema consistency: All brands use same POS schema? (Yes/No)
- [ ] Documentation: Data dictionary available? (Needed for model context)

**RAG Insight:** Quality > Quantity. Retrieve 3-5 high-quality documents, not 20 noisy ones. Helps accuracy AND speed.

**Klar's POS Strategy:** Safer than dashboard (single source of truth, audit trail). Good choice.

**Assessment:** ✅ Data validation is Week 1 blocker. Confirm with Ben or accuracy will suffer.

---

## 6. Klar's 8-Factor Confidence Formula + Triple-Lock Defensive Architecture

**Updated Formula (8-Factor, incl. Reasoning Trace DNC):**
```
Confidence = (
    Completeness      × 0.25 +   ↓ from 30% (reduced to prioritize integrity)
    Complexity        × 0.15 +   ↓ from 20% (reduced to prioritize integrity)
    Freshness         × 0.15 +   — unchanged
    Tool_Routing      × 0.20 +   — unchanged (critical signal)
    Data_Validation   × 0.15 +   — unchanged (critical signal)
    Reasoning_Trace_DNC × 0.10   NEW: catches "distracted AI" failures
)
```

**Triple-Lock Defensive Architecture:**
- **Lock 1 (Formula):** 8-Factor score catches miscalibration at source
- **Lock 2 (Calibration):** Isotonic Regression corrects systematic LLM bias (-23.6 pp ECE)
- **Lock 3 (Circuit Breaker):** Contradiction Matrix hard-stops if data integrity fails (>5% delta between POS and Shopee)
- **Dual ownership:** Adrian (technical contradictions) + Nicholas (logic contradictions)

**Assessment:**
- ✅ Weights revised to prioritize process integrity over query difficulty
- ✅ DNC (Reasoning Trace) catches failure mode not addressed by other factors
- ✅ Triple-Lock is defensive-in-depth (each lock catches a different failure mode)
- ❌ 8-factor formula still novel; must validate weights empirically in Week 5-6
- 🔧 Recommend regression analysis in Week 5-6: "Which factors actually drive accuracy?"

**Expected Outcome:** Weight validation may fine-tune (e.g., Tool_Routing may dominate). DNC weight (10%) to be validated against baseline data.

---

## 7. Multi-Agent System Risk: Compound Reliability

**Warning from Research:**

Single agent at 99.5% reliability = reliable system.

Multi-agent system with 10 steps at 99% each = 90.4% overall (0.99^10).

**This is Klar's compound risk:** If Trend Analysis has 5 sequential steps (fetch data → validate → analyze → format → summarize), each at 95%, overall = 77% accuracy.

**Mitigation:** Track confidence at each step. Escalate if ANY step drops below threshold.

**Assessment:** ⚠️ Design complex queries carefully. Use explicit step-by-step verification, not implicit chaining.

---

## 8. Klar vs. Industry: Detailed Scorecard

| Dimension | Klar | Industry | Status |
|-----------|------|----------|--------|
| **Confidence Calibration Approach** | Triple-Lock (Isotonic → Threshold) | Post-hoc (isotonic) or RL | ✅ Aligned; production-standard |
| **Per-Query-Type Thresholds** | Yes (Sales ≠ Cohort) | Sometimes (domain-specific) | ✅ Advantage: more granular |
| **State Machine Routing** | Yes (5 sub-bots) | Yes (LangGraph, StateFlow) | ✅ Aligned; +5-10% accuracy vs. flat |
| **Data Quality Strategy** | POS (curated source) | Curated > raw data | ✅ Aligned; lower hallucination risk |
| **8-Factor Formula + DNC** | Novel (incl. Reasoning Trace DNC) | Single-factor (research standard) | ⚠️ Novel; must validate weights |
| **Contradiction Matrix (Lock 3)** | Yes (5% delta circuit breaker) | Not standard | ✅ Klar advantage (defensive-in-depth) |
| **Multi-Step Verification** | Implicit (chaining) | Explicit (state-by-state validation) | ❌ Improvement needed; add step-level confidence checks |
| **Accuracy Target** | 99% | 95-99% achievable | ✅ Realistic for simple; aspirational for complex |

---

## 9. What Research **Did NOT Find**

- ❌ **Universal confidence threshold** — Every system calibrates its own threshold
- ❌ **LLM-native perfect calibration** — Even with steering prompts, ECE > 0.08
- ❌ **99.9% accuracy without human review** — Not in published case studies
- ❌ **Tool calling >95% without validation** — Requires schema checks, business rule validation
- ❌ **Single-source data safe for LLM** — All systems use multiple validation layers (prompt + RAG + validation + human)

**Implication:** Klar's conservative targets (99% simple, 95-98% complex) are realistic. 99.9% requires human review on most complex queries.

---

## 10. Action Plan: Weeks 1-12

| Week | Critical Action | Success Criteria | Research Alignment |
|------|-----------------|------------------|-------------------|
| **1** | Confirm POS data freshness, completeness with Ben | Yes ✓ on all 4 validations | Data quality research (Section 5) |
| **2-3** | Design 5 sub-bots (16-20 tools), state machine routing | Intent routing 90%+ on 10 test queries | Tool calling research (Section 2) |
| **4** | Baseline test: 50+ queries (simple + early complex), record confidence | Confidence-accuracy correlation r >0.70 | Calibration research (Section 1) |
| **5-8** | Build complex analytics sub-bots (Trend, Retention, Cohort, Benchmark) | 100+ complex queries validated; step-level checks in place | Multi-agent reliability (Section 7) |
| **9** | Simple calibration: isotonic regression → threshold discovery; validate 8-factor weights | Simple threshold (92-98%); 8-factor weights empirically justified | Escalation research (Section 3) |
| **10** | Complex calibration: threshold per query type (Trend, Retention, Cohort) | Complex threshold (85-95%); ECE <0.12 per query type | Escalation research (Section 3) |
| **11** | Deploy calibrated thresholds; production hardening; documentation | Both thresholds live; monitoring in place | All sections |
| **12** | Final demo, AM training, handoff to Julius | Final accuracy ≥99% simple, ≥95% complex; adoption ≥50% | Multi-agent reliability (Section 7) |

---

## 11. Recommended Reading (In Priority Order)

1. **For Julius (Business Case):** Section 2 (Accuracy Targets) + Section 3 (Escalation ROI: 70% cost reduction)
2. **For Adrian (Architecture):** Section 2 (Tool Calling) + Section 7 (Multi-Agent Risk) + Section 10 (Week-by-Week)
3. **For Stephen (Calibration Sprint):** Section 1 (Confidence Methods) + Section 3 (Empirical Calibration) + Section 10 (Weeks 9-11 execution)
4. **For Ben (Data Validation):** Section 5 (Data Quality Checklist) + Section 4 (RAG Insights)

---

## 12. Key Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| POS data stale (>4 hours) | Medium | High (accuracy -20%) | **Week 1: Confirm freshness SLA with Ben** |
| 8-factor weights are wrong | Medium | Medium (accuracy -5-10%) | **Week 9: Empirical weight validation via regression (on Week 4 baseline data)** |
| Compound reliability issue on complex queries | Low | Medium (90% instead of 95%) | **Weeks 5-8: Add step-level confidence checks during complex sub-bot build** |
| Threshold calibration set too low (oversend) | Low | High (trust erosion) | **Week 6: Validate threshold on hold-out test set** |
| 99.9% accuracy expectation (Julius) | Low | Critical | **Week 4: Align expectations. 99% simple achievable; 99.9% requires human review** |

---

## Bottom Line for Julius

Klar's PoC strategy is **research-backed and achievable:**

1. **Simple queries (sales, members):** 99% accuracy is realistic and in line with production case studies.
2. **Complex queries (retention, trends):** 95-98% accuracy is realistic. 99% is possible with validation but requires human review on 40-60% of answers.
3. **Time savings:** If we achieve 99% accuracy on 80% of queries (direct-send without review), AMs save 3+ hours/day.
4. **Confidence calibration:** No magic formula exists in literature. Klar's empirical approach (Week 5-6) is industry best practice.
5. **Data is king:** Validate Lixus's POS data freshness (Week 1). If stale, accuracy drops significantly.

**Post-PoC Decision:** If accuracy target is truly 99.9% on complex queries, plan for extensive human review (eliminates time savings). If target is 95-98% with limited review, plan for 50-70% direct-send rate and 3+ hours/day AM time savings.

---

## Full Analysis

For detailed findings, tables, methodology, and research citations, see:
**`/Users/stephenhau/Documents/Work/Klar_Lixus/2026-02-28_LLM_Research_Benchmark_Analysis.md`**

---

**Document Prepared By:** Stephen (PM) with Claude
**Status:** Ready for stakeholder review
**Next Update:** Post-Week 4 calibration (data may shift targets)
