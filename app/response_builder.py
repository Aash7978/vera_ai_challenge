from typing import Any, Dict

from app.models import (
    Message,
    VeraResponse,
)


class ResponseBuilder:

    def build(
        self,
        context: Dict[str, Any],
        decision: Dict[str, Any],
        score_result: Dict[str, Any],
        response: Dict[str, Any],
        policy: Dict[str, Any],
    ) -> VeraResponse:

        allowed = policy.get(
            "allowed",
            False,
        )

        selected = score_result.get(
            "selected"
        )

        if not allowed or not selected:

            return VeraResponse(
                should_act=False,
                status="suppressed",
                reasons=[
                    policy.get(
                        "reason",
                        "Action not approved.",
                    )
                ],
            )

        customer = context.get(
            "customer"
        )

        audience = (
            "customer"
            if customer is not None
            else "merchant"
        )

        message = Message(
            body=response.get(
                "body",
                "",
            ),
            cta=response.get(
                "cta"
            ),
            send_as=response.get(
                "send_as",
                "dashboard",
            ),
        )

        return VeraResponse(
            should_act=True,
            status="approved",
            audience=audience,
            action=selected.get(
                "action"
            ),
            opportunity=selected.get(
                "type"
            ),
            priority=selected.get(
                "score",
                0.0,
            ),
            message=message,
            evidence=selected.get(
                "components",
                {},
            ),
            reasons=decision.get(
                "reason",
                [],
            ),
            suppression_key=response.get(
                "suppression_key"
            ),
        )