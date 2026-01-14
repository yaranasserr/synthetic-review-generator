"""Core review generation logic"""

import random
import json
import time
import yaml

import sys
sys.path.append('src')

from api_client import APIClient
from prompt_builder import PromptBuilder
from file_manager import FileManager
from quality.checker import QualityChecker
from tqdm import tqdm


class ReviewGenerator:
    """Main review generator with quality checks"""
    
    def __init__(self, config_path="config/config.yaml", verbose=True):
        self.verbose = verbose
        
        # Load config
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        self.api = APIClient()
        self.prompt_builder = PromptBuilder()
        self.file_manager = FileManager()
        self.quality = QualityChecker(self.config)
    
    def _select_random_config(self):
        """Select random persona, rating, and model"""
        persona = random.choices(
            self.config["personas"],
            weights=[p["weight"] for p in self.config["personas"]]
        )[0]
        
        rating = random.choices(
            list(self.config["rating_distribution"].keys()),
            weights=list(self.config["rating_distribution"].values())
        )[0]
        
        model = random.choices(
            self.config["models"],
            weights=[m["weight"] for m in self.config["models"]]
        )[0]
        
        return persona, rating, model
    
    def generate_one_raw(self, force_bad=False):
        """Generate one raw review"""
        persona, rating, model = self._select_random_config()
        
        # Build prompt
        if force_bad:
            prompt = self.prompt_builder.build_bad_prompt()
        else:
            prompt = self.prompt_builder.build_good_prompt(persona, rating)
        
        # Call API
        text = self.api.generate(model["provider"], model["model"], prompt)
        
        # Parse response
        text = text.strip().replace("```json", "").replace("```", "")
        data = json.loads(text)
        
        # Build review object
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
            "model": f"{model['provider']}/{model['model']}",
            "persona": persona['type'],
            "persona_keywords": persona.get("keywords", [])
        }
    
    def generate_one_with_quality(self, existing_reviews, review_index):
        """Generate one review with quality checks"""
        max_retries = self.config['quality_thresholds']['max_regeneration_attempts']
        force_bad_first = (random.random() < 0.10)
        
        for attempt in range(1, max_retries + 1):
            start = time.time()
            
            try:
                review = self.generate_one_raw(force_bad=(force_bad_first and attempt == 1))
                gen_time = round(time.time() - start, 2)
                
                # Quality check
                result = self.quality.check_all(review, existing_reviews)
                passed = result["passed"]
                failed_metric = result.get("failed_metric", "")
                
                # Log attempt
                self.file_manager.log_attempt(
                    review_index, attempt, review, passed, failed_metric, gen_time
                )
                
                if passed:
                    return review
            
            except Exception as e:
                self.file_manager.log_attempt(
                    review_index, attempt, {"model": "error", "title": "ERROR"}, 
                    False, "exception", 0
                )
        
        return None
    
    def generate_all(self, count=400):
        """Generate full dataset"""
        final_reviews = []
        clean_reviews = []
        
        # Generate reviews
        for i in tqdm(range(count), desc="Generating", disable=not self.verbose):
            review = self.generate_one_with_quality(final_reviews, review_index=i)
            
            if review:
                final_reviews.append(review)
                clean_reviews.append({
                    "rating": review["rating"],
                    "review_text": review["review_text"],
                    "title": review["title"],
                    "pros": review["pros"],
                    "cons": review["cons"]
                })
        
        # Save results
        paths = self.file_manager.save_reviews(final_reviews, clean_reviews)
        
        return {
            **paths,
            'timestamp': self.file_manager.timestamp,
            'success_count': len(clean_reviews),
            'skipped_count': count - len(clean_reviews)
        }