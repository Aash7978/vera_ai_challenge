from fastapi import FastAPI, HTTPException

from app.data_loader import DataLoader
from app.context_store import ContextStore
from app.models import VeraRequest, VeraResponse
from app.vera import Vera


DATA_DIR = "dataset/expanded"


app = FastAPI(
    title="VERA",
    description="Magicpin VERA Challenge Agent",
    version="0.1.0",
)


loader = DataLoader(DATA_DIR)
data = loader.load_all()

store = ContextStore(data)

vera = Vera()


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.post(
    "/evaluate",
    response_model=VeraResponse,
)
def evaluate(
    request: VeraRequest,
):

    try:
        context = store.build_context(
            request.trigger_id
        )

    except Exception as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    return vera.run(
        context
    )


# ---------------------------------------------------------
# STEP 7.10 — Development endpoint
# ---------------------------------------------------------

@app.get("/triggers")
def triggers():

    return [
        {
            "id": trigger_id,
            "kind": trigger.get("kind"),
        }
        for trigger_id, trigger
        in data["triggers"].items()
    ]


# ---------------------------------------------------------
# STEP 7.11 — Convenient GET evaluation endpoint
# ---------------------------------------------------------

@app.get(
    "/evaluate/{trigger_id}",
    response_model=VeraResponse,
)
def evaluate_trigger(
    trigger_id: str,
):

    try:
        context = store.build_context(
            trigger_id
        )

    except Exception as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    return vera.run(
        context
    )