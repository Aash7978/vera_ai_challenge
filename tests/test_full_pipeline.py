from collections import Counter

from app.data_loader import DataLoader
from app.context_store import ContextStore
from app.vera import Vera


DATA_DIR = "dataset/expanded"


def main():

    loader = DataLoader(DATA_DIR)
    data = loader.load_all()

    store = ContextStore(data)
    vera = Vera()

    results = []

    for trigger_id in data["triggers"]:

        context = store.build_context(trigger_id)

        try:
            result = vera.run(context)

            results.append({
                "trigger_id": trigger_id,
                "status": result.status,
                "should_act": result.should_act,
                "reason": (
                    result.reasons[0]
                    if result.reasons
                    else None
                ),
            })

        except Exception as exc:

            results.append({
                "trigger_id": trigger_id,
                "status": "ERROR",
                "should_act": False,
                "reason": str(exc),
            })

    print("\n" + "=" * 70)
    print("VERA FULL PIPELINE")
    print("=" * 70)

    print("Total:", len(results))

    print(
        "Approved:",
        sum(
            r["status"] == "approved"
            for r in results
        ),
    )

    print(
        "Suppressed:",
        sum(
            r["status"] == "suppressed"
            for r in results
        ),
    )

    print(
        "Errors:",
        sum(
            r["status"] == "ERROR"
            for r in results
        ),
    )

    print("\nStatus distribution:")

    for status, count in Counter(
        r["status"]
        for r in results
    ).items():

        print(
            f"  {status}: {count}"
        )

    print("\nErrors:")

    for result in results:

        if result["status"] == "ERROR":

            print(
                result["trigger_id"],
                "->",
                result["reason"],
            )


if __name__ == "__main__":
    main()