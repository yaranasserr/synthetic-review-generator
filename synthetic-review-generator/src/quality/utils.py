
import json


def load_reviews(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)


def tokenize(text):
    return text.lower().split()


def jaccard_similarity(set1, set2):
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0