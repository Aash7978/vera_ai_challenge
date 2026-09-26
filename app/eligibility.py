from typing import Any, Dict


class EligibilityChecker:

    def check(
        self,
        context: Dict[str, Any],
        decision: Dict[str, Any],
    ) -> Dict[str, Any]:

        customer = context.get("customer")

        # If this is not a customer interaction,
        # customer consent is irrelevant.
        if not decision.get(
            "customer_required",
            False,
        ):
            return {
                "eligible": True,
                "reason": None,
            }

        if customer is None:
            return {
                "eligible": False,
                "reason": "Customer context is missing.",
            }

        consent = customer.get(
            "consent",
            {},
        )

        if (
            consent.get(
                "promotional_opt_in"
            )
            is False
        ):
            return {
                "eligible": False,
                "reason": (
                    "Customer has not opted in "
                    "to promotional communication."
                ),
            }

        return {
            "eligible": True,
            "reason": None,
        }