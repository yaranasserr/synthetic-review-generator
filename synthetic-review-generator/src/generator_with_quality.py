import random
import json
import os
import yaml
import csv
import time
from datetime import datetime

from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv
from tqdm import tqdm

from quality.checker import QualityChecker

load_dotenv()


class ReviewGenerator:
    def __init__(self):
        # Load config
        with open("config/config.yaml", "r") as f:
            self.config = yaml.safe_load(f)

        # APIs
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Quality system
        self.quality = QualityChecker(self.config)

        # Timestamp
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Output dirs
        self.base_dir = "data/synthetic"
        self.logs_dir = os.path.join(self.base_dir, "logs")
        self.reviews_dir = os.path.join(self.base_dir, "reviews")
        self.models_dir = os.path.join(self.base_dir, "reviews_models")

        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.reviews_dir, exist_ok=True)
        os.makedirs(self.models_dir, exist_ok=True)

        # Text log
        self.log_file = os.path.join(
            self.logs_dir, f"generation_log_{self.timestamp}.txt"
        )

        # CSV metrics log
        self.csv_file = os.path.join(
            self.logs_dir, f"generation_metrics_{self.timestamp}.csv"
        )

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "review_index",
                "attempt",
                "model",
                "title",
                "passed",
                "failed_metric",
                "generation_time_sec",
                "rating",
                "word_count",
                "low_quality_forced",
                "review_passed_quality"
            ])

    def log(self, msg):
        with open(self.log_file, "a") as f:
            f.write(msg + "\n")

    # ------------------------------------------------------------------
    # RAW GENERATION
    # ------------------------------------------------------------------
    def generate_one_raw(self, low_quality=False):
        """Generate ONE raw review. low_quality=True → intentionally bad prompt."""
        persona = random.choices(
            self.config["personas"],
            weights=[p["weight"] for p in self.config["personas"]],
        )[0]

        rating = random.choices(
            list(self.config["rating_distribution"].keys()),
            weights=list(self.config["rating_distribution"].values()),
        )[0]

        model = random.choices(
            self.config["models"],
            weights=[m["weight"] for m in self.config["models"]],
        )[0]

        # 🔥 Low-quality prompt (forces multiple metric failures)
        if low_quality:
            prompt = """
Write a GitLab review in ONE sentence.
Use less than 10 words.
Be extremely generic.
Do NOT mention any features.
"""
        else:
            prompt = f"""
Write a realistic GitLab review.

Persona: {persona['description']}
Rating: {rating}/5
Length: 50–150 words

Return JSON only:
{{"title": "...", "pros": "...", "cons": "..."}}
"""

        provider = model["provider"]

        if provider == "openai":
            res = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                response_format={"type": "json_object"},
            )
            text = res.choices[0].message.content

        elif provider == "anthropic":
            res = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )
            text = res.content[0].text

        else:
            raise ValueError(f"Unknown provider: {provider}")

        data = json.loads(text.strip().replace("```json", "").replace("```", ""))

        review_text = (
            f"{data.get('title', '')}. "
            f"Pros: {data.get('pros', '')} "
            f"Cons: {data.get('cons', '')}"
        ).strip()

        return {
            "rating": float(rating),
            "review_text": review_text,
            "title": data.get("title", ""),
            "pros": data.get("pros", ""),
            "cons": data.get("cons", ""),
            "model": f"{provider}/{model['model']}",
            "persona_keywords": persona.get("keywords", []),
        }

    # ------------------------------------------------------------------
    # GENERATE WITH QUALITY LOOP
    # ------------------------------------------------------------------
    def generate_one(
    self,
    existing_reviews,
    review_index,
    max_retries=3,
    force_low_quality_for_testing=False
):
        """
        generate → check → fail → regenerate → pass → return
        """

        # 🔥 Deterministic: every 5th review has forced bad first attempt
        force_bad_first_attempt = (review_index % 5 == 0)

        for attempt in range(1, max_retries + 1):
            low_quality_forced = force_bad_first_attempt and attempt == 1

            start = time.time()
            review = self.generate_one_raw(low_quality=low_quality_forced)
            gen_time = round(time.time() - start, 2)

            result = self.quality.check_all(review, existing_reviews)

            passed = result["passed"]
            failed_metric = None if passed else result["failed_metric"]

            # 🔒 THIS is the key flag you asked for
            review_passed_quality = passed

            # ✅ ALWAYS log — even failed forced attempts
            with open(self.csv_file, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    review_index,
                    attempt,
                    review["model"],
                    review["title"],
                    passed,
                    failed_metric,
                    gen_time,
                    review["rating"],
                    len(review["review_text"].split()),
                    low_quality_forced,
                    review_passed_quality
                ])

            if passed:
                self.log(
                    f"PASS | review={review_index} | attempt={attempt} | "
                    f"low_quality_forced={low_quality_forced} | saved=True"
                )
                return review

            # Explicit failure log
            self.log(
                f"FAIL | review={review_index} | attempt={attempt} | "
                f"low_quality_forced={low_quality_forced} | metric={failed_metric}"
            )

        self.log(f"SKIPPED | review={review_index} | max retries exceeded")
        return None


    # ------------------------------------------------------------------
    # DATASET GENERATION
    # ------------------------------------------------------------------
    def generate_all(self, count=400, force_low_quality_for_testing=False):
        final_reviews = []
        clean_reviews = []

        print(f"Generating {count} reviews with quality checks...")

        for i in tqdm(range(count)):
            review = self.generate_one(
                final_reviews,
                review_index=i,
                force_low_quality_for_testing=force_low_quality_for_testing
            )
            if not review:
                continue  # skip after max retries

            final_reviews.append(review)

            clean_reviews.append({
                "rating": review["rating"],
                "review_text": review["review_text"],
                "title": review["title"],
                "pros": review["pros"],
                "cons": review["cons"],
            })

        # Save outputs
        with open(
            f"{self.models_dir}/reviews_with_models_{self.timestamp}.json", "w"
        ) as f:
            json.dump(final_reviews, f, indent=2)

        with open(
            f"{self.reviews_dir}/reviews_clean_{self.timestamp}.json", "w"
        ) as f:
            json.dump(clean_reviews, f, indent=2)

        print("Done.")
        print(f"Saved {len(clean_reviews)} reviews")
        print(f"Logs: {self.logs_dir}")


if __name__ == "__main__":
    gen = ReviewGenerator()
    # Force at least one low-quality review for testing regeneration
    gen.generate_all(10, force_low_quality_for_testing=True)
