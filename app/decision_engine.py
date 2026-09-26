from typing import Any, Dict, List, Optional


class DecisionEngine:

    def decide(self, context: Dict[str, Any]) -> Dict[str, Any]:

        trigger = context["trigger"]
        merchant = context["merchant"]
        customer = context.get("customer")
        category = context["category"]

        kind = trigger.get("kind", "")
        urgency = trigger.get("urgency", 0)

        # Find the strongest applicable opportunity.
        decision = (
            self._customer_opportunity(trigger, merchant, customer, category)
            or self._performance_opportunity(trigger, merchant, category)
            or self._demand_opportunity(trigger, merchant, category)
            or self._business_opportunity(trigger, merchant, category)
            or self._generic_trigger_opportunity(
                trigger, merchant, customer, category
            )
        )

        if decision is None:
            return self._wait_decision(
                reason="No sufficiently actionable opportunity identified."
            )

        # Add trigger urgency to the decision.
        decision["trigger_urgency"] = urgency

        return decision

    # ---------------------------------------------------------
    # Customer opportunities
    # ---------------------------------------------------------

    def _customer_opportunity(
        self,
        trigger,
        merchant,
        customer,
        category,
    ) -> Optional[Dict[str, Any]]:

        kind = trigger.get("kind", "")

        customer_triggers = {
            "recall_due",
            "winback_eligible",
            "customer_lapsed_hard",
            "trial_followup",
            "wedding_package_followup",
        }

        if kind not in customer_triggers:
            return None

        if customer is None:
            return self._wait_decision(
                reason="Customer-level trigger has no customer context."
            )

        consent = customer.get("consent", {})

        # Do not recommend promotional outreach if consent
        # information explicitly says the customer opted out.
        if consent.get("promotional_opt_in") is False:
            return self._wait_decision(
                reason="Customer is not opted in for promotional outreach."
            )

        state = customer.get("state")

        reasons = [
            f"customer trigger '{kind}' is active"
        ]

        if state:
            reasons.append(
                f"customer state is '{state}'"
            )

        return {
            "should_act": True,
            "opportunity": "customer_reactivation",
            "priority": self._priority_from_trigger(trigger),
            "action": "customer_outreach",
            "reason": reasons,
            "evidence": {
                "trigger_kind": kind,
                "customer_state": state,
            },
            "customer_required": True,
        }

    # ---------------------------------------------------------
    # Performance opportunities
    # ---------------------------------------------------------

    def _performance_opportunity(
        self,
        trigger,
        merchant,
        category,
    ) -> Optional[Dict[str, Any]]:

        kind = trigger.get("kind", "")

        performance_triggers = {
            "perf_dip",
            "seasonal_perf_dip",
            "milestone_reached",
        }

        if kind not in performance_triggers:
            return None

        performance = merchant.get("performance", {})

        ctr = self._number(performance.get("ctr"))
        delta_7d = self._number(performance.get("delta_7d"))

        reasons = [
            f"trigger '{kind}' indicates a performance opportunity"
        ]

        evidence = {
            "trigger_kind": kind,
        }

        if ctr is not None:
            evidence["ctr"] = ctr
            reasons.append(f"current CTR is {ctr}")

        if delta_7d is not None:
            evidence["delta_7d"] = delta_7d

        # Existing merchant offers make a performance problem
        # more actionable.
        offers = merchant.get("offers", [])

        if offers:
            reasons.append("merchant has an existing offer")
            evidence["offer_count"] = len(offers)

        return {
            "should_act": True,
            "opportunity": "performance_recovery",
            "priority": self._priority_from_trigger(trigger),
            "action": "merchant_outreach",
            "reason": reasons,
            "evidence": evidence,
            "customer_required": False,
        }

    # ---------------------------------------------------------
    # Demand opportunities
    # ---------------------------------------------------------

    def _demand_opportunity(
        self,
        trigger,
        merchant,
        category,
    ) -> Optional[Dict[str, Any]]:

        kind = trigger.get("kind", "")

        demand_triggers = {
            "research_digest",
            "active_planning_intent",
            "curious_ask_due",
            "ipl_match_today",
            "festival_upcoming",
        }

        if kind not in demand_triggers:
            return None

        payload = trigger.get("payload", {})

        return {
            "should_act": True,
            "opportunity": "demand_opportunity",
            "priority": self._priority_from_trigger(trigger),
            "action": "merchant_outreach",
            "reason": [
                f"trigger '{kind}' indicates a demand opportunity"
            ],
            "evidence": {
                "trigger_kind": kind,
                "payload": payload,
            },
            "customer_required": False,
        }

    # ---------------------------------------------------------
    # Business opportunities
    # ---------------------------------------------------------

    def _business_opportunity(
        self,
        trigger,
        merchant,
        category,
    ) -> Optional[Dict[str, Any]]:

        kind = trigger.get("kind", "")

        business_triggers = {
            "renewal_due",
            "regulation_change",
            "supply_alert",
            "review_theme_emerged",
        }

        if kind not in business_triggers:
            return None

        return {
            "should_act": True,
            "opportunity": "business_action",
            "priority": self._priority_from_trigger(trigger),
            "action": "merchant_outreach",
            "reason": [
                f"business trigger '{kind}' requires attention"
            ],
            "evidence": {
                "trigger_kind": kind,
                "payload": trigger.get("payload", {}),
            },
            "customer_required": False,
        }

    # ---------------------------------------------------------
    # Generic fallback
    # ---------------------------------------------------------

    def _generic_trigger_opportunity(
        self,
        trigger,
        merchant,
        customer,
        category,
    ) -> Optional[Dict[str, Any]]:

        kind = trigger.get("kind")

        if not kind:
            return None

        return {
            "should_act": True,
            "opportunity": "trigger_followup",
            "priority": self._priority_from_trigger(trigger),
            "action": (
                "customer_outreach"
                if customer is not None
                else "merchant_outreach"
            ),
            "reason": [
                f"active trigger '{kind}' requires evaluation"
            ],
            "evidence": {
                "trigger_kind": kind,
                "payload": trigger.get("payload", {}),
            },
            "customer_required": customer is not None,
        }

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def _priority_from_trigger(self, trigger) -> float:

        urgency = trigger.get("urgency", 0)

        try:
            urgency = float(urgency)
        except (TypeError, ValueError):
            urgency = 0

        # Normalize the challenge's urgency into 0-1.
        #
        # We intentionally cap rather than assuming the exact
        # upper bound of future judge data.
        return min(max(urgency / 10.0, 0.0), 1.0)

    @staticmethod
    def _number(value):

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _wait_decision(reason):

        return {
            "should_act": False,
            "opportunity": None,
            "priority": 0.0,
            "action": "wait",
            "reason": [reason],
            "evidence": {},
            "customer_required": False,
        }