from typing import Any, Dict, List


class OpportunityScorer:

    def score(
        self,
        context: Dict[str, Any],
        decision: Dict[str, Any],
    ) -> Dict[str, Any]:

        candidates = self._generate_candidates(
            context,
            decision,
        )

        scored = []

        for candidate in candidates:
            scored.append(
                self._score_candidate(
                    context,
                    candidate,
                )
            )

        if not scored:
            return self._no_opportunity()

        scored.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        selected = scored[0]

        return {
            "should_act": selected["score"] >= 0.50,
            "selected": selected,
            "alternatives": scored[1:],
        }

    # ---------------------------------------------------------
    # Candidate generation
    # ---------------------------------------------------------

    def _generate_candidates(
        self,
        context,
        decision,
    ) -> List[Dict[str, Any]]:

        candidates = []

        opportunity = decision.get("opportunity")

        if opportunity == "customer_reactivation":
            candidates.append({
                "type": "customer_reactivation",
                "action": "customer_outreach",
            })

        elif opportunity == "performance_recovery":
            candidates.append({
                "type": "performance_recovery",
                "action": "merchant_outreach",
            })

            # If the merchant has offers, an offer-related
            # action is also potentially useful.
            if context["merchant"].get("offers"):
                candidates.append({
                    "type": "offer_optimization",
                    "action": "merchant_outreach",
                })

        elif opportunity == "demand_opportunity":
            candidates.append({
                "type": "demand_capture",
                "action": "merchant_outreach",
            })

        elif opportunity == "business_action":
            candidates.append({
                "type": "business_followup",
                "action": "merchant_outreach",
            })

        elif opportunity == "trigger_followup":
            candidates.append({
                "type": "trigger_followup",
                "action": (
                    "customer_outreach"
                    if context.get("customer")
                    else "merchant_outreach"
                ),
            })

        return candidates

    # ---------------------------------------------------------
    # Candidate scoring
    # ---------------------------------------------------------

    def _score_candidate(
        self,
        context,
        candidate,
    ) -> Dict[str, Any]:

        trigger = context["trigger"]
        merchant = context["merchant"]
        customer = context.get("customer")

        urgency = self._urgency_score(trigger)

        relevance = self._relevance_score(
            context,
            candidate,
        )

        actionability = self._actionability_score(
            context,
            candidate,
        )

        evidence = self._evidence_score(
            context,
            candidate,
        )

        score = (
            0.30 * urgency
            + 0.25 * relevance
            + 0.25 * actionability
            + 0.20 * evidence
        )

        return {
            "type": candidate["type"],
            "action": candidate["action"],
            "score": round(score, 3),
            "components": {
                "urgency": round(urgency, 3),
                "relevance": round(relevance, 3),
                "actionability": round(actionability, 3),
                "evidence": round(evidence, 3),
            },
        }

    # ---------------------------------------------------------
    # Scoring dimensions
    # ---------------------------------------------------------

    def _urgency_score(self, trigger) -> float:

        value = trigger.get("urgency", 0)

        try:
            value = float(value)
        except (TypeError, ValueError):
            return 0.0

        return min(max(value / 10.0, 0.0), 1.0)

    def _relevance_score(
        self,
        context,
        candidate,
    ) -> float:

        trigger = context["trigger"]
        customer = context.get("customer")

        score = 0.50

        kind = trigger.get("kind")

        customer_candidates = {
            "customer_reactivation",
        }

        if (
            candidate["type"] in customer_candidates
            and customer is not None
        ):
            score += 0.30

        if kind:
            score += 0.10

        return min(score, 1.0)

    def _actionability_score(
        self,
        context,
        candidate,
    ) -> float:

        merchant = context["merchant"]
        customer = context.get("customer")

        score = 0.40

        if merchant.get("offers"):
            score += 0.20

        if customer is not None:
            preferences = customer.get(
                "preferences",
                {},
            )

            if preferences:
                score += 0.20

        if merchant.get("signals"):
            score += 0.10

        return min(score, 1.0)

    def _evidence_score(
        self,
        context,
        candidate,
    ) -> float:

        trigger = context["trigger"]
        merchant = context["merchant"]

        score = 0.30

        if trigger.get("payload"):
            score += 0.30

        if merchant.get("performance"):
            score += 0.20

        if merchant.get("review_themes"):
            score += 0.10

        return min(score, 1.0)

    @staticmethod
    def _no_opportunity():

        return {
            "should_act": False,
            "selected": None,
            "alternatives": [],
        }