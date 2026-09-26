from dataclasses import asdict

from app.evidence import EvidenceBuilder
from app.decision_engine import DecisionEngine
from app.opportunity_scorer import OpportunityScorer
from app.composer import LLMComposer
from app.eligibility import EligibilityChecker
from app.suppression import SuppressionStore
from app.policy import VeraPolicy
from app.response_builder import ResponseBuilder
from app.grounding_validator import GroundingValidator

class Vera:

    def __init__(self):

        self.evidence_builder = (
            EvidenceBuilder()
        )

        self.decision_engine = (
            DecisionEngine()
        )

        self.scorer = (
            OpportunityScorer()
        )

        self.composer = (
            LLMComposer()
        )

        self.grounding_validator = (
    GroundingValidator()
)

        self.eligibility_checker = (
            EligibilityChecker()
        )

        self.suppression_store = (
            SuppressionStore()
        )

        self.policy = VeraPolicy(
            suppression_store=(
                self.suppression_store
            ),
            eligibility_checker=(
                self.eligibility_checker
            ),
            grounding_validator=(
                self.grounding_validator
            ),
        )
        
        self.response_builder = ResponseBuilder()

    def run(
        self,
        context,
    ):

        evidence = (
            self.evidence_builder.build(
                context
            )
        )

        decision = (
            self.decision_engine.decide(
                context
            )
        )

        score_result = (
            self.scorer.score(
                context,
                decision,
            )
        )

        response = self.composer.compose(
            context,
            decision,
            score_result,
            evidence
        )

        response_dict = asdict(
            response
        )

        policy_result = (
    self.policy.evaluate(
        context=context,
        evidence=evidence,
        decision=decision,
        score_result=score_result,
        response=response_dict,
    )
)

        if policy_result["allowed"]:

            self.suppression_store.record(
                response_dict.get(
                    "suppression_key"
                )
            )

        final_response = (
            self.response_builder.build(
                context=context,
                decision=decision,
                score_result=score_result,
                response=response_dict,
                policy=policy_result,
            )
        )

        return final_response