


class PersonaMetric:
    def __init__(self, config):
        self.min_matches = config["quality_thresholds"]["min_persona_keyword_matches"]

    def check(self, text, persona_keywords):
        """Check if review contains minimum persona keywords"""
        if not persona_keywords:
            # If no keywords provided, pass
            return {"passed": True, "score": 0}
        
        text_lower = text.lower()
        matches = sum(1 for keyword in persona_keywords if keyword.lower() in text_lower)
        
        return {
            "passed": matches >= self.min_matches,
            "score": matches,
        }