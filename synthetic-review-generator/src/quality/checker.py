from .length import LengthMetric
from .diversity import DiversityMetric, SemanticMetric
from .bias import BiasMetric
from .realism import RealismMetric
from .persona import PersonaMetric


class QualityChecker:
    def __init__(self, config):
        self.length = LengthMetric(config)
        self.diversity = DiversityMetric(config)
        self.semantic = SemanticMetric(config)
        self.bias = BiasMetric(config)
        self.realism = RealismMetric(config)
        self.persona = PersonaMetric(config)

    def check_all(self, review, existing_reviews):
        checks = []

        checks.append(("length", self.length.check(review["review_text"])))
        checks.append(("diversity", self.diversity.check(review["review_text"], existing_reviews)))
        checks.append(("semantic", self.semantic.check(review["review_text"], existing_reviews)))
        checks.append(("bias", self.bias.check(review["rating"], review["review_text"])))
        checks.append(("realism", self.realism.check(review["review_text"])))
        checks.append(("persona", self.persona.check(review["review_text"], review.get("persona_keywords", []))))

        for name, result in checks:
            if not result["passed"]:
                return {
                    "passed": False,
                    "failed_metric": name,
                    "score": result["score"],
                }

        return {
            "passed": True,
            "scores": {name: r["score"] for name, r in checks},
        }