# Synthetic Review Generator - Project Plan

## Project Overview

Build a synthetic data generator for GitLab reviews with quality guardrails. Generate synthetic reviews using multiple LLM providers and validate them against 50 real reviews from [G2](https://www.g2.com/products/gitlab/reviews).



### Data Collection & Generation Core
- Collect real reviews from G2 
- Build generator core with API integrations
- Implement basic prompt templates
- Test generation with 50 sample reviews

### Quality System & Full Generation
- Implement quality metrics (diversity, semantic, sentiment)
- Add auto-rejection and regeneration logic
- Generate full 500-review dataset
- Build comparison module

###  Integration & Documentation
- Create CLI interface
- Generate quality report


---

## Part 1: Data Collection

**Data Source:** https://www.g2.com/products/gitlab/reviews

**Output:** 50 real GitLab reviews in JSON format

**Data Structure:**
```
{
  "rating": 5.0,
  "review_text": "Combined title, pros, and cons",
  "title": "Review title",
  "pros": "Positive aspects",
  "cons": "Negative aspects"
}
```


---

## Part 2: Data Generator

### Method: Direct LLM API Calls

**Approach:** Simple API wrapper for three providers

**Models:**
- OpenAI: gpt-4o-mini
- Anthropic: claude-sonnet-4 


**Why This Method:**
- Simple to implement and debug
- Easy to switch between providers
- Direct control over prompts
- No framework overhead
- Fast development time

**Configuration:**
- YAML-based config file
- Configurable personas (5 types)
- Rating distribution (matches real data)
- Review length targets
- Quality thresholds

**Personas:**
1. Backend Developer (25%)
2. DevOps Engineer (25%)
3. Project Manager (20%)
4. Frontend Developer (15%)
5. Team Lead (15%)

---

## Part 3: Quality Guardrails

### Hybrid System Approach

#### Metric 1: Diversity (Vocabulary Overlap)
**Tool:** Python sets + Jaccard similarity

**Method:**
- Calculate word overlap between reviews
- Compute unique vocabulary ratio
- Compare against thresholds

**Threshold:** Max 75% Jaccard similarity

**Why:** Fast, deterministic, no API costs

#### Metric 2: Semantic Similarity
**Tool:** sentence-transformers library

**Method:**
- Generate embeddings for each review
- Calculate cosine similarity
- Identify near-duplicates

**Threshold:** Max 85% semantic similarity

**Why:** Proven approach, runs locally, catches paraphrased duplicates

#### Metric 3: Bias Detection
**Tool:** transformers sentiment pipeline

**Method:**
- Analyze sentiment distribution
- Compare against expected ratios
- Detect unrealistic patterns

**Threshold:** Within 15% of expected distribution

**Why:** Standard NLP tool, efficient, reliable

#### Metric 4: Domain Realism
**Tool:** LLM-as-judge (single API call)

**Method:**
- Use cheaper model to evaluate realism
- Check for GitLab-specific terminology
- Verify natural language patterns

**Threshold:** Minimum score of 7/10

**Why:** LLMs excel at subjective quality assessment

### Auto-Rejection Logic
- Check metrics in order (fast to slow)
- Regenerate failed reviews up to 3 times
- Track rejection rates per model
- Log all quality scores

---

## Part 4: Comparison System

### Approach: Statistical Analysis

**Method:** Apply same metrics to both datasets

**Comparisons:**
1. Vocabulary diversity (synthetic vs real)
2. Semantic similarity patterns
3. Sentiment distribution
4. Rating distribution
5. Review length statistics
6. Common phrase analysis

**Output:** Side-by-side metrics showing similarity

**Validation:** Synthetic reviews should be statistically indistinguishable from real reviews

---

## Part 5: CLI & Quality Report

### CLI Interface

**Command:**
```
python generate.py --config config.yaml --output reviews.json
```

**Features:**
- Progress tracking
- Real-time statistics
- Error handling
- Configurable parameters

**Implementation:**
- argparse for argument parsing
- PyYAML for config loading
- tqdm for progress bars

### Quality Report

**Format:** Markdown file

**Sections:**
1. Dataset Overview
   - Total reviews generated
   - Generation time
   - API costs
   - Model distribution

2. Model Performance
   - Reviews per model
   - Average generation time
   - Rejection rates
   - Quality scores

3. Quality Metrics
   - Vocabulary diversity
   - Semantic similarity
   - Sentiment distribution
   - Domain realism scores

4. Synthetic vs Real Comparison
   - Rating distributions
   - Length statistics
   - Vocabulary overlap
   - Statistical similarity

5. Sample Reviews
   - 3 synthetic examples
   - 3 real examples for comparison

6. Observations & Recommendations

---





## Design Decisions

### 1. Direct API Calls vs Agent Framework
**Decision:** Direct API calls

**Reasoning:**
- Simpler implementation
- Faster development
- Easier debugging
- No framework learning curve
- Sufficient for task requirements

### 2. Hybrid Quality System
**Decision:** Mix of traditional ML and LLM judging

**Reasoning:**
- Traditional metrics (Jaccard, embeddings) are fast and free
- LLMs only used where subjective judgment needed
- Reduces API costs significantly
- More reliable than pure LLM evaluation

### 3. Rating Distribution
**Decision:** Slightly adjusted from real data

**Reasoning:**
- Real data heavily skewed (60% 5-star)
- Added more variety (55% 5-star, 25% 4-star)
- More realistic for evaluation
- Still maintains positive sentiment



Design Decisions
1. Direct API Calls vs Agent Framework
Decision: Direct API calls
Reasoning:

Simpler implementation
Faster development
Easier debugging
No framework learning curve
Sufficient for task requirements

2. Hybrid Quality System
Decision: Mix of traditional ML and LLM judging
Reasoning:

Traditional metrics (Jaccard, embeddings) are fast and free
LLMs only used where subjective judgment needed
Reduces API costs significantly
More reliable than pure LLM evaluation

3. Rating Distribution
Decision: Slightly adjusted from real data
Reasoning:

Real data heavily skewed (60% 5-star)
Added more variety (55% 5-star, 25% 4-star)
More realistic for evaluation
Still maintains positive sentiment

4. Two Models Only
Decision: OpenAI + Anthropic only
Reasoning:

Assignment requires minimum 2 providers
Both are high-quality and reliable
Sufficient diversity for comparison
Avoid complexity of local model setup


Trade-offs
1. Speed vs Cost
Choice: Prioritize speed with paid APIs
Trade-off: Higher cost but faster generation (2-3 hours vs 8+ hours with free models)
Justification: 3-day deadline requires fast iteration
2. Quality vs Quantity
Choice: 400 reviews with strict quality checks
Trade-off: More rejections and regenerations, but higher quality output
Justification: Assignment emphasizes quality guardrails
3. Automation vs Control
Choice: Automated quality checks with thresholds
Trade-off: Less manual review, potential edge cases missed
Justification: Scalable approach, consistent evaluation
4. Exact Match vs Diversity
Choice: Don't exactly match real data distribution
Trade-off: Slightly different from source data
Justification: More realistic and diverse dataset for evaluation
