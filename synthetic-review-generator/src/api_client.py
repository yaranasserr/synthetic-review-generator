
import os
from openai import OpenAI
from anthropic import Anthropic


class APIClient:
    
    def __init__(self):
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    def generate(self, provider, model, prompt):
        if provider == "openai":
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        
        elif provider == "anthropic":
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=400,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
    