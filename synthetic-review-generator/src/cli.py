import argparse
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

import sys
sys.path.append('src')

from utils.config import load_config, get_model_by_weight, get_persona_by_weight, get_rating_by_distribution
from generator.core import RawReviewGenerator
from generator.pipeline import GenerationPipeline
from generator.storage import ReviewStorage


def save_checkpoint(reviews, checkpoint_path):
    """Save checkpoint"""
    with open(checkpoint_path, 'w') as f:
        json.dump(reviews, f, indent=2)
    print(f"\n💾 Checkpoint saved: {checkpoint_path}")


def main():
    # Load environment
    load_dotenv()
    
    # Verify API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in .env")
        return
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not found in .env")
        return
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Generate synthetic reviews')
    parser.add_argument('--config', default='config/config.yaml', help='Config file path')
    parser.add_argument('--count', type=int, help='Number of reviews (overrides config)')
    args = parser.parse_args()
    
    # Load config
    print("📋 Loading configuration...")
    config = load_config(args.config)
    
    target_count = args.count if args.count else config['target_count']
    
    # Create storage
    storage = ReviewStorage()
    
    # Create pipeline
    pipeline = GenerationPipeline(config, storage)
    
    # Storage
    generated_reviews = []
    rejected_reviews = []
    
    checkpoint_dir = Path(config['output']['checkpoint_dir'])
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_interval = config['checkpointing']['interval']
    
    print(f"🎯 Target: {target_count} reviews")
    print(f"📊 Models: {len(config['models'])} configured")
    print(f"👥 Personas: {len(config['personas'])} types")
    print(f"💾 Checkpoints every {checkpoint_interval} reviews")
    print(f"📁 Run timestamp: {storage.run_timestamp}\n")
    
    # Generate reviews
    for i in tqdm(range(target_count), desc="Generating"):
        # Select model, persona, rating
        model_config = get_model_by_weight(config)
        persona = get_persona_by_weight(config)
        rating = get_rating_by_distribution(config)
        
        generator = RawReviewGenerator(model_config)
        
        try:
            review = pipeline.generate_one(generator, persona, rating, index=i)
            generated_reviews.append(review)
            
        except Exception as e:
            rejected_reviews.append({
                'index': i,
                'persona': persona['type'],
                'rating': rating,
                'model': model_config['model'],
                'error': str(e)
            })
        
        # Checkpoint
        if (i + 1) % checkpoint_interval == 0:
            checkpoint_path = checkpoint_dir / f"checkpoint_{storage.run_timestamp}_{i+1}.json"
            save_checkpoint(generated_reviews, checkpoint_path)
    
    # Save final outputs
    print(f"\n💾 Saving {len(generated_reviews)} reviews...")
    
    paths = storage.save_all_reviews(generated_reviews)
    
    # Save rejected reviews
    rejected_path = None
    if rejected_reviews:
        rejected_path = Path(config['output']['rejected_reviews'])
        rejected_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Add timestamp to rejected filename
        rejected_path = rejected_path.parent / f"rejected_{storage.run_timestamp}.json"
        with open(rejected_path, 'w') as f:
            json.dump(rejected_reviews, f, indent=2)
    
    # Stats
    print(f"\n{'='*60}")
    print(f"✅ Generation Complete")
    print(f"{'='*60}")
    print(f"Generated: {len(generated_reviews)}")
    print(f"Rejected: {len(rejected_reviews)}")
    print(f"Success rate: {len(generated_reviews)/target_count*100:.1f}%")
    print(f"\n📁 All reviews: {paths['all_reviews']}")
    print(f"📁 By model: {paths['by_model']}")
    print(f"📁 CSV log: data/synthetic/logs/generation_log.csv")
    if rejected_path:
        print(f"📁 Rejected: {rejected_path}")


if __name__ == "__main__":
    main()