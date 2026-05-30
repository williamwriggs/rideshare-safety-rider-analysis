# Rideshare Safety Rider Analysis

This repository contains a starter analysis workflow for comparing safety, trust, and rider-experience narratives across human-driven rideshare services and autonomous ridehail services, with an initial focus on Uber and Waymo in San Francisco.

The current dataset is **simulated**. It is intended to demonstrate the workflow, visualizations, and research concept before live data collection or validated public-data ingestion. Do not treat the included CSV as observed rider sentiment or verified incident data.

## Project idea

The working research question is: how can publicly available rider narratives, incident reports, and geospatial indicators help identify differences in perceived safety, trust, and service-design needs between autonomous and human-driven mobility services?

The prototype supports scenario tagging, sentiment scoring, comparison of Waymo and Uber scenario mentions, a Streamlit dashboard for mapping and filtering records, and scraper templates that can be adapted to compliant data sources and APIs.

## Repository structure

```text
.
├── data/
│   └── simulated_sentiment_scenario_data.csv
├── docs/
│   └── paper_concept.md
├── src/
│   ├── analyze_scenarios.py
│   ├── av_safety_dashboard.py
│   └── scrape_template.py
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/analyze_scenarios.py
streamlit run src/av_safety_dashboard.py
```

## Data status

The included CSV is synthetic and should be used for demonstration only. A publication-ready version of this project should replace or supplement the simulated data with documented, reproducible sources such as public safety reports, public CPUC or DMV records where applicable, app-store reviews where collection is allowed, survey or intercept data, compliant API-derived public posts, or manually coded incident narratives.

## Research and ethics notes

Scraping should comply with source terms of service, platform API rules, privacy expectations, and institutional review requirements. Publicly visible text can still create human-subjects, privacy, and reputational risks when aggregated, geocoded, or combined with other data.

Recommended safeguards include avoiding handles, names, account IDs, and precise locations unless necessary; aggregating to neighborhoods, ZIP codes, census tracts, or hex bins; documenting collection dates, APIs, filters, and rate limits; distinguishing verified incidents from anecdotal claims; and reporting uncertainty and sampling bias clearly.

## Working paper direction

A potential paper can use this repository as a reproducible methods appendix for a study on “data in the wild,” perceived safety, and AV trust. The strongest contribution is likely not a claim that AVs are categorically safer or less safe based on scraped sentiment, but rather a framework for identifying where rider experience, safety communication, and service design diverge across automated and human-driven mobility.
