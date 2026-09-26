from typing import Any, Dict
from datetime import datetime, timezone

class VeraPolicy:

    def __init__(
        self,
        suppression_store,
        eligibility_checker,
        grounding_validator,
    ):

        self.suppression_store = (
            suppression_store
        )

        self.eligibility_checker = (
            eligibility_checker
        )

        self.grounding_validator = (
            grounding_validator
        )

    def evaluate(
    self,
    context: Dict[str, Any],
    evidence: Dict[str, Any],
    decision: Dict[str, Any],
    score_result: Dict[str, Any],
    response: Dict[str, Any],
) -> Dict[str, Any]:

        # -----------------------------------------------------
        # 1. Decision gate
        # -----------------------------------------------------

        if not decision.get(
            "should_act",
            False,
        ):

            return self._reject(
                "Decision engine said not to act."
            )
            
        if self._expired(
            context["trigger"]
        ):
            return self._reject(
                "Trigger has expired."
            )
        # -----------------------------------------------------
        # 2. Score gate
        # -----------------------------------------------------

        if not score_result.get(
            "should_act",
            False,
        ):

            return self._reject(
                "Opportunity score is below action threshold."
            )

        # -----------------------------------------------------
        # 3. Eligibility gate
        # -----------------------------------------------------

        eligibility = (
            self.eligibility_checker.check(
                context,
                decision,
            )
        )

        if not eligibility["eligible"]:

            return self._reject(
                eligibility["reason"]
            )

        # -----------------------------------------------------
        # 4. Suppression gate
        # -----------------------------------------------------

        suppression_key = response.get(
            "suppression_key"
        )

        if self.suppression_store.has_been_sent(
            suppression_key
        ):

            return self._reject(
                "Suppression key has already been used."
            )

        # -----------------------------------------------------
        # 5. Grounding gate
        # -----------------------------------------------------

        grounding = (
    self.grounding_validator.validate(
        response,
        evidence,
    )
)

        if not grounding["valid"]:

            return self._reject(
                grounding["reason"],
                details=grounding,
            )

        # -----------------------------------------------------
        # Passed
        # -----------------------------------------------------

        return {
            "allowed": True,
            "reason": None,
            "details": grounding,
        }

    @staticmethod
    def _reject(
        reason,
        details=None,
    ):

        return {
            "allowed": False,
            "reason": reason,
            "details": details,
        }
    
    def _expired(self, trigger):

        expires_at = trigger.get(
            "expires_at"
        )

        if not expires_at:
            return False

        try:
            expiry = datetime.fromisoformat(
                expires_at.replace(
                    "Z",
                    "+00:00",
                )
            )

            return (
                datetime.now(timezone.utc)
                >= expiry
            )

        except ValueError:
            # Invalid expiry should not silently
            # result in an action.
            return True