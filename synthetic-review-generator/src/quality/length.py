class LengthMetric:
    def __init__(self, config):
        cfg = config["review_length"]
        self.min_words = cfg["min_words"]
        self.max_words = cfg["max_words"]

    def check(self, text):
        count = len(text.split())
        return {
            "passed": self.min_words <= count <= self.max_words,
            "score": count,
        }
