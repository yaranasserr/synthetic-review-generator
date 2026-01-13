import csv
import json
from pathlib import Path
from datetime import datetime


class ReviewStorage:
    def __init__(self, base_dir="data/synthetic"):
        self.base = Path(base_dir)
        self.reviews_dir = self.base / "reviews"
        self.models_dir = self.base / "reviews_models"
        self.logs_dir = self.base / "logs"
        
        # Create directories
        for d in [self.reviews_dir, self.models_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp for this run
        self.run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
     
        self.log_file = self.logs_dir / f"generation_log_{self.run_timestamp}.csv"
        self._init_log()
    
    def _init_log(self):
        """Initialize CSV log file with headers"""
        if not self.log_file.exists():
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'review_index',
                    'attempt',
                    'model',
                    'title',
                    'passed',
                    'failed_metric',
                    'generation_time_sec',
                    'rating',
                    'word_count',
                    'low_quality_forced',
                    'review_passed_quality'
                ])
    
    def get_output_paths(self):
        """Get timestamped output file paths for this run"""
        return {
            'all_reviews': self.reviews_dir / f"reviews_{self.run_timestamp}.json",
            'by_model': self.models_dir / f"reviews_by_model_{self.run_timestamp}.json"
        }
    
    def save_all_reviews(self, reviews):
        """Save all reviews to single timestamped JSON file"""
        paths = self.get_output_paths()
        
        # Save all reviews
        with open(paths['all_reviews'], 'w') as f:
            json.dump(reviews, f, indent=2)
        
        # Group by model and save
        by_model = {}
        for review in reviews:
            model_key = review.get('model', 'unknown')
            provider = review.get('provider', 'unknown')
            full_key = f"{provider}/{model_key}"
            
            if full_key not in by_model:
                by_model[full_key] = []
            by_model[full_key].append(review)
        
        with open(paths['by_model'], 'w') as f:
            json.dump(by_model, f, indent=2)
        
        return paths
    
    def log_attempt(self, index, attempt, review_data, passed, failed_metric=None, 
                   generation_time=0, low_quality_forced=False):
        """Log each generation attempt to CSV"""
        timestamp = datetime.now().isoformat()
        
        # Extract data safely
        model = review_data.get('model', 'unknown')
        provider = review_data.get('provider', 'unknown')
        full_model = f"{provider}/{model}"
        
        title = review_data.get('title', 'N/A')
        rating = review_data.get('rating', 0)
        
        review_text = review_data.get('review_text', '')
        word_count = len(review_text.split()) if review_text else 0
        
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                index,
                attempt,
                full_model,
                title,
                passed,
                failed_metric if failed_metric else '',
                round(generation_time, 2),
                rating,
                word_count,
                low_quality_forced,
                passed
            ])