from app.data_loader import DataLoader
from app.context_store import ContextStore
from app.vera import Vera


DATA_DIR = "dataset/expanded"


def test_vera_approves_first_run_and_suppresses_second_run():

    loader = DataLoader(DATA_DIR)
    data = loader.load_all()

    store = ContextStore(data)

    vera = Vera()

    trigger_id = "trg_003_recall_due_priya"

    context = store.build_context(trigger_id)

    # First run
    result_1 = vera.run(context)

    print("\nFIRST RUN")
    print("=" * 60)
    print(result_1)

    assert result_1.should_act is True
    assert result_1.status == "approved"

    # Second run
    result_2 = vera.run(context)

    print("\nSECOND RUN")
    print("=" * 60)
    print(result_2)

    assert result_2.should_act is False
    assert result_2.status == "suppressed"

    assert (
        "Suppression key has already been used."
        in result_2.reasons
    )