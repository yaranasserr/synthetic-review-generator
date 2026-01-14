from textblob import TextBlob


class BiasMetric:
    def __init__(self, config):
        self.tolerance = config["quality_thresholds"]["sentiment_tolerance"]
        self.ranges = {
            5.0: (0.3, 1.0),
            4.5: (0.2, 1.0),
            4.0: (0.1, 0.8),
            3.5: (-0.1, 0.6),
            3.0: (-0.3, 0.5),
            2.5: (-0.5, 0.3),
            2.0: (-0.7, 0.2),
            1.5: (-0.9, 0.0),
            1.0: (-1.0, -0.2),
        }

    def check(self, rating, text):
        sentiment = TextBlob(text).sentiment.polarity
        low, high = self.ranges.get(rating, (-0.3, 0.5))

        return {
            "passed": (low - self.tolerance) <= sentiment <= (high + self.tolerance),
            "score": sentiment,
        }
