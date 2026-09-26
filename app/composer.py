import json
import os
import time
from dataclasses import dataclass
from typing import Optional, Any, Dict

from google import genai
from google.genai import types

from app.prompts import COMPOSER_SYSTEM_PROMPT
from app.response_validator import ResponseValidator


# ============================================================
# RESPONSE OBJECT
# ============================================================

@dataclass
class ComposedResponse:
    body: str
    cta: Optional[str]
    send_as: str
    suppression_key: Optional[str]
    rationale: str


# ============================================================
# CONTEXT BUILDER
# ============================================================

class ComposerContextBuilder:
    """
    Converts the internal VERA context into the smaller,
    approved context sent to the LLM.

    Gemini receives only approved information.

    Gemini does NOT decide:
        - whether VERA should act
        - priority
        - suppression
        - opportunity selection
        - send_as
    """

    def build(
        self,
        context,
        decision,
        score_result,
        evidence,
    ):

        merchant = context["merchant"]
        customer = context.get("customer")
        trigger = context["trigger"]

        selected = score_result.get(
            "selected"
        )

        return {
            "trigger": {
                "id": trigger.get("id"),
                "kind": trigger.get("kind"),
                "urgency": trigger.get("urgency"),
                "payload": trigger.get(
                    "payload",
                    {},
                ),
            },

            "evidence": evidence,

            "decision": {
                "should_act": decision.get(
                    "should_act"
                ),
                "opportunity": decision.get(
                    "opportunity"
                ),
                "action": decision.get(
                    "action"
                ),
            },

            "selected_opportunity": selected,

            "merchant": {
                "name": merchant["identity"].get(
                    "name"
                ),
                "category": merchant.get(
                    "category_slug"
                ),
                "city": merchant["identity"].get(
                    "city"
                ),
                "offers": merchant.get(
                    "offers",
                    [],
                ),
                "performance": merchant.get(
                    "performance",
                    {},
                ),
            },

            "customer": (
                {
                    "name": customer["identity"].get(
                        "name"
                    ),
                    "state": customer.get(
                        "state"
                    ),
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
                if customer
                else None
            ),
        }


# ============================================================
# LLM COMPOSER
# ============================================================

class LLMComposer:
    """
    Uses Gemini to compose the final VERA message.

    Gemini does NOT make VERA's decision.

    Deterministic VERA layers already decide:
        - should_act
        - opportunity
        - priority
        - suppression
        - evidence

    Gemini only turns approved context into:
        - body
        - cta
        - rationale

    send_as is always deterministic.
    """

    def __init__(
        self,
        model: str = "gemini-3.8-flash",
    ):

        self.model = model

        self.context_builder = (
            ComposerContextBuilder()
        )

        self.validator = (
            ResponseValidator()
        )

        api_key = os.environ.get(
            "GEMINI_API_KEY"
        )

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. "
                "Run: export GEMINI_API_KEY='YOUR_KEY'"
            )

        self.client = genai.Client(
            api_key=api_key
        )

    # ========================================================
    # MAIN COMPOSE METHOD
    # ========================================================

    def compose(
        self,
        context,
        decision,
        score_result,
        evidence,
    ) -> ComposedResponse:

        # ----------------------------------------------------
        # 1. Build approved context
        # ----------------------------------------------------

        payload = (
            self.context_builder.build(
                context=context,
                decision=decision,
                score_result=score_result,
                evidence=evidence,
            )
        )

        # ----------------------------------------------------
        # 2. Determine send_as deterministically
        # ----------------------------------------------------

        merchant = context["merchant"]

        identity = merchant.get(
            "identity",
            {},
        )

        send_as = identity.get(
            "name"
        )

        if not send_as:
            send_as = "dashboard"

        # ----------------------------------------------------
        # 3. Get suppression key
        # ----------------------------------------------------

        trigger = context["trigger"]

        suppression_key = trigger.get(
            "suppression_key"
        )

        # ----------------------------------------------------
        # 4. Build prompt
        # ----------------------------------------------------

        user_prompt = (
            "Create the VERA response using ONLY "
            "the approved context below.\n\n"

            "VERA has already decided whether to act. "
            "Do not make a new decision.\n\n"

            "Do not invent facts.\n\n"

            "Return only JSON containing:\n"
            "- body\n"
            "- cta\n"
            "- rationale\n\n"

            "Do NOT return send_as. "
            "VERA controls send_as deterministically.\n\n"

            "APPROVED CONTEXT:\n"
            +
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
            )
        )

        # ----------------------------------------------------
        # 5. Ask Gemini
        # ----------------------------------------------------

        response = None
        last_error = None

        max_attempts = 2

        for attempt in range(
            max_attempts
        ):

            try:

                response = (
                    self.client.models.generate_content(

                        model=self.model,

                        contents=user_prompt,

                        config=(
                            types.GenerateContentConfig(

                                system_instruction=(
                                    COMPOSER_SYSTEM_PROMPT
                                ),

                                response_mime_type=(
                                    "application/json"
                                ),

                                response_schema={
                                    "type": "object",

                                    "properties": {

                                        "body": {
                                            "type": "string"
                                        },

                                        "cta": {
                                            "type": [
                                                "string",
                                                "null",
                                            ]
                                        },

                                        "rationale": {
                                            "type": "string"
                                        },
                                    },

                                    "required": [
                                        "body",
                                        "cta",
                                        "rationale",
                                    ],
                                },
                            )
                        ),
                    )
                )

                break

            except Exception as exc:

                last_error = exc

                print(
                    f"Gemini attempt "
                    f"{attempt + 1}/"
                    f"{max_attempts} failed: "
                    f"{exc}"
                )

                # --------------------------------------------
                # Don't waste time retrying quota exhaustion
                # --------------------------------------------

                error_text = str(
                    exc
                ).lower()

                if (
                    "429" in error_text
                    or "resource_exhausted"
                    in error_text
                    or "quota" in error_text
                ):
                    print(
                        "Gemini unavailable. "
                        "Using deterministic fallback: "
                        "Gemini quota exhausted."
                    )

                    break

                # --------------------------------------------
                # Retry temporary service failures
                # --------------------------------------------

                if (
                    attempt
                    < max_attempts - 1
                ):

                    time.sleep(
                        2
                    )

        # ----------------------------------------------------
        # 6. Gemini unavailable -> deterministic fallback
        # ----------------------------------------------------

        if response is None:

            return self._fallback_response(
                context=context,
                decision=decision,
                score_result=score_result,
                evidence=evidence,
                send_as=send_as,
                suppression_key=suppression_key,
                error=last_error,
            )

        # ----------------------------------------------------
        # 7. Extract Gemini response
        # ----------------------------------------------------

        raw_output = getattr(
            response,
            "text",
            None,
        )

        if not raw_output:

            print(
                "Gemini returned empty output. "
                "Using deterministic fallback."
            )

            return self._fallback_response(
                context=context,
                decision=decision,
                score_result=score_result,
                evidence=evidence,
                send_as=send_as,
                suppression_key=suppression_key,
                error=None,
            )

        # ----------------------------------------------------
        # 8. Parse JSON
        # ----------------------------------------------------

        try:

            result = json.loads(
                raw_output
            )

        except json.JSONDecodeError as exc:

            print(
                "Gemini returned invalid JSON. "
                "Using deterministic fallback."
            )

            return self._fallback_response(
                context=context,
                decision=decision,
                score_result=score_result,
                evidence=evidence,
                send_as=send_as,
                suppression_key=suppression_key,
                error=exc,
            )

        # ----------------------------------------------------
        # 9. VERA controls send_as
        # ----------------------------------------------------

        result["send_as"] = send_as

        # ----------------------------------------------------
        # 10. Make sure optional CTA exists
        # ----------------------------------------------------

        if "cta" not in result:

            result["cta"] = None

        # ----------------------------------------------------
        # 11. Make sure rationale exists
        # ----------------------------------------------------

        if "rationale" not in result:

            result["rationale"] = (
                "Response composed from "
                "approved VERA context."
            )

        # ----------------------------------------------------
        # 12. Validate
        # ----------------------------------------------------

        try:

            self.validator.validate(
                result
            )

        except ValueError as exc:

            print(
                "Gemini response failed validation: "
                f"{exc}"
            )

            return self._fallback_response(
                context=context,
                decision=decision,
                score_result=score_result,
                evidence=evidence,
                send_as=send_as,
                suppression_key=suppression_key,
                error=exc,
            )

        # ----------------------------------------------------
        # 13. Return composed response
        # ----------------------------------------------------

        return ComposedResponse(

            body=result["body"],

            cta=result.get(
                "cta"
            ),

            send_as=send_as,

            suppression_key=suppression_key,

            rationale=result[
                "rationale"
            ],
        )

    # ========================================================
    # DETERMINISTIC FALLBACK
    # ========================================================

    def _fallback_response(
        self,
        context,
        decision,
        score_result,
        evidence,
        send_as,
        suppression_key,
        error=None,
    ) -> ComposedResponse:
        """
        Deterministic fallback used when Gemini is unavailable.

        This is especially important when the Gemini free-tier
        quota is exhausted.

        The fallback does not invent appointment times,
        prices, offers, or other unsupported facts.
        """

        customer = context.get(
            "customer"
        )

        trigger = context.get(
            "trigger",
            {},
        )

        kind = trigger.get(
            "kind",
            "opportunity",
        )

        customer_name = None

        if customer:

            customer_name = (
                customer
                .get("identity", {})
                .get("name")
            )

        # ----------------------------------------------------
        # Customer-facing fallback
        # ----------------------------------------------------

        if (
            customer_name
            and decision.get(
                "action"
            ) == "customer_outreach"
        ):

            body = (
                f"Hi {customer_name}, "
                f"this is a reminder from "
                f"{send_as} that your "
                f"appointment is due."
            )

            cta = (
                "Reply to this message "
                "to book a convenient time."
            )

        # ----------------------------------------------------
        # Generic customer fallback
        # ----------------------------------------------------

        elif customer_name:

            body = (
                f"Hi {customer_name}, "
                f"we wanted to follow up "
                f"regarding your recent "
                f"activity with {send_as}."
            )

            cta = (
                "Reply to this message "
                "if you'd like to continue."
            )

        # ----------------------------------------------------
        # Merchant-facing fallback
        # ----------------------------------------------------

        else:

            body = (
                f"{send_as} has an active "
                f"VERA opportunity related "
                f"to {kind}."
            )

            cta = (
                "Review the opportunity."
            )

        # ----------------------------------------------------
        # Rationale
        # ----------------------------------------------------

        if error:

            rationale = (
                "Deterministic fallback used "
                "because Gemini composition "
                "was unavailable."
            )

        else:

            rationale = (
                "Deterministic fallback used "
                "because Gemini returned an "
                "empty or invalid response."
            )

        result = {
            "body": body,
            "cta": cta,
            "send_as": send_as,
            "rationale": rationale,
        }

        # ----------------------------------------------------
        # Validate fallback too
        # ----------------------------------------------------

        self.validator.validate(
            result
        )

        return ComposedResponse(

            body=result["body"],

            cta=result["cta"],

            send_as=result["send_as"],

            suppression_key=(
                suppression_key
            ),

            rationale=result[
                "rationale"
            ],
        )


# ============================================================
# MOCK COMPOSER
# ============================================================

class MockComposer:
    """
    Deterministic composer used by tests.

    It avoids Gemini completely.
    """

    def __init__(self):

        self.validator = (
            ResponseValidator()
        )

    def compose(
        self,
        context,
        decision,
        score_result,
        evidence,
    ) -> ComposedResponse:

        merchant = context[
            "merchant"
        ]

        identity = merchant.get(
            "identity",
            {},
        )

        send_as = identity.get(
            "name",
            "dashboard",
        )

        customer = context.get(
            "customer"
        )

        trigger = context[
            "trigger"
        ]

        suppression_key = trigger.get(
            "suppression_key"
        )

        if customer:

            customer_name = (
                customer
                .get("identity", {})
                .get(
                    "name",
                    "there",
                )
            )

            body = (
                f"Hi {customer_name}, "
                f"this is a reminder from "
                f"{send_as} that your "
                f"appointment is due."
            )

            cta = (
                "Reply to this message "
                "to book a convenient time."
            )

        else:

            body = (
                f"{send_as} has an active "
                "VERA opportunity."
            )

            cta = (
                "Review the opportunity."
            )

        result = {
            "body": body,
            "cta": cta,
            "send_as": send_as,
            "rationale": (
                "Mock response generated "
                "for deterministic testing."
            ),
        }

        self.validator.validate(
            result
        )

        return ComposedResponse(

            body=result["body"],

            cta=result["cta"],

            send_as=result["send_as"],

            suppression_key=(
                suppression_key
            ),

            rationale=result[
                "rationale"
            ],
        )