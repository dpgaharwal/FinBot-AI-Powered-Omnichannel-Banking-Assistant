import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.router import router_node
from app.agents.state import FinBotState
from langchain_core.messages import HumanMessage

# Test cases: (input, expected_intent)
ROUTING_EVAL = [
    ("What is my account balance?", "balance"),
    ("Show me my recent transactions", "transactions"),
    ("What is the refund policy?", "policy"),
    ("My transaction failed, I want a refund", "dispute"),
    ("I want to pay my EMI", "loan"),
    ("I want to talk to a human agent", "handoff"),
    ("What are the ATM withdrawal limits?", "policy"),
    ("How much do I owe on my loan?", "loan"),
    ("My UPI payment failed", "dispute"),
    ("What is my savings account balance?", "balance"),
]


def run_routing_eval():
    print("=" * 50)
    print("FinBot Routing Accuracy Eval")
    print("=" * 50)

    correct = 0
    total = len(ROUTING_EVAL)
    results = []

    for user_input, expected in ROUTING_EVAL:
        state = FinBotState(
            messages=[HumanMessage(content=user_input)],
            intent="",
            customer_email="happy@finbot.com",
            customer_data={},
            account_data=[],
            context="",
            response="",
            escalate=False,
            summary=""
        )

        result = router_node(state)
        actual = result.get("intent", "unknown")
        is_correct = actual == expected
        if is_correct:
            correct += 1

        results.append({
            "input": user_input,
            "expected": expected,
            "actual": actual,
            "correct": is_correct
        })

        status = "✅" if is_correct else "❌"
        print(f"{status} [{expected}→{actual}] {user_input}")

    accuracy = (correct / total) * 100
    print("=" * 50)
    print(f"Routing Accuracy: {correct}/{total} = {accuracy:.1f}%")
    print("=" * 50)
    return accuracy


if __name__ == "__main__":
    run_routing_eval()