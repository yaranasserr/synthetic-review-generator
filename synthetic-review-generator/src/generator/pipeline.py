import sys
sys.path.append('src')

from quality.checker import QualityChecker


class GenerationPipeline:
    def __init__(self, config, storage):
        self.config = config
        self.storage = storage
        self.quality_checker = QualityChecker(config)
        self.max_attempts = config['quality_thresholds']['max_regeneration_attempts']
        self.existing_reviews = []

    def generate_one(self, generator, persona, rating, index):
        """Generate one review with quality checks and logging"""
        attempts = 0
        
        while attempts < self.max_attempts:
            attempts += 1
            
            try:
                # Generate review
                review, duration = generator.generate(persona, rating)
                
                # Check quality
                quality_result = self.quality_checker.check_all(
                    review, 
                    self.existing_reviews
                )
                
                # Log this attempt
                self.storage.log_attempt(
                    index=index,
                    attempt=attempts,
                    review_data=review,
                    passed=quality_result['passed'],
                    failed_metric=quality_result.get('failed_metric'),
                    generation_time=duration,
                    low_quality_forced=False
                )
                
                if quality_result['passed']:
                    # Add to existing reviews for future checks
                    self.existing_reviews.append(review)
                    
                    return {
                        **review,
                        'attempts': attempts,
                        'time': round(duration, 2),
                        'quality_scores': quality_result.get('scores', {}),
                        'passed': True
                    }
                
                # If failed, log reason
                print(f"  Attempt {attempts} failed: {quality_result['failed_metric']}")
            
            except Exception as e:
                # Log failed attempt
                self.storage.log_attempt(
                    index=index,
                    attempt=attempts,
                    review_data={'model': generator.model, 'provider': generator.provider, 
                                'title': 'ERROR', 'rating': rating},
                    passed=False,
                    failed_metric='exception',
                    generation_time=0,
                    low_quality_forced=False
                )
                print(f"  Attempt {attempts} error: {e}")
        
        # Max attempts reached
        raise RuntimeError(f"Failed after {self.max_attempts} attempts")