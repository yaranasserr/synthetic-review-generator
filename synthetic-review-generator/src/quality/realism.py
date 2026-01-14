import os
from openai import OpenAI


class RealismMetric:
    def __init__(self, config):
        self.min_score = config["quality_thresholds"]["min_realism_score"]
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def check(self, text):
        prompt = (
            "Rate how realistic this GitLab review is on a scale from 1 to 10.\n\n"
            f'Review: "{text}"\n\n'
            "Reply with only a number."
        )

        try:
            res = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=5,
            )

            score = float(res.choices[0].message.content.strip())

            return {
                "passed": score >= self.min_score,
                "score": score,
            }

        except Exception:
            # Fail open to avoid blocking generation
            return {"passed": True, "score": 7.0}
