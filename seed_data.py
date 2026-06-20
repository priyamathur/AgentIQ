"""
seed_data.py — 500 demo sessions for AgentIQ dashboard.

Constraints:
  - All 7 failure types present
  - Billing disputes account for >40% of all failures
  - Data spread over last 7 days so the trend chart has content
  - Realistic pass/fail score distributions

Run: python3 seed_data.py
"""
import json
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

AGENT_ID = "demo-agent"
SEED = 42
WEIGHTS = {"accuracy": 0.35, "goal_alignment": 0.35, "decision_quality": 0.15, "completeness": 0.15}
PASS_THRESHOLD = 0.7

random.seed(SEED)

# ---------------------------------------------------------------------------
# Step and scenario definitions
# ---------------------------------------------------------------------------

@dataclass
class StepTemplate:
    name: str
    input_text: str
    output_pass: str
    fail_prob: float
    failure_type: str
    failure_output: str
    failure_reason: str
    failure_step: int


@dataclass
class Scenario:
    name: str
    session_count: int
    steps: List[StepTemplate]


SCENARIOS: List[Scenario] = [
    # ── Billing dispute ─────────────────────────────────────────────────────
    # Accounts for ~55-60% of all failures (well above the 40% target)
    Scenario("billing_dispute", 200, [
        StepTemplate(
            name="classify_intent",
            input_text="I was charged twice for my order last Tuesday.",
            output_pass="Intent identified: billing dispute. Routing to billing workflow.",
            fail_prob=0.02,
            failure_type="wrong_answer",
            failure_output="Intent identified: order status inquiry. Routing to order tracking.",
            failure_reason="Agent misclassified a billing dispute as an order status request.",
            failure_step=1,
        ),
        StepTemplate(
            name="query_billing_api",
            input_text="Retrieve transaction history for customer account.",
            output_pass="Retrieved 3 transactions. Duplicate charge of $49.99 confirmed on 2026-06-10.",
            fail_prob=0.35,
            failure_type="tool_failure",
            failure_output="Error: Billing API returned 503 Service Unavailable.",
            failure_reason="Billing API returned 503 at step 2; agent could not retrieve transaction history.",
            failure_step=2,
        ),
        StepTemplate(
            name="apply_dispute_policy",
            input_text="Apply refund policy for confirmed duplicate charge.",
            output_pass="Refund of $49.99 initiated under duplicate charge policy. Confirmation sent.",
            fail_prob=0.20,
            failure_type="wrong_answer",
            failure_output="Applied 7-day return window policy. Refund denied as purchase exceeds window.",
            failure_reason="Agent applied product return policy instead of duplicate charge policy at step 3.",
            failure_step=3,
        ),
    ]),

    # ── Order status ────────────────────────────────────────────────────────
    Scenario("order_status", 100, [
        StepTemplate(
            name="parse_order_id",
            input_text="Where is my order #ORD-88421?",
            output_pass="Order ID ORD-88421 parsed. Querying order system.",
            fail_prob=0.02,
            failure_type="wrong_answer",
            failure_output="No order ID detected in user message.",
            failure_reason="Agent failed to extract order ID from a clearly formatted request.",
            failure_step=1,
        ),
        StepTemplate(
            name="query_order_system",
            input_text="Fetch order details for ORD-88421.",
            output_pass="Order ORD-88421: shipped 2026-06-13, estimated delivery 2026-06-17.",
            fail_prob=0.10,
            failure_type="tool_failure",
            failure_output="Error: Order system request timed out after 5s.",
            failure_reason="Order system timed out at step 2; no delivery estimate could be provided.",
            failure_step=2,
        ),
        StepTemplate(
            name="format_status_response",
            input_text="Summarize order status for customer.",
            output_pass="Your order shipped on June 13 and arrives by June 17.",
            fail_prob=0.05,
            failure_type="incomplete",
            failure_output="Your order has shipped.",
            failure_reason="Response omitted the estimated delivery date the customer needs.",
            failure_step=3,
        ),
    ]),

    # ── Refund request ──────────────────────────────────────────────────────
    Scenario("refund_request", 80, [
        StepTemplate(
            name="verify_purchase",
            input_text="I want a refund on my headphones purchased June 1.",
            output_pass="Purchase verified: Sony WH-1000XM5, $349, purchased 2026-06-01.",
            fail_prob=0.03,
            failure_type="wrong_answer",
            failure_output="No purchase found for headphones in the past 30 days.",
            failure_reason="Agent searched wrong customer account due to a session context error.",
            failure_step=1,
        ),
        StepTemplate(
            name="check_refund_eligibility",
            input_text="Check if purchase is within refund window.",
            output_pass="Purchase is within 30-day refund window. Eligible.",
            fail_prob=0.12,
            failure_type="wrong_answer",
            failure_output="Purchase exceeds 15-day refund window. Not eligible.",
            failure_reason="Agent applied 15-day electronics window instead of 30-day standard window.",
            failure_step=2,
        ),
        StepTemplate(
            name="calculate_refund_amount",
            input_text="Calculate refund amount including restocking fee.",
            output_pass="Refund amount: $314.10 (after 10% restocking fee on $349).",
            fail_prob=0.08,
            failure_type="wrong_answer",
            failure_output="Refund amount: $349.00 (full refund).",
            failure_reason="Agent issued full refund without applying the required 10% restocking fee.",
            failure_step=3,
        ),
        StepTemplate(
            name="confirm_refund",
            input_text="Process refund and notify customer.",
            output_pass="Refund of $314.10 processed. Confirmation email sent to customer.",
            fail_prob=0.06,
            failure_type="incomplete",
            failure_output="Refund processed successfully.",
            failure_reason="Refund was processed but confirmation email was not sent to the customer.",
            failure_step=4,
        ),
    ]),

    # ── Product inquiry ─────────────────────────────────────────────────────
    Scenario("product_inquiry", 70, [
        StepTemplate(
            name="search_product_catalog",
            input_text="What are the specs for the Sony WH-1000XM5?",
            output_pass="Found Sony WH-1000XM5: 30h battery, ANC, Bluetooth 5.2, $349.",
            fail_prob=0.03,
            failure_type="tool_failure",
            failure_output="Product search returned no results.",
            failure_reason="Catalog search returned zero results for a product that exists in inventory.",
            failure_step=1,
        ),
        StepTemplate(
            name="generate_product_response",
            input_text="Describe product features for customer.",
            output_pass="The Sony WH-1000XM5 offers 30 hours of battery, active noise cancellation, and Bluetooth 5.2 for $349.",
            fail_prob=0.10,
            failure_type="hallucination",
            failure_output="The Sony WH-1000XM5 offers 60 hours of battery, 4K audio, and built-in translation for $299.",
            failure_reason="Agent cited 60-hour battery and 4K audio — neither feature exists on this product.",
            failure_step=2,
        ),
    ]),

    # ── Account management ──────────────────────────────────────────────────
    Scenario("account_management", 50, [
        StepTemplate(
            name="authenticate_user",
            input_text="Update my email address to new@example.com.",
            output_pass="User authenticated. Proceeding to account update.",
            fail_prob=0.02,
            failure_type="wrong_answer",
            failure_output="Authentication failed. Please try again.",
            failure_reason="Agent rejected a valid authentication token due to a format mismatch.",
            failure_step=1,
        ),
        StepTemplate(
            name="load_account_context",
            input_text="Load current account details.",
            output_pass="Account loaded: email old@example.com, plan Premium, since 2024-01.",
            fail_prob=0.15,
            failure_type="context_loss",
            failure_output="Account details unavailable. Please re-authenticate.",
            failure_reason="Agent lost account context between authentication and the account load step.",
            failure_step=2,
        ),
        StepTemplate(
            name="apply_account_changes",
            input_text="Update email to new@example.com.",
            output_pass="Email updated to new@example.com. Change confirmed.",
            fail_prob=0.06,
            failure_type="incomplete",
            failure_output="Email update initiated.",
            failure_reason="Agent initiated the email change but did not confirm it was persisted.",
            failure_step=3,
        ),
    ]),
]

# ── Rare failure types injected to ensure all 7 are present ─────────────────
_RARE_INJECTIONS: List[Tuple[str, str, str]] = [
    (
        "goal_drift",
        "Agent began explaining general billing policies instead of resolving the specific duplicate charge.",
        "Agent drifted from resolving the duplicate charge to explaining unrelated billing terms at step 2.",
    ),
    (
        "loop",
        "Agent repeatedly asked for the order number the customer had already provided three times.",
        "Agent looped on requesting order confirmation already provided by the customer at step 1.",
    ),
]
_RARE_INJECTION_COUNT = 8  # per type — ensures ≥5 so patterns are detected


# ---------------------------------------------------------------------------
# Score generation
# ---------------------------------------------------------------------------

def _passed_scores() -> Dict[str, Any]:
    a = random.uniform(0.75, 0.99)
    g = random.uniform(0.75, 0.99)
    d = random.uniform(0.72, 0.96)
    c = random.uniform(0.75, 0.99)
    overall = (a * WEIGHTS["accuracy"] + g * WEIGHTS["goal_alignment"]
               + d * WEIGHTS["decision_quality"] + c * WEIGHTS["completeness"])
    return {"accuracy": round(a, 3), "goal_alignment": round(g, 3),
            "decision_quality": round(d, 3), "completeness": round(c, 3),
            "overall_score": round(overall, 3), "passed": True}


def _failed_scores(failure_type: str) -> Dict[str, Any]:
    a, g, d, c = (random.uniform(0.75, 0.90) for _ in range(4))
    if failure_type in ("wrong_answer", "hallucination"):
        a = random.uniform(0.15, 0.45)
        g = random.uniform(0.30, 0.55)
    elif failure_type == "tool_failure":
        d = random.uniform(0.15, 0.45)
        c = random.uniform(0.15, 0.40)
    elif failure_type == "goal_drift":
        g = random.uniform(0.15, 0.40)
    elif failure_type == "incomplete":
        c = random.uniform(0.10, 0.40)
    elif failure_type == "context_loss":
        a = random.uniform(0.20, 0.45)
        g = random.uniform(0.25, 0.50)
    elif failure_type == "loop":
        d = random.uniform(0.10, 0.35)
        c = random.uniform(0.10, 0.30)
    overall = (a * WEIGHTS["accuracy"] + g * WEIGHTS["goal_alignment"]
               + d * WEIGHTS["decision_quality"] + c * WEIGHTS["completeness"])
    overall = min(overall, PASS_THRESHOLD - 0.01)
    return {"accuracy": round(a, 3), "goal_alignment": round(g, 3),
            "decision_quality": round(d, 3), "completeness": round(c, 3),
            "overall_score": round(overall, 3), "passed": False}


# ---------------------------------------------------------------------------
# Row builders
# ---------------------------------------------------------------------------

def _make_log(session_id: str, step: StepTemplate, output: str, ts: datetime) -> Dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "agent_id": AGENT_ID,
        "session_id": session_id,
        "step_number": step.failure_step,
        "step_name": step.name,
        "input": step.input_text,
        "output": output,
        "tool_calls": None,
        "latency_ms": random.randint(120, 1800),
        "session_ended": False,
        "timestamp": ts,
        "step_metadata": None,
    }


def _make_eval(
    log_id: str,
    session_id: str,
    scores: Dict[str, Any],
    failure_type: Optional[str],
    failure_step: Optional[int],
    failure_reason: Optional[str],
    ts: datetime,
) -> Dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "log_id": log_id,
        "session_id": session_id,
        "agent_id": AGENT_ID,
        "accuracy": scores["accuracy"],
        "goal_alignment": scores["goal_alignment"],
        "decision_quality": scores["decision_quality"],
        "completeness": scores["completeness"],
        "overall_score": scores["overall_score"],
        "passed": scores["passed"],
        "failure_type": failure_type,
        "failure_step": failure_step,
        "failure_reason": failure_reason,
        "confidence": round(random.uniform(0.75, 0.97), 3),
        "eval_error": False,
        "evaluated_at": ts + timedelta(seconds=random.randint(5, 30)),
    }


# ---------------------------------------------------------------------------
# Session generation
# ---------------------------------------------------------------------------

def _random_ts(day_offset: int) -> datetime:
    base = datetime.now(timezone.utc) - timedelta(days=day_offset)
    return base.replace(
        hour=random.randint(6, 23),
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
        microsecond=0,
    )


def _generate_sessions(scenario: Scenario) -> Tuple[List[Dict], List[Dict]]:
    logs: List[Dict] = []
    evals: List[Dict] = []
    day_pool = (list(range(0, 7)) * (scenario.session_count // 7 + 2))[: scenario.session_count]

    for i, day in enumerate(day_pool):
        session_id = f"{scenario.name}-{str(uuid.uuid4())[:8]}"
        session_ts = _random_ts(day)

        for step in scenario.steps:
            step_ts = session_ts + timedelta(seconds=step.failure_step * random.randint(3, 15))
            failed = random.random() < step.fail_prob

            log = _make_log(session_id, step, step.failure_output if failed else step.output_pass, step_ts)
            logs.append(log)

            scores = _failed_scores(step.failure_type) if failed else _passed_scores()
            evals.append(_make_eval(
                log_id=log["id"],
                session_id=session_id,
                scores=scores,
                failure_type=step.failure_type if failed else None,
                failure_step=step.failure_step if failed else None,
                failure_reason=step.failure_reason if failed else None,
                ts=step_ts,
            ))

    return logs, evals


def _generate_rare_injections() -> Tuple[List[Dict], List[Dict]]:
    """Inject goal_drift and loop failures so all 7 types are present."""
    logs: List[Dict] = []
    evals: List[Dict] = []
    billing = next(s for s in SCENARIOS if s.name == "billing_dispute")
    step = billing.steps[1]  # query_billing_api

    for failure_type, failure_output, failure_reason in _RARE_INJECTIONS:
        for _ in range(_RARE_INJECTION_COUNT):
            session_id = f"billing_rare-{failure_type[:4]}-{str(uuid.uuid4())[:6]}"
            ts = _random_ts(random.randint(0, 6))

            log = _make_log(session_id, step, failure_output, ts)
            log["step_number"] = 2
            logs.append(log)

            scores = _failed_scores(failure_type)
            evals.append(_make_eval(
                log_id=log["id"],
                session_id=session_id,
                scores=scores,
                failure_type=failure_type,
                failure_step=2,
                failure_reason=failure_reason,
                ts=ts,
            ))

    return logs, evals


# ---------------------------------------------------------------------------
# DB write
# ---------------------------------------------------------------------------

def _bulk_write(db: Any, logs: List[Dict], evals: List[Dict]) -> None:
    from db.models import AgentLog, EvalResult
    CHUNK = 250
    for i in range(0, len(logs), CHUNK):
        db.bulk_insert_mappings(AgentLog, logs[i: i + CHUNK])
    for i in range(0, len(evals), CHUNK):
        db.bulk_insert_mappings(EvalResult, evals[i: i + CHUNK])
    db.commit()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("AgentIQ seed — initialising database …", flush=True)
    from api.database import SessionLocal, engine
    from db.models import Base

    Base.metadata.create_all(bind=engine)
    print("  Tables verified.", flush=True)

    all_logs: List[Dict] = []
    all_evals: List[Dict] = []

    for scenario in SCENARIOS:
        logs, evals = _generate_sessions(scenario)
        all_logs.extend(logs)
        all_evals.extend(evals)
        failed = sum(1 for e in evals if not e["passed"])
        print(f"  {scenario.name:25s} {scenario.session_count} sessions  "
              f"{len(logs)} steps  {failed} failures", flush=True)

    rare_logs, rare_evals = _generate_rare_injections()
    all_logs.extend(rare_logs)
    all_evals.extend(rare_evals)
    print(f"  {'rare injections':25s} —          "
          f"{len(rare_logs)} steps  {len(rare_evals)} failures", flush=True)

    db = SessionLocal()
    try:
        _bulk_write(db, all_logs, all_evals)
    finally:
        db.close()

    # ── Summary ──────────────────────────────────────────────────────────────
    total_steps = len(all_logs)
    total_failures = sum(1 for e in all_evals if not e["passed"])
    billing_failures = sum(
        1 for e in all_evals
        if not e["passed"] and e["session_id"].startswith("billing")
    )
    billing_pct = billing_failures / max(total_failures, 1) * 100

    print(f"\n  Total steps:      {total_steps}")
    print(f"  Total evals:      {len(all_evals)}")
    print(f"  Total failures:   {total_failures}  ({total_failures / len(all_evals) * 100:.1f}%)")
    print(f"  Billing failures: {billing_failures}  ({billing_pct:.1f}% of all failures)", end="")
    print("  ✓" if billing_pct > 40 else "  ✗ BELOW TARGET")

    failure_types_present = {e["failure_type"] for e in all_evals if e["failure_type"]}
    all_seven = {"wrong_answer", "tool_failure", "goal_drift", "incomplete",
                 "hallucination", "context_loss", "loop"}
    missing = all_seven - failure_types_present
    print(f"  Failure types:    {sorted(failure_types_present)}")
    print(f"  All 7 present:    {'✓' if not missing else f'✗ missing {missing}'}")

    # ── Run pattern analyzer ─────────────────────────────────────────────────
    print("\nRunning pattern analysis …", flush=True)
    from agentiq.analyzer import run_analysis
    db = SessionLocal()
    try:
        n = run_analysis(AGENT_ID, db)
    finally:
        db.close()
    print(f"  LossPattern rows written: {n}", flush=True)

    print("\nDone. Launch the dashboard:")
    print("  streamlit run agentiq/dashboard.py --server.port 8501")


if __name__ == "__main__":
    main()
