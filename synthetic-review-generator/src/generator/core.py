import json
import time
import os
from openai import OpenAI
from anthropic import Anthropic


class RawReviewGenerator:
    def __init__(self, model_config):
        """
        model_config should have: provider, model, temperature
        """
        self.provider = model_config['provider']
        self.model = model_config['model']
        self.temperature = model_config.get('temperature', 0.8)
        
        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found")
            self.client = OpenAI(api_key=api_key)
        
        elif self.provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found")
            self.client = Anthropic(api_key=api_key)
        
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _build_prompt(self, persona, rating):
        """Build prompt based on persona and rating"""
        keywords = ", ".join(persona.get('keywords', []))
        
        prompt = (
            "You must output ONLY valid JSON. No markdown. No explanation.\n\n"
            f"Write a realistic GitLab review from a {persona['type'].replace('_', ' ')}.\n"
            f"Rating: {rating} stars\n"
            f"Perspective: {persona['description']}\n"
            f"Try to naturally include terms like: {keywords}\n\n"
            "Write a detailed, authentic review with specific examples.\n\n"
            'Output format:\n'
            '{"title": "string", "pros": "string", "cons": "string"}'
        )
        return prompt

    def generate(self, persona, rating):
        """Generate a review for given persona and rating"""
        prompt = self._build_prompt(persona, rating)
        
        start = time.time()
        
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                )
                text = response.choices[0].message.content.strip()
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    temperature=self.temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                text = response.content[0].text.strip()
            
            duration = time.time() - start
            
            # Clean up markdown if present
            if text.startswith("```"):
                text = text.strip("`")
                if text.startswith("json"):
                    text = text[4:].strip()
            
            # Parse JSON
            data = json.loads(text)
            
            # Combine into review_text
            review_text = f"{data['title']}. Pros: {data['pros']} Cons: {data['cons']}"
            
            # Find which persona keywords appear in the review
            persona_keywords = []
            review_lower = review_text.lower()
            for keyword in persona.get('keywords', []):
                if keyword.lower() in review_lower:
                    persona_keywords.append(keyword)
            
            # Build final review object
            review = {
                'rating': rating,
                'review_text': review_text,
                'title': data['title'],
                'pros': data['pros'],
                'cons': data['cons'],
                'model': f"{self.provider}/{self.model}",
                'persona': persona['type'],
                'persona_keywords': persona_keywords,
                'provider': self.provider
            }
            
            return review, duration
        
        except Exception as e:
            raise ValueError(f"Generation failed: {e}")