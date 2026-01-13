import yaml
from pathlib import Path
import random

def load_config(config_path="config/config.yaml"):
   
    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate required fields
    required = ['domain', 'target_count', 'personas', 'rating_distribution', 
                'models', 'quality_thresholds', 'review_length']
    
    for field in required:
        if field not in config:
            raise ValueError(f"Missing required config field: {field}")
    
    return config


def get_model_by_weight(config):
    models = config['models']
    weights = [m['weight'] for m in models]
    
    selected = random.choices(models, weights=weights, k=1)[0]
    return selected


def get_persona_by_weight(config):
    personas = config['personas']
    weights = [p['weight'] for p in personas]
    
    selected = random.choices(personas, weights=weights, k=1)[0]
    return selected


def get_rating_by_distribution(config):
    dist = config['rating_distribution']
    ratings = list(dist.keys())
    weights = list(dist.values())
    
    selected = random.choices(ratings, weights=weights, k=1)[0]
    return selected