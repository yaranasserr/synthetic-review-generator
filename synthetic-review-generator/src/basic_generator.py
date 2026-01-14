import random
import json
import os
import yaml
from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()


class ReviewGenerator:
    
    def __init__(self):
        # Load config
        with open('config/config.yaml', 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Setup APIs
        self.openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    def generate_one(self):
        """Generate one review"""
        # Pick random stuff
        persona = random.choices(self.config['personas'], weights=[p['weight'] for p in self.config['personas']])[0]
        rating = random.choices(list(self.config['rating_distribution'].keys()), weights=list(self.config['rating_distribution'].values()))[0]
        model = random.choices(self.config['models'], weights=[m['weight'] for m in self.config['models']])[0]
        
        # Prompt
        prompt = f"""Write a GitLab review from a {persona['description']}.
Rating: {rating}/5
Length: 50-150 words
JSON format: {{"title": "...", "pros": "...", "cons": "..."}}"""
        
        # Call API
        provider = model['provider']
        
        try:
            if provider == "openai":
                text = self.openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8,
                    response_format={"type": "json_object"}
                ).choices[0].message.content
            
            elif provider == "anthropic":
                text = self.anthropic.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=500,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                ).content[0].text
            
            else:
                raise ValueError(f"Unknown provider: {provider}")
            
            # Parse
            text = text.strip().replace('```json', '').replace('```', '').strip()
            data = json.loads(text)
            
            return {
                "rating": float(rating),
                "review_text": f"{data['title']}. Pros: {data['pros']} Cons: {data.get('cons', '')}".strip(),
                "title": data['title'],
                "pros": data['pros'],
                "cons": data.get('cons', ''),
                "model": f"{provider}/{model['model']}"
            }
        
        except Exception as e:
            print(f"\nError with {provider}: {e}")
            raise
    
    def generate_all(self, count=400):
        """Generate all reviews"""
        reviews_with_model = []
        reviews_without_model = []
        
        print(f"Generating {count} reviews...")
        for i in tqdm(range(count)):
            try:
                review = self.generate_one()
                
                reviews_with_model.append(review)
                review_clean = {
                    "rating": review["rating"],
                    "review_text": review["review_text"],
                    "title": review["title"],
                    "pros": review["pros"],
                    "cons": review["cons"]
                }
                reviews_without_model.append(review_clean)
                
            except Exception as e:
                print(f"\nError on review {i+1}: {e}")
                continue
        
     
        os.makedirs('data/synthetic', exist_ok=True)
        with open('data/synthetic/generated_reviews_with_models.json', 'w') as f:
            json.dump(reviews_with_model, f, indent=2)
        
      
        with open('data/synthetic/generated_reviews.json', 'w') as f:
            json.dump(reviews_without_model, f, indent=2)
        
      


# Run
if __name__ == "__main__":
    gen = ReviewGenerator()
    gen.generate_all(500)