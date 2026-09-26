from app.data_loader import DataLoader
from app.context_store import ContextStore
from app.decision_engine import DecisionEngine
from app.opportunity_scorer import OpportunityScorer


DATA_DIR = "dataset/expanded"


def run_trigger(trigger_id):

    loader = DataLoader(DATA_DIR)
    data = loader.load_all()

    store = ContextStore(data)

    decision_engine = DecisionEngine()
    scorer = OpportunityScorer()

    context = store.build_context(trigger_id)

    decision = decision_engine.decide(context)

    result = scorer.score(
        context,
        decision,
    )

    print("\n" + "=" * 70)
    print("TRIGGER")
    print("=" * 70)

    print("ID:", context["trigger"]["id"])
    print("Kind:", context["trigger"]["kind"])

    print(
        "Merchant:",
        context["merchant"]["identity"]["name"],
    )

    print(
        "Category:",
        context["merchant"]["category_slug"],
    )

    if context["customer"]:
        print(
            "Customer:",
            context["customer"]["identity"]["name"],
        )
    else:
        print("Customer: None")

    print("\n" + "=" * 70)
    print("BASE DECISION")
    print("=" * 70)

    print(decision)

    print("\n" + "=" * 70)
    print("OPPORTUNITY SCORING")
    print("=" * 70)

    print("Should act:", result["should_act"])
    print("Selected:", result["selected"])

    print("\nAlternatives:")

    for alternative in result["alternatives"]:
        print(alternative)

    return result


def test_context_builds():

    result = run_trigger(
        "trg_003_recall_due_priya"
    )

    assert result is not None


def test_context_builds_corporate_trigger():

    result = run_trigger(
        "trg_013_corporate_thali_planning"
    )

    assert result is not None