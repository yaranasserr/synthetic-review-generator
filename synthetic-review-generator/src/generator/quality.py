def score_review(review: dict) -> float:
    score = 0.0

    if len(review["pros"].split()) > 10:
        score += 0.4
    if len(review["cons"].split()) > 10:
        score += 0.4
    if len(review["title"].split()) > 3:
        score += 0.2

    return round(score, 2)
