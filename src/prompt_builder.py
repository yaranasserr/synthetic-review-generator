"""Prompt construction for review generation"""

import random


class PromptBuilder:
    """Build prompts for review generation"""
    
    @staticmethod
    def build_good_prompt(persona, rating):
        """Build a good quality prompt"""
        keywords = ", ".join(persona.get('keywords', [])[:3])
        
        return f"""Write a GitLab review. Output ONLY valid JSON, no markdown.

Persona: {persona['type'].replace('_', ' ')}
Rating: {rating}/5 stars
Keywords: {keywords}

Keep SHORT - 50-150 words total.

Output: {{"title": "5-8 words", "pros": "30-70 words", "cons": "20-50 words"}}

Be specific, use examples."""
    
    @staticmethod
    def build_bad_prompt():
        """Build a deliberately bad prompt to test quality checks"""
        bad_type = random.choice(['too_short', 'generic', 'wrong_sentiment'])
        
        if bad_type == 'too_short':
            return 'Write a GitLab review in ONE sentence. Less than 10 words.\nOutput JSON: {"title": "...", "pros": "...", "cons": "..."}'
        
        elif bad_type == 'generic':
            return 'Write an extremely generic review. Use NO specific features.\nBe vague. Output JSON: {"title": "...", "pros": "...", "cons": "..."}'
        
        else:  # wrong_sentiment
            return 'Write a GitLab review with rating 5/5.\nBut write ONLY negative things. Output JSON: {"title": "...", "pros": "terrible", "cons": "bad"}'