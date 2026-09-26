from typing import Any, Dict

from app.response_validator import ResponseValidator


class GroundingValidator:
    """
    Adapter between VeraPolicy and ResponseValidator.

    VeraPolicy expects:

        validate(response, evidence)

    to return:

        {
            "valid": bool,
            "reason": str | None
        }
    """

    def __init__(self):
        self.response_validator = ResponseValidator()

    def validate(
        self,
        response: Dict[str, Any],
        evidence: Dict[str, Any],
    ) -> Dict[str, Any]:

        try:
            # ResponseValidator performs:
            # - required field validation
            # - body validation
            # - CTA validation
            # - send_as validation
            # - rationale validation
            self.response_validator.validate(response)

        except ValueError as exc:

            return {
                "valid": False,
                "reason": str(exc),
            }

        return {
            "valid": True,
            "reason": None,
        }