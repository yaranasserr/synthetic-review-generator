# Synthetic Review Generator - Project Plan

## Project Overview

Build a synthetic data generator for GitLab reviews with quality guardrails. Generate 500 synthetic reviews using multiple LLM providers and validate them against 50 real reviews from G2.

---

## Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yaranasser/synthetic-review-generator.git
cd synthetic-review-generator
```

### 2. Create a Python Virtual Environment
```bash
python3 -m venv venv
```

### 3. Activate the Virtual Environment

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Windows (cmd):**
```cmd
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install Requirements
```bash
pip install --upgrade pip
pip install -r requirements.txt
```



### 5. Environment Variables

Set up your API keys in .env file


```bash
OPENAI_API_KEY="your_openai_key"
ANTHROPIC_API_KEY="your_anthropic_key"
```



### 6. Output Structure
```
data/
├── raw/
│   └── real_reviews.json
└── synthetic/
    ├── logs/
    │   └── generation_log_TIMESTAMP.csv
    ├── reviews/
    │   └── reviews_clean_TIMESTAMP.json
    └── reviews_models/
        └── reviews_with_models_TIMESTAMP.json

reports/
├── charts/
│   ├── rating_distribution.png
│   ├── word_count_distribution.png
│   └── ...
├── quality_report_TIMESTAMP.md
└── comparison_TIMESTAMP.md
```


---

## Development Phases

### Phase 1: [Data Collection](synthetic-review-generator/data/raw)
- Collected 50 real reviews from G2 as CSV
- Converted to JSON format with rating, title, pros, cons

### Phase 2: [Basic Generation (No Quality Checks)](synthetic-review-generator/src/basic_generator.py)
- Built core generator with OpenAI and Anthropic APIs
- Implemented persona-based prompts
- Generated initial reviews to test API integration

### Phase 3: [Quality Metrics Implementation](synthetic-review-generator/src/quality)
- Built length validation
- Implemented diversity checks (Jaccard similarity)
- Added semantic similarity (TF-IDF)
- Implemented bias detection (TextBlob)
- Added domain realism check (LLM-as-judge)

### Phase 4: [Generation with Quality Checks](synthetic-review-generator/src/generator.py)
- Integrated quality checker into generation pipeline
- Added auto-retry logic (max 3 attempts)
- Implemented CSV logging for all attempts
- Added 10% bad prompts to test retry system

### Phase 5: [Reports](synthetic-review-generator/src/reports.py) and [CLI](synthetic-review-generator/src/cli.py)
- Built comparison report (real vs synthetic)
- Built quality report from CSV logs
- Created unified CLI with subcommands

---

## Part 1: Data Collection

**Method:** Manual CSV export from G2

**Data Source:** https://www.g2.com/products/gitlab/reviews

**Output:** 50 real GitLab reviews in JSON format

**Data Structure:**
```json
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

**Models:**
- OpenAI: gpt-4o-mini (40%)
- OpenAI: gpt-3.5-turbo (20%)
- Anthropic: claude-sonnet-4 (40%)

**Personas:**
1. Backend Developer (25%)
2. DevOps Engineer (25%)
3. Project Manager (20%)
4. Frontend Developer (15%)
5. Team Lead (15%)

**Rating Distribution:**
- 5 stars: 30%
- 4.5 stars: 20%
- 4 stars: 15%
- 3.5-1 stars: 35%

**Review Length:** 25-200 words (avg ~88 words to match real data)

---

## Part 3: Quality Guardrails

### Metric 1: Length Validation
**Tool:** Python string operations  
**Threshold:** 25-200 words

### Metric 2: Diversity (Vocabulary Overlap)
**Tool:** Jaccard similarity  
**Threshold:** Max 75% word overlap

### Metric 3: Semantic Similarity
**Tool:** TF-IDF + cosine similarity  
**Threshold:** Max 85%

### Metric 4: Bias Detection
**Tool:** TextBlob sentiment  
**Threshold:** Sentiment within 15% of expected range for rating

### Metric 5: Domain Realism
**Tool:** LLM-as-judge (gpt-4o-mini)  
**Threshold:** Score ≥ 7/10

### Auto-Rejection Logic
- Check all metrics sequentially
- Regenerate up to 3 times on failure
- Log every attempt to CSV
- Skip review if max retries exceeded

---

## Part 4: Comparison System

**Method:** Statistical comparison

**Metrics:**
- Review counts
- Average/min/max ratings
- Average/min/max word counts
- Top words in titles

**Output:** Markdown report with side-by-side stats

---

## Part 5: CLI & Reports

### CLI Commands
```bash
# Generate reviews
python src/cli.py generate --count 400

# Generate with auto-reports
python src/cli.py generate --count 100 --with-reports --real-reviews data/raw/real_reviews.json

# Quality report only
python src/cli.py quality-report --csv data/synthetic/logs/generation_log_*.csv

# Comparison only
python src/cli.py compare --real data/raw/real_reviews.json --synthetic data/synthetic/reviews/reviews_clean_*.json

# Quiet mode
python src/cli.py generate --count 50 --quiet
```

### Quality Report Content
- Total attempts and passed reviews
- Success rate
- Average rating and word count
- Failed metrics breakdown

### Comparison Report Content
- Review counts
- Rating statistics
- Word count statistics
- Top title words

---

## Technical Architecture

### File Structure
```
src/
├── cli.py              # Unified CLI
├── generator.py        # Core logic
├── api_client.py       # API calls
├── prompt_builder.py   # Prompts
├── file_manager.py     # File I/O & CSV
├── reports.py          # Report generation
├── logger.py           # Logging (optional)
└── quality/            # Quality checks
    ├── checker.py
    ├── length.py
    ├── diversity.py
    ├── bias.py
    ├── realism.py
    └── utils.py
```

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



---

## Trade-offs


### 1. Quality vs Quantity
**Choice:** 500 reviews with strict quality checks  
**Trade-off:** More rejections and regenerations, but higher quality output  
**Justification:** Assignment emphasizes quality guardrails

### 2. Automation vs Control
**Choice:** Automated quality checks with thresholds  
**Trade-off:** Less manual review, potential edge cases missed  
**Justification:** Scalable approach, consistent evaluation

### 3. Exact Match vs Diversity
**Choice:** Don't exactly match real data distribution  
**Trade-off:** Slightly different from source data  
**Justification:** More realistic and diverse dataset for evaluation