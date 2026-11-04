
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Bank Fraud Architecture Simulator",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 Bank Fraud–Rule Processing Architecture Simulator")
st.caption(
    "Computer Architecture Mini Project | Logic • ALU • CPU Cycle • Pipeline • Cache"
)

# -------------------- SESSION STATE --------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "cache" not in st.session_state:
    st.session_state.cache = {}
if "cycle_log" not in st.session_state:
    st.session_state.cycle_log = []
if "next_id" not in st.session_state:
    st.session_state.next_id = 1

# -------------------- SIDEBAR --------------------
st.sidebar.header("⚙️ Fraud Rule Settings")

large_limit = st.sidebar.number_input(
    "Large transaction threshold (NPR)",
    min_value=1000, value=50000, step=5000
)
rapid_limit = st.sidebar.number_input(
    "Rapid transaction count threshold",
    min_value=2, value=5, step=1
)
pin_limit = st.sidebar.number_input(
    "Failed PIN attempt threshold",
    min_value=1, value=3, step=1
)
risk_limit = st.sidebar.slider(
    "Flag for review at risk score",
    min_value=1, max_value=10, value=4
)

use_cache = st.sidebar.checkbox("Enable rule cache", value=True)
use_pipeline = st.sidebar.checkbox(
    "Enable pipeline timing simulation", value=True
)

# -------------------- TRANSACTION INPUT --------------------
st.header("1. Enter Banking Transaction")

with st.form("transaction_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        amount = st.number_input(
            "Transaction amount (NPR)",
            min_value=0.0, value=10000.0, step=1000.0
        )
        balance = st.number_input(
            "Available account balance (NPR)",
            min_value=0.0, value=100000.0, step=5000.0
        )

    with col2:
        frequency = st.number_input(
            "Transactions in last 10 minutes",
            min_value=1, value=1, step=1
        )
        failed_pins = st.number_input(
            "Failed PIN attempts",
            min_value=0, value=0, step=1
        )

    with col3:
        foreign = st.checkbox("Unusual / foreign location")
        new_device = st.checkbox("Unrecognized device")

    submitted = st.form_submit_button(
        "▶ Process Transaction", type="primary"
    )

# -------------------- PROCESSOR --------------------
def process_transaction(tx, settings, cache, cache_enabled):
    log = []
    results = {}
    risk = 0
    alu_ops = 0
    logic_ops = 0
    cache_hits = 0
    cache_misses = 0
    rules = [
        ("R1", "Large transaction"),
        ("R2", "Rapid repeated transactions"),
        ("R3", "Insufficient balance"),
        ("R4", "Failed PIN attempts"),
        ("R5", "Unusual location"),
        ("R6", "Unrecognized device"),
    ]

    conditions = {
        "R1": tx["amount"] >= settings["large_limit"],
        "R2": tx["frequency"] >= settings["rapid_limit"],
        "R3": tx["amount"] > tx["balance"],
        "R4": tx["failed_pins"] >= settings["pin_limit"],
        "R5": tx["foreign"],
        "R6": tx["new_device"],
    }

    # Fetch, Decode, Execute, Write Back
    for rule_id, description in rules:
        instruction = f"{rule_id}:{description}"
        log.append({
            "Cycle": len(log) + 1,
            "Stage": "FETCH",
            "Instruction": instruction,
            "Result": "Instruction loaded"
        })
        log.append({
            "Cycle": len(log) + 1,
            "Stage": "DECODE",
            "Instruction": instruction,
            "Result": "Identify rule operation"
        })

        key = (rule_id, settings["large_limit"],
               settings["rapid_limit"], settings["pin_limit"],
               tx["amount"], tx["balance"], tx["frequency"],
               tx["failed_pins"], tx["foreign"], tx["new_device"])

        if cache_enabled and key in cache:
            triggered = cache[key]
            cache_hits += 1
            source = "Cache hit"
        else:
            # Arithmetic and logical evaluation
            if rule_id == "R1":
                alu_ops += 1
            elif rule_id == "R2":
                alu_ops += 1
            elif rule_id == "R3":
                alu_ops += 1
            elif rule_id == "R4":
                alu_ops += 1
            else:
                logic_ops += 1

            triggered = conditions[rule_id]
            cache_misses += 1
            source = "Rule evaluated"
            if cache_enabled:
                cache[key] = triggered

        results[rule_id] = triggered
        if triggered:
            risk += 2 if rule_id in ("R3", "R4") else 1

        log.append({
            "Cycle": len(log) + 1,
            "Stage": "EXECUTE",
            "Instruction": instruction,
            "Result": f"{triggered} ({source})"
        })
        log.append({
            "Cycle": len(log) + 1,
            "Stage": "WRITE BACK",
            "Instruction": instruction,
            "Result": "Risk score updated"
        })

    # Demonstrate ALU arithmetic
    remaining = tx["balance"] - tx["amount"]
    alu_ops += 1

    if risk >= settings["risk_limit"]:
        decision = "FLAG FOR REVIEW"
    elif results["R3"] or results["R4"]:
        decision = "REJECT"
    else:
        decision = "APPROVE"

    # Simple illustrative timing model, not real CPU benchmark data
    instruction_count = len(rules) * 4
    sequential_cycles = instruction_count * 4
    pipeline_cycles = instruction_count + 3 if use_pipeline_global else sequential_cycles

    return {
        "results": results,
        "risk": risk,
        "decision": decision,
        "remaining": remaining,
        "alu_ops": alu_ops,
        "logic_ops": logic_ops,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "log": log,
        "instruction_count": instruction_count,
        "sequential_cycles": sequential_cycles,
        "pipeline_cycles": pipeline_cycles,
    }

# -------------------- EXECUTION --------------------
if submitted:
    tx = {
        "id": st.session_state.next_id,
        "amount": amount,
        "balance": balance,
        "frequency": frequency,
        "failed_pins": failed_pins,
        "foreign": foreign,
        "new_device": new_device,
    }

    settings = {
        "large_limit": large_limit,
        "rapid_limit": rapid_limit,
        "pin_limit": pin_limit,
        "risk_limit": risk_limit,
    }

    # Use the pipeline setting selected by the user
    use_pipeline_global = use_pipeline

    output = process_transaction(
        tx, settings, st.session_state.cache, use_cache
    )

    st.session_state.cycle_log = output["log"]
    st.session_state.history.append({
        "ID": tx["id"],
        "Amount (NPR)": tx["amount"],
        "Risk Score": output["risk"],
        "Decision": output["decision"],
        "Rules Triggered": sum(output["results"].values()),
        "Remaining Balance (NPR)": output["remaining"],
    })
    st.session_state.next_id += 1

    st.header("2. Processor Output")

    a, b, c, d = st.columns(4)
    a.metric("Risk Score", output["risk"])
    b.metric("Triggered Rules", sum(output["results"].values()))
    c.metric("ALU Operations", output["alu_ops"])
    d.metric("Cache Hits", output["cache_hits"])

    if output["decision"] == "APPROVE":
        st.success("Decision: APPROVE")
    elif output["decision"] == "REJECT":
        st.error("Decision: REJECT")
    else:
        st.warning("Decision: FLAG FOR REVIEW")

    st.write("**Arithmetic result:**")
    st.write(
        f"Available balance − transaction amount = "
        f"NPR {output['remaining']:,.2f}"
    )

    st.subheader("Rule Evaluation")
    rule_table = pd.DataFrame([
        {
            "Rule": k,
            "Triggered": v,
            "Result": "Risk added" if v else "No risk added"
        }
        for k, v in output["results"].items()
    ])
    st.dataframe(rule_table, use_container_width=True)

    st.subheader("3. Instruction Cycle Log")
    st.dataframe(pd.DataFrame(output["log"]), use_container_width=True)

    st.subheader("4. Pipeline and Cache Statistics")
    st.write(f"Instructions: {output['instruction_count']}")
    st.write(f"Sequential model cycles: {output['sequential_cycles']}")
    st.write(f"Pipeline model cycles: {output['pipeline_cycles']}")
    st.write(f"Cache misses: {output['cache_misses']}")
    st.caption(
        "These are simplified educational counts. The cache stores exact "
        "rule results for identical inputs; it does not represent a real "
        "CPU instruction/data cache."
    )

# -------------------- HISTORY --------------------
st.header("5. Transaction History")

if st.session_state.history:
    history_df = pd.DataFrame(st.session_state.history)
    st.dataframe(history_df, use_container_width=True)

    csv = history_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Transaction Report (CSV)",
        data=csv,
        file_name="fraud_report.csv",
        mime="text/csv"
    )
else:
    st.info("Process a transaction to generate the report.")

st.sidebar.divider()
if st.sidebar.button("Clear Simulation History"):
    st.session_state.history = []
    st.session_state.cycle_log = []
    st.session_state.cache = {}
    st.session_state.next_id = 1
    st.rerun()
