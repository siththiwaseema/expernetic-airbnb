# Bangkok Airbnb Market Intelligence
### Expernetic Data Engineer Intern — Technical Assignment
**Dataset:** Inside Airbnb — Bangkok, Thailand  
**Candidate:** [Your Full Name]  
**Submission Date:** July 2026

---

## Project Overview

This project implements a full data engineering and analytics pipeline on the 
Bangkok Inside Airbnb dataset, transforming raw public data into actionable 
market intelligence. The analysis covers 31,069 listings, 11.3 million calendar 
records, and 693,558 guest reviews across 50 Bangkok neighbourhoods.

---

## Repository Structure

expernetic-airbnb/
├── data/
│   ├── raw/              ← Downloaded Inside Airbnb files (not tracked in git)
│   └── processed/        ← Cleaned and enriched outputs
├── notebooks/
│   ├── 03_eda.ipynb                    ← Exploratory Data Analysis
│   ├── 04_statistical_analysis.ipynb   ← Hypothesis testing & regression
│   ├── 05_ml_models.ipynb              ← Price prediction & clustering
│   └── 06_ai_llm.ipynb                 ← Sentiment analysis & LLM insights
├── src/
│   ├── ingest.py         ← Data ingestion pipeline
│   ├── clean.py          ← Data cleaning & standardization
│   ├── enrich.py         ← Data enrichment & joins
│   ├── model.py          ← Star schema & DuckDB modeling
│   └── utils.py          ← Shared utilities & path config
├── reports/              ← Charts, maps, PDF report, LLM insights
├── db/                   ← DuckDB database
├── requirements.txt
└── README.md

---

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/siththiwaseema/expernetic-airbnb.git
cd expernetic-airbnb
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Download Bangkok Dataset
Go to https://insideairbnb.com/get-the-data/ and download these files 
for **Bangkok, Thailand** into `data/raw/`:

| File | Description |
|------|-------------|
| `listings.csv.gz` | Core listing data |
| `listings.csv` | Detailed listing attributes |
| `calendar.csv.gz` | Daily availability data |
| `reviews.csv.gz` | Full guest reviews |
| `reviews.csv` | Review summary metrics |
| `neighbourhoods.csv` | Neighbourhood names |
| `neighbourhoods.geojson` | Neighbourhood boundaries |

### 5. Run the Full Pipeline
Run in this exact order:

```bash
# Step 1: Ingest & extract all files
python -m src.ingest

# Step 2: Clean & standardize
python -m src.clean

# Step 3: Enrich & join datasets
python -m src.enrich

# Step 4: Build star schema in DuckDB
python -m src.model
```

### 6. Run Notebooks
Launch Jupyter and run notebooks in order:

```bash
jupyter notebook
```

| Order | Notebook | Section |
|-------|----------|---------|
| 1 | `03_eda.ipynb` | Exploratory Data Analysis |
| 2 | `04_statistical_analysis.ipynb` | Statistical Analysis |
| 3 | `05_ml_models.ipynb` | ML Price Prediction & Clustering |
| 4 | `06_ai_llm.ipynb` | Sentiment Analysis & LLM Insights |

---

## What Was Built

### Section 2 — Dataset Familiarization
- Full schema documentation across all 7 files
- Primary/foreign key mapping
- Data limitations and assumptions documented

### Section 3 — Data Engineering Pipeline
- Repeatable ingestion pipeline with logging and skip-if-exists logic
- Price parsing, date standardization, boolean normalization
- Master enriched table: 31,069 listings × 115 columns
- Star schema in DuckDB: `fact_listings` + 4 dimension tables
- 6 analytical SQL queries with business interpretations
- Derived fields: occupancy rate, estimated annual revenue,
  host tenure, price per bedroom, review frequency

### Section 4 — Exploratory Data Analysis
- 8 professional visualizations saved to `reports/`
- Price distributions, neighbourhood analysis, host power law
- Interactive Folium map of listing density by neighbourhood
- Superhost performance comparison
- Every chart accompanied by business interpretation

### Section 5 — Statistical Analysis
- 5 formal hypothesis tests with null/alternative hypotheses:
  - H1: Entire home vs private room prices (Mann-Whitney U)
  - H2: Superhost vs regular host review scores (Mann-Whitney U)
  - H3: High vs low review count listings prices (Mann-Whitney U)
  - H4: Price differences across neighbourhoods (ANOVA)
  - H5: Weekend vs weekday occupancy (Mann-Whitney U)
- Effect sizes reported (Cohen's d, eta-squared, rank-biserial r)
- Correlation matrix across key numerical features
- OLS regression on log-transformed price

### Section 6 — Data Science & ML
- Feature engineering: amenity flags, categorical encoding
- Three model comparison: Ridge, Random Forest, Gradient Boosting
- Cross-validated metrics: MAE, RMSE, R², MAPE
- Feature importance analysis
- Residual analysis
- K-Means clustering with elbow + silhouette optimisation
- 4 distinct listing segment profiles

### Section 7 — AI & LLM
- VADER sentiment analysis on 50,000 reviews
- Sentiment vs review score correlation
- LDA topic modeling (6 topics from 10,000 reviews)
- Word frequency analysis by sentiment class
- Review volume trend (2015–2026) with COVID-19 impact
- LLM-powered insight generation (Anthropic Claude API architecture)

---

## Key Findings

| Finding | Insight |
|---------|---------|
| Avg occupancy rate | 24.1% across all listings |
| Priciest neighbourhood | Parthum Wan (median ฿2,652/night) |
| Weekday vs weekend | Weekday occupancy significantly higher — business travel market |
| Superhost advantage | 28.3% occupancy vs 21.9% for regular hosts |
| Market concentration | Power law dynamics — few hosts control majority of listings |
| Best ML model | Gradient Boosting outperforms linear and RF models |
| Review sentiment | 80%+ positive — rating inflation confirmed |
| COVID impact | Near-complete collapse 2020–2021, strong recovery by 2023 |

---

## Tech Stack

| Category | Tools |
|----------|-------|
| Language | Python 3.12 |
| Data Processing | pandas, numpy |
| Database | DuckDB |
| Visualization | matplotlib, seaborn, plotly, folium |
| ML & Statistics | scikit-learn, statsmodels, scipy |
| NLP | NLTK (VADER), TextBlob, sklearn LDA |
| Notebooks | Jupyter |
| Version Control | Git, GitHub |

---

## Artifacts Review Order

Reviewers should examine artifacts in this order:

1. `src/` — pipeline source code
2. `notebooks/03_eda.ipynb` — EDA findings
3. `notebooks/04_statistical_analysis.ipynb` — hypothesis tests
4. `notebooks/05_ml_models.ipynb` — ML models
5. `notebooks/06_ai_llm.ipynb` — NLP & AI work
6. `reports/` — all saved figures and LLM insights
7. `db/airbnb_bangkok.duckdb` — star schema
8. `reports/[PDF Report]` — full written report

---

## AI Tools Used

This project used Claude (Anthropic) as an AI coding assistant.
Full disclosure is documented in the PDF report Appendix A.

---

## Sections Not Completed

- **Section 8 (Open Innovation)** — deprioritized in favour of depth
  in core sections
- **Section 9 (City Selection Guide)** — reference guide only, no tasks
- **Multi-city analysis** — single city chosen for analytical depth
  over breadth as recommended in the assignment brief


## Candidate Information

- **Name:** Siththi Waseema
- **GPA/Results:** Academic results currently pending, will be shared
  upon release
- **Available Start Date:** 27th of July 2026
- **Onsite Flexibility:** Yes


*Submitted for Expernetic (Pvt) Ltd — Data Engineer Intern Assessment*