from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .utils import tokenize, jaccard_similarity


class DiversityMetric:
    def __init__(self, config):
        self.max_jaccard = config["quality_thresholds"]["max_jaccard_similarity"]

    def check(self, text, existing_reviews):
        if not existing_reviews:
            return {"passed": True, "score": 0.0}

        current = set(tokenize(text))
        max_sim = 0.0

        for r in existing_reviews:
            words = set(tokenize(r["review_text"]))
            sim = jaccard_similarity(current, words)
            max_sim = max(max_sim, sim)

        return {
            "passed": max_sim <= self.max_jaccard,
            "score": max_sim,
        }


class SemanticMetric:
    def __init__(self, config):
        self.max_similarity = config["quality_thresholds"]["max_semantic_similarity"]
        self.vectorizer = TfidfVectorizer(max_features=500)

    def check(self, text, existing_reviews):
        if not existing_reviews:
            return {"passed": True, "score": 0.0}

        texts = [text] + [r["review_text"] for r in existing_reviews]

        try:
            vectors = self.vectorizer.fit_transform(texts)
            sims = cosine_similarity(vectors[0:1], vectors[1:])[0]
            max_sim = float(max(sims)) if len(sims) else 0.0

            return {
                "passed": max_sim <= self.max_similarity,
                "score": max_sim,
            }

        except Exception:
            return {"passed": True, "score": 0.0}
