from collections import Counter

from app.data_loader import DataLoader
from app.context_store import ContextStore
from app.decision_engine import DecisionEngine
from app.opportunity_scorer import OpportunityScorer


DATA_DIR = "dataset/expanded"


def main():

    loader = DataLoader(DATA_DIR)
    data = loader.load_all()

    store = ContextStore(data)
    decision_engine = DecisionEngine()
    scorer = OpportunityScorer()

    results = []

    for trigger_id in data["triggers"]:

        context = store.build_context(trigger_id)

        decision = decision_engine.decide(context)

        score = scorer.score(
            context,
            decision,
        )

        results.append({
            "trigger_id": trigger_id,
            "kind": context["trigger"]["kind"],
            "should_act": score["should_act"],
            "opportunity": (
                score["selected"]["type"]
                if score["selected"]
                else None
            ),
            "score": (
                score["selected"]["score"]
                if score["selected"]
                else 0
            ),
        })

    print(
        "Total triggers:",
        len(results),
    )

    print(
        "Should act:",
        sum(
            r["should_act"]
            for r in results
        ),
    )

    print(
        "Should wait:",
        sum(
            not r["should_act"]
            for r in results
        ),
    )

    print("\nOpportunity distribution:")

    counts = Counter(
        r["opportunity"]
        for r in results
    )

    for opportunity, count in counts.items():
        print(
            f"  {opportunity}: {count}"
        )


if __name__ == "__main__":
    main()