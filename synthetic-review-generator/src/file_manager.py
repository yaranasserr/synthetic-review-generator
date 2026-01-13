"""File management and CSV logging"""

import os
import json
import csv
from datetime import datetime


class FileManager:
    """Handle file I/O and CSV logging"""
    
    def __init__(self, timestamp=None):
        self.timestamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Setup directories
        self.base_dir = "data/synthetic"
        self.logs_dir = os.path.join(self.base_dir, "logs")
        self.reviews_dir = os.path.join(self.base_dir, "reviews")
        self.models_dir = os.path.join(self.base_dir, "reviews_models")
        
        for directory in [self.logs_dir, self.reviews_dir, self.models_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # CSV log file
        self.csv_file = os.path.join(
            self.logs_dir, f"generation_log_{self.timestamp}.csv"
        )
        self._init_csv()
    
    def _init_csv(self):
        """Initialize CSV log with headers"""
        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "review_index", "attempt", "model",
                "title", "rating", "word_count", "passed",
                "failed_metric", "generation_time_sec"
            ])
    
    def log_attempt(self, review_index, attempt, review, passed, failed_metric, gen_time):
        """Log a generation attempt to CSV"""
        with open(self.csv_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                review_index,
                attempt,
                review.get("model", "error"),
                review.get("title", "ERROR")[:50],
                review.get("rating", 0),
                len(review.get("review_text", "").split()),
                passed,
                failed_metric,
                gen_time
            ])
    
    def save_reviews(self, final_reviews, clean_reviews):
        """Save generated reviews to JSON files"""
        with_models_path = f"{self.models_dir}/reviews_with_models_{self.timestamp}.json"
        clean_path = f"{self.reviews_dir}/reviews_clean_{self.timestamp}.json"
        
        with open(with_models_path, "w") as f:
            json.dump(final_reviews, f, indent=2)
        
        with open(clean_path, "w") as f:
            json.dump(clean_reviews, f, indent=2)
        
        return {
            'clean_path': clean_path,
            'with_models_path': with_models_path,
            'csv_log': self.csv_file
        }