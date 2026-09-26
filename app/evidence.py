from typing import Any, Dict


class EvidenceBuilder:

    def build(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:

        trigger = context["trigger"]
        merchant = context["merchant"]
        customer = context.get("customer")
        category = context["category"]

        return {
            "trigger": self._trigger_evidence(trigger),
            "merchant": self._merchant_evidence(merchant),
            "customer": self._customer_evidence(customer),
            "category": self._category_evidence(category),
        }

    def _trigger_evidence(self, trigger):

        return {
            "kind": trigger.get("kind"),
            "urgency": trigger.get("urgency"),
            "payload": trigger.get("payload", {}),
            "source": trigger.get("source"),
        }

    def _merchant_evidence(self, merchant):

        performance = merchant.get(
            "performance",
            {},
        )

        return {
            "merchant_id": merchant.get("merchant_id"),
            "category_slug": merchant.get("category_slug"),
            "performance": performance,
            "offers": merchant.get("offers", []),
            "signals": merchant.get("signals", []),
            "review_themes": merchant.get(
                "review_themes",
                [],
            ),
        }

    def _customer_evidence(self, customer):

        if customer is None:
            return None

        return {
            "customer_id": customer.get(
                "customer_id"
            ),
            "state": customer.get("state"),
            "relationship": customer.get(
                "relationship",
                {},
            ),
            "preferences": customer.get(
                "preferences",
                {},
            ),
            "consent": customer.get(
                "consent",
                {},
            ),
        }

    def _category_evidence(self, category):

        return {
            "slug": category.get("slug"),
            "display_name": category.get(
                "display_name"
            ),
            "peer_stats": category.get(
                "peer_stats",
                {},
            ),
            "offer_catalog": category.get(
                "offer_catalog",
                {},
            ),
            "trend_signals": category.get(
                "trend_signals",
                [],
            ),
        }