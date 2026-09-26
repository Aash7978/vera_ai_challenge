from dataclasses import asdict

from app.data_loader import DataLoader
from app.context_store import ContextStore
from app.decision_engine import DecisionEngine
from app.opportunity_scorer import OpportunityScorer
from app.composer import MockComposer


DATA_DIR = "dataset/expanded"


def main():

    loader = DataLoader(DATA_DIR)
    data = loader.load_all()

    store = ContextStore(data)
    engine = DecisionEngine()
    scorer = OpportunityScorer()
    composer = MockComposer()

    trigger_id = "trg_003_recall_due_priya"

    context = store.build_context(trigger_id)

    decision = engine.decide(context)

    score_result = scorer.score(
        context,
        decision,
    )

    response = composer.compose(
        context,
        decision,
        score_result,
    )

    print("\nFINAL RESPONSE")
    print("=" * 60)

    for key, value in asdict(response).items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()

class ComposerContextBuilder:

    def build(
        self,
        context,
        decision,
        score_result,
    ):

        merchant = context["merchant"]
        customer = context.get("customer")
        trigger = context["trigger"]

        selected = score_result.get("selected")

        return {
            "trigger": {
                "kind": trigger.get("kind"),
                "urgency": trigger.get("urgency"),
                "payload": trigger.get("payload", {}),
            },

            "decision": {
                "should_act": decision.get(
                    "should_act"
                ),
                "opportunity": decision.get(
                    "opportunity"
                ),
                "action": decision.get(
                    "action"
                ),
            },

            "selected_opportunity": selected,

            "merchant": {
                "name": merchant["identity"].get(
                    "name"
                ),
                "category": merchant.get(
                    "category_slug"
                ),
                "city": merchant["identity"].get(
                    "city"
                ),
                "offers": merchant.get(
                    "offers",
                    []
                ),
                "performance": merchant.get(
                    "performance",
                    {}
                ),
            },

            "customer": (
                {
                    "name": customer["identity"].get(
                        "name"
                    ),
                    "state": customer.get(
                        "state"
                    ),
                    "relationship": customer.get(
                        "relationship",
                        {}
                    ),
                    "preferences": customer.get(
                        "preferences",
                        {}
                    ),
                    "consent": customer.get(
                        "consent",
                        {}
                    ),
                }
                if customer
                else None
            ),
        }