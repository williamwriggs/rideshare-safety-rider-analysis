# Rideshare Safety Rider Analysis

A research prototype exploring trust, safety, comfort, reliability, and rider experience in autonomous and human-driven mobility services.

## Live Application

https://rideshare-safety.streamlit.app/

Status: active research prototype.

## Project Overview

Traditional evaluations of autonomous vehicles often focus on crashes, disengagements, and technical performance. This project explores a complementary dimension of mobility: rider experience.

The repository provides a reproducible workflow for:

- scenario classification;
- sentiment analysis;
- geospatial visualization;
- trust and comfort assessment;
- comparative mobility-service evaluation;
- multi-source triangulation across simulated, public narrative, and rider research datasets.

The current implementation focuses on autonomous and human-driven ridehail services, with Waymo, Uber, Cruise, Tesla robotaxi/supervised autonomy, and related public narratives used as demonstration cases.

## Research Question

How can rider narratives, sentiment indicators, and geospatial analysis help identify trust, comfort, perceived safety, reliability, and operational-design issues in autonomous mobility services?

## Datasets

### Dataset A — Simulated Scenario Dataset

A synthetic demonstration dataset used to validate the workflow, dashboard, and analytical methods. This dataset should not be interpreted as observed rider behavior or verified incident evidence.

Files:

- `data/simulated_sentiment_scenario_data.csv`
- `data/simulated_sentiment_scenario_data_xy.csv`

### Dataset B — Public Narrative Dataset

A curated dataset of public narratives and public incident descriptions with documented XY coordinates. Records are paraphrased summaries tied to source URLs rather than scraped verbatim text.

File:

- `data/public_narratives_xy.csv`

### Dataset C — Research Rider Dataset

A structure for anonymized rider research data from surveys, interviews, or intercepts. This dataset is intended to support reviewer response, triangulation, and future publication.

Files:

- `data/research_rider_dataset.csv`
- `data/research_rider_dataset_template.csv`

### Qualitative Coding Note

The direct and indirect references reported in the paper are subsets of the 37 coded thematic references. This relationship is not capturable in the public database because its scenario classifications are mutually exclusive record-level categories developed for dashboard visualization and are analytically distinct from the multi-label qualitative coding reported in the paper.

## Live Dashboard Features

- Dataset selector
- Interactive maps
- Sentiment visualization
- Scenario filtering
- Comparative service analysis
- Geospatial clustering
- Multi-source trust and safety analysis

## Repository Structure

```text
.
├── data/
│   ├── simulated_sentiment_scenario_data.csv
│   ├── simulated_sentiment_scenario_data_xy.csv
│   ├── public_narratives_xy.csv
│   ├── research_rider_dataset.csv
│   └── research_rider_dataset_template.csv
├── docs/
│   ├── paper_concept.md
│   ├── deployment.md
│   └── data_dictionary.md
├── src/
│   ├── analyze_scenarios.py
│   ├── av_safety_dashboard.py
│   ├── create_geocoded_dataset.py
│   └── scrape_template.py
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/create_geocoded_dataset.py
python src/analyze_scenarios.py
streamlit run src/av_safety_dashboard.py
```

## Working Paper

**Mapping Trust and Safety in Urban Mobility from Data in the Wild: A Framework for Understanding Rider Experience in Autonomous and Human-Driven Mobility Services**

The paper examines how rider narratives and geospatial analysis can complement traditional AV safety metrics by identifying dimensions of trust, comfort, perceived safety, reliability, and service quality that are often overlooked in technical evaluations.

## Research Ethics

Any future collection of public narratives should comply with platform terms of service, privacy expectations, institutional review requirements, and applicable data-governance standards. Publicly available text can still create human-subjects, privacy, and reputational risks when aggregated, geocoded, or combined with other data.
