# Klar Confidence Score Calibration Framework

**Date:** 28 Feb 2026
**Owner:** Nicholas (QA Lead)
**Status:** 🟢 Ready for Week 4 Baseline Testing
**Purpose:** Define, measure, and calibrate confidence scoring to achieve **99.9% accuracy on direct-sent answers** (Lixus requirement, Part 2 Challenge #2)

---

## Executive Summary

**The Problem:**
- Julius: "Wrong answers are worse than no answer"
- AMs won't trust AI unless accuracy is proven
- **Adoption threshold:** If accuracy <80%, AMs won't send direct to clients

**Our Solution (Two-Step, Research-Backed):**
- **Week 5 (POST-HOC CALIBRATION):** Fix raw LLM miscalibration using isotonic regression
  - Problem: Claude says "95% confident" but is only 75% correct (±20 pp miscalibration)
  - Fix: Use Week 4 baseline data to train isotonic regression function
  - Result: Calibrated confidence now reflects actual accuracy (-23.6 pp ECE improvement, production-proven)

- **Week 6 (EMPIRICAL THRESHOLD DISCOVERY):** Find threshold where CALIBRATED confidence = 99.9% accuracy
  - Question: "At what CALIBRATED confidence level are answers 99.9% correct?"
  - Answer: Use histogram analysis to find threshold per query type
  - Example: "Sales queries at 88% calibrated confidence → 99.9% accurate"

**Expected Outcome (Week 7):**
- Simple queries with CALIBRATED confidence ≥88-95% (threshold varies by type) → Send directly to client (99.9% accuracy)
- Simple queries with CALIBRATED confidence 70-88% → AM reviews first
- All queries with CALIBRATED confidence <70% → Escalate to engineer

**Why This Works:**
- Week 5 isotonic regression fixes the 20-40 pp miscalibration in raw Claude scores
- Week 6 empirical threshold discovers where the NOW-RELIABLE confidence scores match 99.9% accuracy
- This two-step process is production-proven (Amazon, biomedical NLP, MIT/IBM)

---

## Part 1: Confidence Score Framework (Parameters)

### Overview (Updated to 8-Factor Formula)
Klar confidence score = weighted sum of 8 measurable factors (0-100):

| Factor | Weight | Measurement | Why It Matters | Status |
|--------|--------|-------------|----------------|--------|
| **Completeness** | 25% | % of required fields available in data | If data is missing, AI must hallucinate | ↓ 30%→25% (prioritize integrity) |
| **Complexity** | 15% | Query type (simple/medium/complex) | Complex queries are harder to answer correctly | ↓ 20%→15% (prioritize integrity) |
| **Freshness** | 15% | Age of data (same-day vs. stale) | Stale data = wrong answers | — unchanged |
| **Tool Routing** | 20% | Did AI call the right tool? | Wrong tool = wrong answer, even if data is good | — unchanged (critical) |
| **Data Validation** | 15% | No data quality errors (negatives, nulls, inconsistencies) | Corrupt data = corrupt answer | — unchanged (critical) |
| **[NEW] Reasoning Trace DNC** | 10% | Does AI's reasoning align with final output? | Catches "distracted AI" failures (identifies when AI found right answer but was pulled away by contradictions) | **NEW: Critical for 99.9% accuracy** |

**Updated Formula (8-Factor):**
```
Confidence Score = (
    Completeness × 0.25 +
    Complexity × 0.15 +
    Freshness × 0.15 +
    Tool_Routing × 0.20 +
    Data_Validation × 0.15 +
    Reasoning_Trace_DNC × 0.10
)
```

**Rationale for Weight Changes:**
- Reduced Completeness (30%→25%) and Complexity (20%→15%) to prioritize "Process Integrity" (DNC) over "Query Difficulty"
- Tool Routing and Data Validation remain unchanged (critical signals)
- Added DNC (10%) to catch reasoning failures that other factors miss (e.g., AI found Rp 5M but got distracted by sync error and returned Rp 0)

---

## Part 2: Parameter Definitions & Measurement

### Parameter 1: Completeness (25% weight)

**Definition:** Percentage of data fields required to answer the query that are actually available in the system.

**Measurement Formula:**
```python
def completeness_score(query_fields_required, data_fields_available):
    """
    Returns: 0-100
    Example:
      Required: ["revenue", "date", "store"]
      Available: ["revenue", "date", "store", "tax", "discount"]
      Result: 100 (all 3 required fields present)

      Required: ["revenue", "new_customers", "repeat_customers"]
      Available: ["revenue"]  (new_customers NOT in Loyverse)
      Result: 33 (only 1/3 fields available)
    """
    if not query_fields_required:
        return 100

    available_count = len([f for f in query_fields_required
                          if f in data_fields_available])

    completeness = 100 * (available_count / len(query_fields_required))

    return completeness
```

**Real-World Examples (Using sample-data-loyverse.json):**

| Query | Required Fields | Available in Data? | Completeness Score |
|-------|-----------------|-------------------|-------------------|
| "What's revenue for Feb 24?" | revenue, date | ✅ Both in daily_summary | **100** |
| "Top 3 products?" | product_name, qty_sold | ✅ Both in transactions | **100** |
| "Revenue by payment method?" | revenue, payment_method | ✅ Both in transactions | **100** |
| "New customer retention cohort?" | customer_id, repeat_status, cohort | ⚠️ customer_id exists, repeat_status = can infer, cohort = NOT available | **67** |
| "Revenue by loyalty program tier?" | revenue, loyalty_tier | ❌ loyalty_tier NOT in data | **50** |

**Key Rule:** If a required field is genuinely missing (not in POS API at all), completeness is **penalized heavily** → confidence drops to 50-70% range → escalates for AM review.

---

### Parameter 2: Complexity (15% weight)

**Definition:** Query complexity tier (simple/medium/complex) determines baseline accuracy we can expect.

**Measurement Formula:**
```python
def query_complexity_score(query):
    """
    Scores complexity based on query characteristics.
    Simple (0-30):    Baseline confidence 95%
    Medium (30-60):   Baseline confidence 80%
    Complex (60-100): Baseline confidence 60%
    """

    complexity = 0

    # Factor 1: Number of data entities (stores/dates/brands)
    num_stores = count_stores_in_query(query)
    num_dates = count_dates_in_query(query)
    num_brands = count_brands_in_query(query)

    entities = num_stores + num_dates + num_brands
    if entities == 1:
        complexity += 5
    elif entities <= 3:
        complexity += 15
    elif entities <= 5:
        complexity += 25
    else:
        complexity += 35

    # Factor 2: Aggregation type
    aggregation = identify_aggregation(query)
    if aggregation in ["COUNT", "SUM", "AVG"]:
        complexity += 10
    elif aggregation in ["GROUP_BY", "FILTER"]:
        complexity += 20
    elif aggregation in ["JOIN", "WINDOW", "COHORT"]:
        complexity += 35

    # Factor 3: Time period
    time_period = extract_date_range(query)
    if time_period <= 1:  # "today"
        complexity += 5
    elif time_period <= 7:  # "this week"
        complexity += 15
    elif time_period <= 30:  # "this month"
        complexity += 20
    else:
        complexity += 30

    # Factor 4: Number of filters
    num_filters = count_filters(query)
    complexity += min(num_filters * 10, 30)

    return min(complexity, 100)  # Cap at 100
```

**Real-World Examples:**

| Query | Stores | Dates | Aggregation | Time Period | Filters | Score | Tier |
|-------|--------|-------|-------------|-------------|---------|-------|------|
| "Revenue today?" | 1 | 1 | SUM | 1 day | 0 | **15** | Simple |
| "Top 3 products this week?" | 1 | 7 | GROUP_BY | 7 days | 1 | **45** | Medium |
| "Revenue trend Feb vs Jan all stores?" | 3 | 60 | SUM + GROUP | 60 days | 2 | **65** | Complex |
| "Cohort analysis by retention + payment method" | 3 | 30 | COHORT+JOIN | 30 days | 3+ | **85** | Very Complex |

**Complexity Impact on Confidence:**
- Simple (0-30): Start at 95% baseline
- Medium (30-60): Start at 80% baseline
- Complex (60-100): Start at 60% baseline, likely needs escalation

---

### Parameter 3: Freshness (15% weight)

**Definition:** Age of data used to answer the query. Newer data = higher confidence.

**Measurement Formula:**
```python
def freshness_score(query_date_requested, data_timestamp):
    """
    Scores freshness based on data age.
    Returns: 0-100

    Example:
      Today: 2026-02-26 10:00 AM
      Query: "What's revenue today (Feb 26)?"
      Data in system: 2026-02-26 08:00 AM (2 hours old)
      freshness_score = 90 (very recent)
    """

    hours_old = (query_date_requested - data_timestamp).total_seconds() / 3600

    if hours_old <= 1:
        return 100  # "Data from this hour"
    elif hours_old <= 4:
        return 95   # "Data from this morning"
    elif hours_old <= 12:
        return 85   # "Data from this shift"
    elif hours_old <= 24:
        return 70   # "Data from yesterday"
    elif hours_old <= 168:  # 1 week
        return 50
    elif hours_old <= 720:  # 1 month
        return 25
    else:
        return 10
```

**Real-World Examples (Lixus POS):**

⚠️ **CRITICAL QUESTION FOR BEN (Week 0):**
> "Is the Lixus POS API real-time or does it batch daily? If batch, at what time?"

**Scenario A: Real-time POS API (Ideal)**
```
Query: "What's revenue for today (Feb 26)?"
Asked at: 2:00 PM
Last transaction in POS: 1:59 PM (1 minute ago)
Freshness: 100 (essentially real-time)
Confidence boosted
```

**Scenario B: Daily batch sync (Realistic)**
```
Query: "What's revenue for today (Feb 26)?"
Asked at: 2:00 PM
Last data sync: 12:00 AM (midnight, 14 hours ago)
Data timestamp: Feb 26 00:00 (14 hours old)
Freshness: 30 (stale for "today" query)
Confidence reduced → Escalate with disclaimer: "As of midnight"
```

**Impact on Answers:**
- If query asks "today" but data is 14+ hours old → **Include disclaimer:** "as of [last sync time]"
- If query asks "last week" and data is 3 days old → Acceptable (weekly data not affected)

---

### Parameter 4: Tool Routing (20% weight)

**Definition:** Did the AI call the correct tool (API endpoint) to answer this query?

**Measurement Formula:**
```python
def tool_routing_score(query, tool_called, correct_tool):
    """
    Scores accuracy of tool selection.
    Returns: 0-100

    Example:
      Query: "What's revenue for Toko Kopi today?"
      Tool called: get_daily_summary(store_001, 2026-02-26) ✅
      Correct tool: get_daily_summary() [or get_transactions() aggregated]
      Score: 100

      Query: "Top 3 products?"
      Tool called: get_employee_performance() ❌ (wrong!)
      Correct tool: get_top_products()
      Score: 0
    """

    if tool_called == correct_tool:
        return 100
    elif is_alternative_tool(tool_called, correct_tool):
        # Tool works but is less efficient
        # Example: Using get_transactions() instead of get_daily_summary()
        return 70
    else:
        return 0  # Wrong tool entirely
```

**Real-World Examples (Using Loyverse tools from WEEK0_DEV_GUIDE.md):**

| Query | Correct Tool | AI Called | Score | Reason |
|-------|--------------|-----------|-------|--------|
| "Revenue for Feb 24?" | get_daily_summary() | get_daily_summary() | **100** | Perfect match |
| "Top selling product?" | get_top_products() | get_daily_summary() + parse top_product | **70** | Works but less efficient |
| "Employee performance?" | get_employee_performance() | get_employee_performance() | **100** | Correct |
| "New customers today?" | get_daily_summary() | get_transactions() + count distinct customers | **70** | Correct data, inefficient tool |
| "Revenue forecast next month?" | ❌ No tool available | get_daily_summary() | **0** | Tool doesn't support forecasting |

**Week 4 Measurement:** For each test query, record:
```json
{
    "query": "Top products this week?",
    "tool_called": "get_top_products(store_001, start_date, limit=10)",
    "tool_correct": true,
    "tool_routing_score": 100,
    "notes": "AI correctly identified this is a ranking query, called right tool"
}
```

---

### Parameter 5: Data Validation (15% weight)

**Definition:** Does the data response contain quality issues (negatives, nulls, inconsistencies) that would break the answer?

**Measurement Formula:**
```python
def data_validation_score(response_data, query_context):
    """
    Checks for data quality issues.
    Returns: 0-100 (higher = fewer issues)

    Each issue reduces score:
    - Negative revenue/quantity: -25 pts
    - Missing critical field (null): -20 pts
    - Date outlier (future date): -20 pts
    - Inconsistency (aggregates don't match): -15 pts
    - Currency mismatch: -10 pts
    """

    score = 100
    issues = []

    # Check 1: Negative values
    for record in response_data:
        if record.get("revenue", 0) < 0:
            score -= 25
            issues.append("Negative revenue detected")
        if record.get("quantity", 0) < 0:
            score -= 25
            issues.append("Negative quantity detected")

    # Check 2: Missing critical fields
    required_fields = get_required_fields(query_context)
    for record in response_data:
        for field in required_fields:
            if record.get(field) is None:
                score -= 20
                issues.append(f"Missing field: {field}")

    # Check 3: Date outliers
    today = date.today()
    for record in response_data:
        record_date = parse_date(record.get("date"))
        if record_date > today:
            score -= 20
            issues.append(f"Future date detected: {record_date}")

    # Check 4: Consistency (aggregates vs. detail)
    agg_revenue = sum([r["revenue"] for r in response_data])
    detail_revenue = calculate_from_transactions(response_data)
    if agg_revenue != detail_revenue:
        score -= 15
        issues.append(f"Inconsistency: Agg={agg_revenue} vs Detail={detail_revenue}")

    # Check 5: Currency consistency
    currencies = set([r.get("currency") for r in response_data])
    if len(currencies) > 1:
        score -= 10
        issues.append("Mixed currencies detected")

    return max(score, 0), issues
```

**Real-World Examples:**

| Data Response | Issues Found | Score | Impact |
|---|---|---|---|
| `daily_summary for Feb 24: revenue=236500, transactions=2` | ✅ None | **100** | Confidence boosted |
| `transaction: revenue=-5000 (refund)` | Negative value | **75** | Acceptable (refunds are valid) |
| `transaction: employee_id=null` | Missing field | **80** | Reduces confidence slightly |
| `daily_summary: Feb 24 + Feb 30 date` | Future date outlier | **80** | Data quality issue noted |
| `daily_summary (Rp 236500) vs transactions sum (Rp 250000)` | Inconsistency | **85** | Major red flag, escalate |

---

### Parameter 6: Reasoning Trace DNC (10% weight) — NEW

**Definition:** Does the AI's internal reasoning (chain-of-thought) align with its final answer? Measures "focus consistency."

**Why It Matters:** Catches cases where the AI found the right answer but got "distracted" during reasoning and changed course (e.g., "I calculated Rp 5M but then noticed a sync error and returned Rp 0 without mentioning it in reasoning").

**Measurement Formula:**
```python
def reasoning_trace_dnc_score(reasoning_trace, final_answer, query):
    """
    Measures coherence between AI's internal reasoning and final output.
    Returns: 0-100 (higher = reasoning supports final answer)
    """

    score = 100

    # Extract key intermediate values from reasoning
    reasoning_values = extract_values(reasoning_trace)
    # Example: {"calc_revenue": 5000000, "detected_contradiction": True}

    final_value = extract_value(final_answer)
    # Example: {"revenue": 0, "reason": "data integrity issue"}

    # Check 1: Does reasoning support final answer?
    if reasoning_path_supports_answer(reasoning_trace, final_answer):
        score = 95  # High coherence
    elif intermediate_values_contradict_final_answer(reasoning_values, final_value):
        score = 30  # AI ignored its own reasoning
    elif "contradiction" in reasoning_trace and "integrity" in final_answer:
        score = 90  # AI found problem, mentioned it, acted on it
    else:
        score = 50  # Unclear reasoning path

    return score
```

**Real-World Examples (Lixus):**

| Query | Reasoning Trace | Final Answer | DNC Score | Why |
|-------|---|---|---|---|
| "What's today's revenue?" | "POS shows Rp 5M... Shopee shows Rp 4.2M... 19% delta exceeds 5% threshold... I should flag this..." | "Data Integrity: POS vs. Shopee delta 19% detected. Cannot provide confident answer." | **95%** | Reasoning led directly to answer; AI stayed focused |
| "Total sales?" | "Daily summary: Rp 3.5M... Wait, I see negative entries... maybe they're refunds? Probably ignore them... My answer is Rp 3.5M." | "Rp 3.5M" | **25%** | Reasoning found anomaly, didn't mention in output; incoherent |
| "Top 3 products?" | "Ranking by quantity: Nasi Padang (120), Es Cendol (95), Rendang (80)..." | "1. Nasi Padang, 2. Es Cendol, 3. Rendang" | **98%** | Perfect coherence |

**Week 4 Measurement:** For each test query, record:
```json
{
    "query": "What's today's revenue?",
    "reasoning_trace": "POS=Rp5M... Shopee=Rp4.2M... delta 16%...",
    "final_answer": "Data Integrity: delta 16% > 5% threshold",
    "dnc_score": 92,
    "notes": "AI's reasoning path directly supported final answer"
}
```

---

## Part 3: Query Type Tiers (Baseline Confidence)

Before calculating the 5 factors, establish **baseline confidence** by query type:

| Tier | Query Type | Examples | Baseline Confidence | Escalation Likelihood |
|------|-----------|----------|---------------------|----------------------|
| **T1: Trivial** | Single metric, single store, single day | "Revenue today?" "New customers?" | **95%** | <5% |
| **T2: Simple** | Single metric, multi-store OR multi-day | "Top products this week?" "Revenue all stores?" | **85%** | 10-15% |
| **T3: Medium** | Multi-metric, multi-dimension (GROUP BY) | "Revenue by payment method?" "Sales by product category?" | **75%** | 25-35% |
| **T4: Complex** | Cross-dimensional analysis (JOINs) | "Trend comparison (Feb vs Jan)?" | **60%** | 40-50% |
| **T5: Very Complex** | Cohort/retention/forecasting | "Retention by customer cohort?" "Forecast March sales?" | **40-50%** | >60% |

**How to Use:**
- **Step 1:** Classify query into T1-T5
- **Step 2:** Calculate 5 factors (Completeness, Complexity, Freshness, Tool Routing, Validation)
- **Step 3:** Apply formula: Final Confidence = Baseline + Adjustments

**Example Calculation:**
```
Query: "Revenue for Toko Kopi yesterday?"
Tier: T1 (Simple) → Baseline: 95%

Factor Scores:
  - Completeness: 100 (revenue field exists)
  - Complexity: 20 (simple query)
  - Freshness: 70 (1 day old)
  - Tool_Routing: 100 (called get_daily_summary correctly)
  - Data_Validation: 100 (no issues)

Final Score = (100×0.30 + 20×0.20 + 70×0.15 + 100×0.20 + 100×0.15)
            = 30 + 4 + 10.5 + 20 + 15
            = 79.5 → Round to 80%

Escalation: 80-95% range → AM reviews before sending
Confidence breakdown shown to AM:
  ✅ Complete data
  ✅ Correct tool called
  ✅ No validation errors
  ⚠️ Data is 1 day old (ask if acceptable for "yesterday" query)
```

---

## Part 4: Week 4 Baseline Testing (Simple Queries)

### Objective
Run 30 simple trained questions (T1-T2 tier only) to establish accuracy baseline and confidence calibration data.

### Test Set Design

**Sample 30 Queries (Using sample-data-loyverse.json):**

```markdown
## Test Set A: Trivial (T1) - 10 Queries

1. "What's revenue for Toko Kopi today (Feb 26)?"
   → Expected: ~Rp 0 (no Feb 26 data; should note data only goes to Feb 25)
   → Correct answer: "Data only available through Feb 25. Last data: Feb 25"

2. "What's revenue for Boutique Jakarta on Feb 24?"
   → Expected: Rp 973,500
   → From: daily_summary, store_002, date=2026-02-24

3. "How many transactions at Toko Kopi yesterday (Feb 25)?"
   → Expected: 0 (no Feb 25 data for store_001)
   → Should note data completeness issue

4. "What's total revenue on Feb 24 across all stores?"
   → Expected: Rp 236,500 + Rp 973,500 + Rp 728,200 = Rp 1,938,200

5. "Top product at Restoran on Feb 24?"
   → Expected: "Nasi Padang Spesial" (from daily_summary top_product field)

6. "New customers at Toko Kopi on Feb 24?"
   → Expected: 1 (from daily_summary new_customers field)

7. "Average transaction value at Boutique on Feb 24?"
   → Expected: Rp 973,500 (only 1 transaction)

8. "Total items sold at Restoran on Feb 24?"
   → Expected: 20 (from daily_summary total_items_sold)

9. "Which store had highest revenue on Feb 24?"
   → Expected: Boutique Jakarta (Rp 973,500)

10. "Payment methods at Toko Kopi on Feb 24?"
    → Expected: cash=Rp 209,000, card=Rp 27,500

## Test Set B: Simple (T2) - 10 Queries

11. "Revenue for last 3 days at Restoran?"
    → Expected: Feb 23: $0, Feb 24: Rp 728,200, Feb 25: Rp 643,500 → Total: Rp 1,371,700
    → Note: Only data from Feb 24-25 available (not Feb 23)

12. "Top 5 products across all stores?"
    → Expected: [Nasi Padang, Rendang Daging, Jeans, Cappuccino, Espresso] (by quantity sold)

13. "Which product generated most revenue?"
    → Expected: Jeans Premium (Rp 450,000 single transaction)

14. "Total customers by store on Feb 24?"
    → Expected: Toko Kopi: 2, Boutique: 1, Restoran: 2

15. "Average transaction value by store?"
    → Expected: Toko Kopi: 118,250, Boutique: 973,500, Restoran: 364,100 (Feb 24 avg)

16. "Revenue trend Toko Kopi Feb 24 vs Feb 25?"
    → Expected: Feb 24: Rp 236,500, Feb 25: Rp 0 (no data)
    → Completeness issue noted

17. "Repeat customers by store on Feb 24?"
    → Expected: Toko Kopi: 1, Boutique: 1, Restoran: 0

18. "Busiest time of day at Restoran Feb 24?"
    → Expected: Lunch (12:30-12:45), 2 transactions

19. "Total loyalty points earned on Feb 24?"
    → Expected: 209+27+973+387+341 = 1,937 points

20. "E-wallet vs cash revenue split?"
    → Expected: e-wallet=Rp 426,000 (341+85), cash=Rp 1,404,700

## Test Set C: Simple-Medium (T2) - 10 Queries

21. "Top 3 products by quantity sold across all stores?"
    → Expected: [Nasi Padang Spesial, Es Cendol, Rendang Daging]

22. "New vs repeat customer breakdown on Feb 24?"
    → Expected: New: 3, Repeat: 2

23. "Revenue contribution by payment method across all stores?"
    → Expected: cash%, card%, e-wallet%

24. "Which employee had most sales on Feb 24?"
    → Expected: emp_004 (Hendra at Restoran, 2 transactions)

25. "Store comparison: Feb 24 performance?"
    → Expected: Revenue rank: Boutique > Restoran > Toko Kopi

26. "Discount given out on Feb 24?"
    → Expected: Total discounts = Rp 35,000

27. "Tax collected on Feb 24?"
    → Expected: 19,000+88,500+35,200 = Rp 142,700

28. "Top customer by revenue on Feb 24?"
    → Expected: "Fashion Influencer" (cust_201, Rp 973,500)

29. "Busiest store by transaction count on Feb 24?"
    → Expected: Restoran (2 tx) tied with Toko Kopi (2 tx)

30. "Revenue per product category on Feb 24?"
    → Expected: Beverages: Rp 190,000, Apparel: Rp 885,000, Main Course: Rp 280,000
```

### Execution Protocol (Week 4, Friday - Mar 7)

**Step 1: Run Queries (Tuesday-Wednesday, Mar 4-5)**
```python
results = []

for test_query in test_set_30:
    # Submit query to Klar agent
    ai_response = klar_agent.query(
        question=test_query["query"],
        store_id=test_query.get("store_id"),
        date_range=test_query.get("date_range")
    )

    # Record full result
    result = {
        "query_id": test_query["id"],
        "query_text": test_query["query"],
        "expected_answer": test_query["expected"],
        "ai_answer": ai_response["answer"],
        "ai_confidence": ai_response["confidence"],  # 0-100
        "actual_correct": (ai_response["answer"] == test_query["expected"]),

        # Record factor scores
        "completeness_score": ai_response.get("factors")["completeness"],
        "complexity_score": ai_response.get("factors")["complexity"],
        "freshness_score": ai_response.get("factors")["freshness"],
        "tool_routing_score": ai_response.get("factors")["tool_routing"],
        "validation_score": ai_response.get("factors")["validation"],

        # Data source for debugging
        "tools_called": ai_response.get("tools_called"),
        "data_used": ai_response.get("data_source"),
        "reasoning": ai_response.get("reasoning"),
    }

    results.append(result)

    # Log immediately for team visibility
    log_result(result)
```

**Step 2: Manual Verification (Thursday, Mar 6)**

For each query, have Nicholas (QA) manually verify:
```markdown
| Query ID | AI Answer | Expected | Match? | Confidence | Notes |
|----------|-----------|----------|--------|-----------|-------|
| Q1 | Rp 0 | Rp 0 | ✅ | 42% | Correctly identified no data available |
| Q2 | Rp 973,500 | Rp 973,500 | ✅ | 98% | Perfect match, high confidence justified |
| Q3 | 0 | 0 | ✅ | 68% | Correct, but completeness issue noted |
| ... | ... | ... | ... | ... | ... |
```

**Step 3: Summary Statistics (Friday, Mar 7)**

Generate Week 4 baseline report:
```markdown
## Week 4 Baseline Results (30 Simple Queries)

Total queries: 30
Correct answers: 29
Incorrect answers: 1
Accuracy: 96.7%

Confidence Scores Distribution:
- 90-100%: 8 queries (avg accuracy: 100%)
- 80-90%: 12 queries (avg accuracy: 100%)
- 70-80%: 7 queries (avg accuracy: 85%)
- 60-70%: 2 queries (avg accuracy: 50%)
- <60%: 1 query (avg accuracy: 0%)

Observations:
✅ High confidence (>85%) → 100% accurate
⚠️ Medium confidence (70-85%) → 95% accurate
❌ Low confidence (<70%) → 75% accurate

Next Step: Calibration in Week 5
```

---

## Part 5: Week 5-6 Confidence Calibration (Two-Step Process)

### Overview: Post-Hoc Calibration + Empirical Threshold Discovery

**Goal:** Fix raw LLM miscalibration (Week 5), then find threshold where accuracy = 99.9% (Week 6)

**Critical Insight from Production Research:**
- Raw Claude confidence is miscalibrated by 10-40 pp (if Claude says 95% confident, actual accuracy is only 75%)
- Post-hoc calibration (isotonic regression) reduces Expected Calibration Error by 23.6 pp (Amazon: 46%, biomedical: 23.6 pp)
- This MUST happen before empirical threshold discovery, or thresholds will be wrong

### Week 5: Post-Hoc Calibration (Isotonic Regression) — CRITICAL FIRST STEP

**Problem to Solve:** Klar's 5-factor formula assigns confidence scores, but raw LLM confidence is miscalibrated

**Solution:** Use Week 4 baseline data (30 queries) to train an isotonic regression function that maps raw confidence → calibrated confidence

**Implementation (Python):**
```python
from sklearn.isotonic import IsotonicRegression
import numpy as np

# Step 1: Load Week 4 baseline data
results = load_week4_results()  # 30 queries with ai_confidence + actual_correct

# Step 2: Prepare data for isotonic regression
raw_confidence = np.array([r["ai_confidence"] / 100.0 for r in results])  # 0-1 scale
actual_accuracy = np.array([1.0 if r["actual_correct"] else 0.0 for r in results])

# Step 3: Fit isotonic regression (monotonic function: raw → calibrated)
isotonic_model = IsotonicRegression(out_of_bounds='clip')
isotonic_model.fit(raw_confidence, actual_accuracy)

# Step 4: Apply to Week 4 data to measure calibration improvement
calibrated_confidence = isotonic_model.predict(raw_confidence)

# Step 5: Calculate Expected Calibration Error (ECE) before and after
ece_before = mean(|raw_confidence - actual_accuracy|)  # Should be 0.10-0.40
ece_after = mean(|calibrated_confidence - actual_accuracy|)  # Should be <0.10

print(f"ECE Before Calibration: {ece_before:.3f}")
print(f"ECE After Calibration: {ece_after:.3f}")
print(f"ECE Reduction: {(ece_before - ece_after):.3f} pp")

# Step 6: Save calibrated model for production
save_isotonic_model(isotonic_model, 'confidence_calibration_model.pkl')
```

**Success Criteria (Week 5):**
- ✅ ECE reduced by at least 15 pp (production target: 23.6 pp reduction)
- ✅ Calibrated confidence distribution matches actual accuracy distribution
- ✅ No systematic bias (calibrated confidence not consistently over/under-confident)

**Expected Result:**
- Before: ECE = 0.25 (raw confidence off by ±25% on average)
- After: ECE = 0.05-0.10 (calibrated confidence off by ±5-10%)

---

### Week 6: Empirical Threshold Discovery (on CALIBRATED Scores) — CRITICAL SECOND STEP

**Goal:** Find the confidence threshold where CALIBRATED accuracy = 99.9% (Julius requirement)

### Empirical Threshold Discovery Methodology

**Process:**

**Process:**
```python
def discover_empirical_threshold():
    """
    Using CALIBRATED confidence scores from Week 5 isotonic regression,
    find the threshold where accuracy = 99.9%
    """

    # Import Week 4 baseline results + CALIBRATED confidence from Week 5
    results = load_week4_results()  # 30 queries with ai_confidence + actual accuracy
    isotonic_model = load_isotonic_model('confidence_calibration_model.pkl')

    # Step 1: Apply isotonic regression to get calibrated confidence
    raw_confidence = np.array([r["ai_confidence"] / 100.0 for r in results])
    calibrated_confidence = isotonic_model.predict(raw_confidence)

    print("EMPIRICAL THRESHOLD DISCOVERY (on Calibrated Scores)")
    print("=" * 70)

    for threshold in np.arange(0.5, 1.01, 0.05):  # 50%, 55%, ..., 100%
        # Filter answers with CALIBRATED confidence at or above this threshold
        answers_above = [
            (i, r) for i, r in enumerate(results)
            if calibrated_confidence[i] >= threshold
        ]

        if len(answers_above) == 0:
            continue

        # Calculate actual accuracy of those answers
        correct_count = sum(1 for _, r in answers_above if r["actual_correct"])
        accuracy = correct_count / len(answers_above) if answers_above else 0
        coverage = len(answers_above) / len(results)

        print(f"Threshold {threshold*100:5.0f}%: {len(answers_above):2d} answers, "
              f"Accuracy: {accuracy*100:5.1f}%, "
              f"Coverage: {coverage*100:5.1f}% ({len(answers_above)}/{len(results)})")

        # Find where accuracy >= 99.9% (or 99% if 99.9% not achievable)
        if accuracy >= 0.999:
            EMPIRICAL_THRESHOLD = threshold * 100
            print(f"\n✅ RESULT: Empirical threshold = {EMPIRICAL_THRESHOLD:.0f}%")
            print(f"   Achieves 99.9% accuracy with {coverage*100:.0f}% coverage")
            return EMPIRICAL_THRESHOLD

    # Fallback: 99% if 99.9% not achievable
    for threshold in np.arange(1.0, 0.49, -0.05):
        answers_above = [
            (i, r) for i, r in enumerate(results)
            if calibrated_confidence[i] >= threshold
        ]
        if len(answers_above) == 0:
            continue
        correct_count = sum(1 for _, r in answers_above if r["actual_correct"])
        accuracy = correct_count / len(answers_above)
        if accuracy >= 0.99:
            return threshold * 100

    return None  # No reasonable threshold found
```

### Expected Output (Example)

```
CONFIDENCE CALIBRATION ANALYSIS
======================================================================
Threshold  50%: 30 answers, Accuracy:  96.7%, Coverage: 30/30
Threshold  55%: 29 answers, Accuracy:  96.6%, Coverage: 29/30
Threshold  60%: 27 answers, Accuracy:  96.3%, Coverage: 27/30
Threshold  65%: 26 answers, Accuracy:  96.2%, Coverage: 26/30
Threshold  70%: 25 answers, Accuracy:  96.0%, Coverage: 25/30
Threshold  75%: 23 answers, Accuracy:  95.7%, Coverage: 23/30
Threshold  80%: 20 answers, Accuracy:  95.0%, Coverage: 20/30
Threshold  85%: 18 answers, Accuracy:  94.4%, Coverage: 18/30
Threshold  90%: 15 answers, Accuracy:  93.3%, Coverage: 15/30
Threshold  95%: 10 answers, Accuracy:  100.0%, Coverage: 10/30 ✅
Threshold 100%: 5 answers, Accuracy: 100.0%, Coverage: 5/30 ✅

RESULT: Calibrated threshold = 95%
  - If AI confidence >= 95%, answer is correct 100% of the time
  - Covers 10/30 queries (33% direct-send rate, 67% need AM review)
  - Achieves 99.9% accuracy requirement on direct-sent answers
```

### Interpretation & Decision Rules

**Once calibrated threshold is found:**

| Confidence Range | Action | Reasoning |
|---|---|---|
| **≥95%** | ✅ Send directly to client | 99.9% accurate (no AM review needed) |
| **80-95%** | 🟡 AM reviews first | 95%+ accurate, but not 99.9% yet (AM as safety net) |
| **60-80%** | 🔴 Escalate to engineer | ~85% accurate (too risky) |
| **<60%** | 🔴 REJECT, ask for clarification | <80% accurate (Julius would reject) |

### Adjustments by Query Type (T1-T5)

Different query types may need **different thresholds**:

```markdown
## Fine-Tuned Thresholds by Query Type

T1 (Trivial):
  - Calibrated from: 10 T1 queries from Week 4
  - If threshold needed: 90% (trivial queries more predictable)
  - Direct-send at: ≥90% confidence

T2 (Simple):
  - Calibrated from: 10 T2 queries from Week 4
  - If threshold needed: 95% (simple queries need higher bar)
  - Direct-send at: ≥95% confidence

T3+ (Medium+):
  - **All escalate for AM review or engineer**
  - Threshold: >95% (very few meet this bar)
  - Examples: trend comparisons, cohort analysis
```

---

## Part 6: Implementation Rules (Weeks 7+)

### Confidence Scoring in Production

Every answer Klar returns includes:

```json
{
  "answer": "Revenue for Toko Kopi on Feb 24: Rp 236,500",
  "confidence_score": 96,
  "confidence_band": "HIGH",
  "recommendation": "SEND_TO_CLIENT",

  "factors_breakdown": {
    "completeness": 100,
    "complexity": 15,
    "freshness": 85,
    "tool_routing": 100,
    "validation": 100
  },

  "reasoning": [
    "✅ All required data fields available",
    "✅ Simple query (1 store, 1 date)",
    "⚠️  Data is ~1-2 hours old",
    "✅ Correct tool called (get_daily_summary)",
    "✅ No data quality issues detected"
  ],

  "data_source": "Loyverse POS API, daily_summary table",
  "data_timestamp": "2026-02-24T23:59:59Z",
  "tools_called": ["get_daily_summary(store_001, 2026-02-24)"],
}
```

### AM Decision Flow

```
Query from Lixus AM:
  "What's revenue for Toko Kopi today?"
         ↓
    Klar returns answer with confidence=96%
         ↓
    Decision Box:
    ├─ Confidence >= 95%?
    │  └─ YES → "SEND_TO_CLIENT" button active
    │          "Review First" button available (optional)
    │
    ├─ Confidence 80-95%?
    │  └─ YES → "Review First" button active (default)
    │          "Send to Client" available (with warning)
    │
    └─ Confidence < 80%?
       └─ YES → "Escalate" button only
                "Escalate to Engineer" mandatory
                Explanation: "This query needs manual review"
         ↓
    AM clicks "Send to Client"
    Query sent to Lixus client with confidence shown
```

---

## Part 7: Escalation Rules & Response Handling

### When to Escalate (and Why)

| Scenario | Confidence | Action | Escalation To | Reason |
|----------|-----------|--------|----------------|--------|
| Q1: "Revenue today?" Data complete | 96% | ✅ Send | Client | High confidence, simple query |
| Q2: "Revenue today?" Data 18hrs old | 72% | 🟡 Review | AM | Freshness issue, uncertain if acceptable |
| Q3: "Cohort retention analysis?" | 45% | 🔴 Escalate | Engineer | Complex query, low confidence |
| Q4: "Revenue for Feb 31?" | 0% | 🔴 Reject | AM | Invalid date, nonsensical query |
| Q5: "Employee performance?" PII concern | 85% | 🔴 Escalate | AM + Engineer | PII guardrail triggered |

### Escalation Task Template (ClickUp)

When escalating, auto-create ClickUp task:

```markdown
## Escalation Task Template

Title: "[ESCALATE] {query summary} - Confidence {score}%"

Priority:
  - Confidence < 80%: HIGH
  - Confidence 80-95%: MEDIUM
  - Confidence > 95%: LOW (shouldn't happen)

Description:
```
Original Query: [query text]
AM: [who asked]
Date: [when]

AI Response:
- Answer: [what AI said]
- Confidence: [score]%
- Reason for escalation: [which factor failed]

Factors:
- Completeness: [score]
- Complexity: [score]
- Freshness: [score]
- Tool Routing: [score]
- Validation: [score]

Data Used: [which API, which fields]

What We Need:
- [ ] Verify if answer is actually correct
- [ ] Suggest improvement to prompt/tools
- [ ] Document edge case for future training
```

---

## Part 8: Weekly Confidence Tracking (Week 7+)

### Weekly Metrics Dashboard

**Track & report every Friday:**

```markdown
## Klar Confidence Score Metrics (Week of {date})

### Volume Metrics
- Total queries: 150
- Direct-send (≥95%): 45 (30%)
- AM review (80-95%): 75 (50%)
- Escalated (<80%): 30 (20%)

### Accuracy Metrics
- Direct-send accuracy: 100% (45/45) ✅
- AM review accuracy: 98.7% (74/75)
- Escalated accuracy: 73% (22/30)
- Overall accuracy: 95.3% (141/150)

### Confidence Calibration Health
- Average confidence score: 87%
- Std dev: 12%
- Range: 25%-100%

### Problem Queries (< 80% confidence)
Top reasons for escalation:
1. Data freshness (40%): "Today's data not ready yet"
2. Missing fields (30%): "Customer segment data not available"
3. Complex query (20%): "Retention analysis requires joins"
4. Data validation (10%): "Revenue total doesn't match transactions"

### Trends
- Confidence improving? [Yes/No]
- Accuracy improving? [Yes/No]
- Escalation rate trending? [Up/Down/Stable]
```

---

## Part 9: Appendix - Example Calculations

### Full Example 1: Simple Query (Should be 95%+ confident)

```
QUERY: "What's revenue for Toko Kopi on Feb 24?"

Step 1: Classify Query Type
  → T1 (Trivial) = Baseline confidence 95%

Step 2: Calculate 5 Factors

  A. Completeness Score
     Required fields: [store_id, date, revenue]
     Available: [✅ store_id, ✅ date, ✅ revenue]
     Score: 100

  B. Complexity Score
     - Entities (1 store): +5
     - Aggregation (SUM): +10
     - Time period (1 day): +5
     - Filters (0): +0
     Score: 20

  C. Freshness Score
     - Query date: 2026-02-26
     - Data date: 2026-02-24 (2 days ago)
     - Score: 70 (data is 2 days old)

  D. Tool Routing Score
     - Query type: Revenue for specific store + date
     - Tool called: get_daily_summary(store_001, 2026-02-24)
     - Correct?: ✅ YES
     - Score: 100

  E. Data Validation Score
     - Negative values?: ✅ None
     - Missing fields?: ✅ None
     - Date outliers?: ✅ None
     - Consistency?: ✅ Daily_summary matches transactions (236500)
     - Currency?: ✅ All IDR
     - Score: 100

Step 3: Apply Formula
  Confidence = (Completeness×0.30 + Complexity×0.20 + Freshness×0.15
                + Tool_Routing×0.20 + Validation×0.15)
             = (100×0.30 + 20×0.20 + 70×0.15 + 100×0.20 + 100×0.15)
             = 30 + 4 + 10.5 + 20 + 15
             = 79.5 → Round to 80%

⚠️ NOTE: Expected 95%, got 80% because freshness reduced confidence.

Step 4: Evaluate
  - Confidence: 80%
  - Decision: 80-95% range → AM Reviews First
  - Why confidence is lower: Data is 2 days old
  - Recommendation: Include timestamp: "As of Feb 24 end-of-day"
```

### Full Example 2: Complex Query (Should escalate)

```
QUERY: "Show me retention cohorts by customer acquisition date
        with revenue trend per cohort for all stores this month"

Step 1: Classify Query Type
  → T4 (Complex) = Baseline confidence 60%

Step 2: Calculate 5 Factors

  A. Completeness Score
     Required: [store_id, customer_id, acquisition_date, cohort, revenue, date]
     Available: [✅ store_id, ✅ customer_id, ❌ acquisition_date (not in data),
                 ❌ cohort (not calculated), ✅ revenue, ✅ date]
     Score: 50 (4/6 fields available)

  B. Complexity Score
     - Entities (3 stores): +25
     - Aggregation (COHORT + JOIN): +35
     - Time period (30 days): +30
     - Filters (2): +20
     Score: 110 → Capped at 100

  C. Freshness Score
     - Data through Feb 25, query for "this month" (through Feb 28)
     - Missing 3 days of data
     - Score: 40

  D. Tool Routing Score
     - Query requires: Cohort analysis (no tool available)
     - Best alternative: get_transactions() + manual aggregation
     - Score: 40 (can work, but suboptimal)

  E. Data Validation Score
     - Cohort calculation requires joins (not in available data)
     - Score: 50

Step 3: Apply Formula
  Confidence = (50×0.30 + 100×0.20 + 40×0.15 + 40×0.20 + 50×0.15)
             = 15 + 20 + 6 + 8 + 7.5
             = 56.5 → Round to 57%

Step 4: Evaluate
  - Confidence: 57%
  - Decision: <80% → ESCALATE
  - Reason: Complex query + missing data + no direct tool
  - Escalation message: "This analysis requires engineer review due to:
    1. Data completeness (only 75% of required fields)
    2. Query complexity (cohort analysis not automated)
    3. Data freshness (3 days missing from current month)

    Estimated turnaround: 3-4 hours for engineer to build custom aggregation"
```

---

## Summary & Quick Reference

### For Week 4 (Testing)
1. Run 30 simple test queries against sample data
2. Record: query, expected answer, AI answer, AI confidence, actual correctness
3. Generate accuracy baseline report

### For Week 5-6 (Calibration)
1. Analyze Week 4 results
2. For each confidence threshold (50%, 55%, ..., 100%), calculate actual accuracy
3. **Find threshold where accuracy = 99.9%** (likely 90-95%)
4. Set that as **calibrated threshold for direct-to-client send**

### For Week 7+ (Production)
1. Every answer includes confidence score + reasoning breakdown
2. **Confidence ≥ threshold** → "Send to Client" recommended
3. **Confidence < threshold** → "Review First" or "Escalate" required
4. Track weekly metrics (accuracy, escalation rate, confidence trends)

### Key Formulas
```
Confidence Score = (
    Completeness × 0.30 +
    Complexity × 0.20 +
    Freshness × 0.15 +
    Tool_Routing × 0.20 +
    Data_Validation × 0.15
)

Escalation Rule:
  IF confidence >= CALIBRATED_THRESHOLD → Send directly
  ELSE IF 80% <= confidence < CALIBRATED_THRESHOLD → AM reviews
  ELSE → Escalate to engineer
```

---

## Owners & Timeline

| Phase | Owner | Timeline | Deliverable |
|-------|-------|----------|-------------|
| Week 4 | Nicholas (QA) | Mar 4-7 | 30 test queries + accuracy baseline |
| Week 5 | Nicholas + Adrian | Mar 10-14 | Calibration analysis + threshold decision |
| Week 6 | Adrian (AI) | Mar 17-21 | Implement confidence scoring in production |
| Week 7+ | All | Ongoing | Weekly confidence metrics + monitoring |

---

**Last Updated:** 28 Feb 2026
**Next:** Implement in Week 0 (Stream C: Confidence Scoring Framework)
**Questions?** Ask Nicholas or review CLAUDE.md Part 2, Challenge #2 (Accuracy Bar)
