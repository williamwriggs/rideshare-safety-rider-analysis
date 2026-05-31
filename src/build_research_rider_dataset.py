from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = REPO_ROOT / "data" / "mapping-trust-and-safety.csv"
OUTPUT_PATH = REPO_ROOT / "data" / "research_rider_dataset.csv"

RIDER_COL = "Took Ride in AV (Rider vs. Non-rider)"
SURVEY_LAT_COL = "SurveyLatitude"
SURVEY_LON_COL = "Survey Longitude"
DROPOFF_COL = "Dropoff Location"
TRIP_MIN_COL = "About how long in minutes did your trip take? - Trip time in minutes (choose max duration if more than 60 minutes)"
TIME_COL = "About what time of day was the trip?"
PURPOSE_COL = "What was the primary purpose of the trip?\n(e.g. work, school, leisure, etc.) - Selected Choice"
ALT_MODE_COL = "Would you have made this trip otherwise? And if so how would you have made it?"
CHOICE_COL = "What are the top 3 factors that made you choose a Cruise autonomous vehicle over your other transportation options? - Selected Choice"
LATE_NIGHT_COL = "Does Cruise’s service change your ability to travel during overnight / late night hours? (If so can you tell us how.) - Selected Choice"
WTP_COL = "What is the max amount that you think you might have paid for the trip if it had not been free?"
IMPROVE_COL = "What could have improved your experience?"
VIEWS_CHANGED_COL = "Have your views on autonomous vehicles changed since participating in the research rider survey? If so, will you tell us how. - Selected Choice"
ZERO_EMISSION_COL = "Now having participated in the research rider study, what are your views on the importance of the following values for an autonomous vehicle ridesharing company? - Zero-emission vehicles"
ACCESSIBILITY_COL = "Now having participated in the research rider study, what are your views on the importance of the following values for an autonomous vehicle ridesharing company? - More service accessibility; including for non-ambulatory, blind/low vision, and deaf/hard of hearing riders"
DISTRIBUTION_COL = "Now having participated in the research rider study, what are your views on the importance of the following values for an autonomous vehicle ridesharing company? - Good distribution of service across city"
TRANSIT_COL = "Now having participated in the research rider study, what are your views on the importance of the following values for an autonomous vehicle ridesharing company? - Connectivity with transit"
SHARED_RIDE_COL = "What are your feelings on sharing the kind of ride you had with another passenger if the ride was          safe, reliable and cost effective?"
ATTRACTED_COL = "To start, what attracted you to this project? - Selected Choice"
PREVENTED_COL = "What prevented you from riding a Cruise vehicle? - Selected Choice"
ENCOURAGED_COL = "What would have encouraged           you to participate and take rides          ? - Selected Choice"

VALUE_SCORE = {
    "Not important": 1,
    "Slightly important": 2,
    "Somewhat important": 3,
    "Very important": 4,
    "Extremely important": 5,
}


def first_present(row: pd.Series, column: str) -> str:
    value = row.get(column, "")
    if pd.isna(value):
        return ""
    return str(value).strip()


def is_rider(value: str) -> bool:
    return "rider" in str(value).lower() and "non" not in str(value).lower()


def parse_dropoff_coordinates(value: str) -> tuple[float | None, float | None]:
    """Extract final lat/lon from Qualtrics-style Dropoff Location JSON-ish data."""
    if pd.isna(value) or not str(value).strip():
        return None, None

    text = str(value).strip()

    # Try JSON first.
    try:
        parsed = json.loads(text)
        candidates = []
        if isinstance(parsed, dict):
            candidates.append(parsed)
            for item in parsed.values():
                if isinstance(item, dict):
                    candidates.append(item)
        elif isinstance(parsed, list):
            candidates.extend([item for item in parsed if isinstance(item, dict)])
        for item in candidates:
            lat = item.get("lat") or item.get("latitude") or item.get("Latitude")
            lon = item.get("lng") or item.get("lon") or item.get("longitude") or item.get("Longitude")
            if lat is not None and lon is not None:
                return float(lat), float(lon)
    except Exception:
        pass

    # Fallback regex for coordinate-like strings.
    nums = re.findall(r"-?\d+\.\d+", text)
    floats = [float(n) for n in nums]
    lat_candidates = [n for n in floats if 37.0 <= n <= 38.0]
    lon_candidates = [n for n in floats if -123.0 <= n <= -121.0]
    if lat_candidates and lon_candidates:
        return lat_candidates[-1], lon_candidates[-1]

    return None, None


def as_float(value) -> float | None:
    if pd.isna(value):
        return None
    try:
        return float(value)
    except Exception:
        return None


def score_value(value: str) -> float | None:
    if not value:
        return None
    return VALUE_SCORE.get(value.strip())


def infer_scenario(row: pd.Series, rider: bool) -> str:
    choice = first_present(row, CHOICE_COL).lower()
    prevented = first_present(row, PREVENTED_COL).lower()
    encouraged = first_present(row, ENCOURAGED_COL).lower()
    improve = first_present(row, IMPROVE_COL).lower()
    combined = " ".join([choice, prevented, encouraged, improve])

    if any(term in combined for term in ["safe", "safety", "security"]):
        return "Safety/Trust"
    if any(term in combined for term in ["reliable", "reliability", "late", "overnight"]):
        return "Reliability/Late-Night Mobility"
    if any(term in combined for term in ["comfort", "comfortable"]):
        return "Comfort"
    if any(term in combined for term in ["transit", "bus", "train"]):
        return "Transit Connection"
    if rider:
        return "Rider Experience"
    return "Barrier to Riding"


def infer_sentiment(row: pd.Series, rider: bool) -> tuple[str, float]:
    views = first_present(row, VIEWS_CHANGED_COL).lower()
    late = first_present(row, LATE_NIGHT_COL).lower()
    choice = first_present(row, CHOICE_COL).lower()
    prevented = first_present(row, PREVENTED_COL).lower()

    score = 0.0
    if "yes" in views:
        score += 0.25
    if "yes" in late:
        score += 0.15
    if any(term in choice for term in ["safer", "comfortable", "reliable", "coolest", "fastest"]):
        score += 0.2
    if not rider and prevented:
        score -= 0.1

    if score > 0.1:
        return "Positive", round(score, 2)
    if score < -0.1:
        return "Negative", round(score, 2)
    return "Neutral", round(score, 2)


def build_public_safe_dataset(df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for idx, row in df.iterrows():
        rider_value = first_present(row, RIDER_COL)
        rider = is_rider(rider_value)

        if rider:
            lat, lon = parse_dropoff_coordinates(first_present(row, DROPOFF_COL))
            coordinate_method = "Final dropoff coordinate from anonymized Dropoff Location field"
            location_label = "Dropoff area"
        else:
            lat = as_float(row.get(SURVEY_LAT_COL))
            lon = as_float(row.get(SURVEY_LON_COL))
            coordinate_method = "SurveyLatitude and Survey Longitude fields"
            location_label = "Survey response area"

        if lat is None or lon is None:
            continue

        scenario = infer_scenario(row, rider)
        sentiment, sentiment_score = infer_sentiment(row, rider)

        text_summary = (
            f"respondent_group={'Rider' if rider else 'Non-rider'}; "
            f"purpose={first_present(row, PURPOSE_COL)}; "
            f"alternative={first_present(row, ALT_MODE_COL)}; "
            f"choice_factors={first_present(row, CHOICE_COL)}; "
            f"barriers={first_present(row, PREVENTED_COL)}; "
            f"encouragement={first_present(row, ENCOURAGED_COL)}; "
            f"late_night_change={first_present(row, LATE_NIGHT_COL)}; "
            f"views_changed={first_present(row, VIEWS_CHANGED_COL)}"
        )

        rows.append(
            {
                "record_id": f"RR-{len(rows) + 1:04d}",
                "Dataset": "Research Rider Dataset",
                "Source": "Anonymized rider/non-rider survey",
                "Service": "Cruise",
                "Respondent_Group": "Rider" if rider else "Non-rider",
                "Scenario": scenario,
                "Sentiment": sentiment,
                "Sentiment Score": sentiment_score,
                "Location": location_label,
                "Latitude": round(lat, 6),
                "Longitude": round(lon, 6),
                "X": round(lon, 6),
                "Y": round(lat, 6),
                "Coordinate_Method": coordinate_method,
                "Trip_Time_Minutes": first_present(row, TRIP_MIN_COL),
                "Time_of_Day": first_present(row, TIME_COL),
                "Trip_Purpose": first_present(row, PURPOSE_COL),
                "Alternative_Mode": first_present(row, ALT_MODE_COL),
                "Choice_Factors": first_present(row, CHOICE_COL),
                "Barrier_to_Riding": first_present(row, PREVENTED_COL),
                "Encouragement": first_present(row, ENCOURAGED_COL),
                "Late_Night_Travel_Change": first_present(row, LATE_NIGHT_COL),
                "Views_Changed": first_present(row, VIEWS_CHANGED_COL),
                "Max_WTP": first_present(row, WTP_COL),
                "Zero_Emission_Importance": first_present(row, ZERO_EMISSION_COL),
                "Accessibility_Importance": first_present(row, ACCESSIBILITY_COL),
                "Distribution_Importance": first_present(row, DISTRIBUTION_COL),
                "Transit_Connectivity_Importance": first_present(row, TRANSIT_COL),
                "Zero_Emission_Score": score_value(first_present(row, ZERO_EMISSION_COL)),
                "Accessibility_Score": score_value(first_present(row, ACCESSIBILITY_COL)),
                "Distribution_Score": score_value(first_present(row, DISTRIBUTION_COL)),
                "Transit_Connectivity_Score": score_value(first_present(row, TRANSIT_COL)),
                "Shared_Ride_View": first_present(row, SHARED_RIDE_COL),
                "Attraction_to_Project": first_present(row, ATTRACTED_COL),
                "Text_Summary": text_summary,
                "Privacy_Notes": "Derived public-safe record; raw open-ended responses omitted.",
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Could not find {INPUT_PATH}")

    raw = pd.read_csv(INPUT_PATH)
    output = build_public_safe_dataset(raw)
    output.to_csv(OUTPUT_PATH, index=False)

    print(f"Loaded {len(raw)} raw survey rows from {INPUT_PATH}")
    print(f"Wrote {len(output)} public-safe rows to {OUTPUT_PATH}")
    if "Respondent_Group" in output.columns:
        print(output["Respondent_Group"].value_counts().to_string())


if __name__ == "__main__":
    main()
