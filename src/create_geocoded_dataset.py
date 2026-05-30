from __future__ import annotations

import hashlib
import math
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATHS = [
    REPO_ROOT / "data" / "simulated_sentiment_scenario_data.csv",
    REPO_ROOT / "simulated_sentiment_scenario_data.csv",
]
OUTPUT_PATH = REPO_ROOT / "data" / "simulated_sentiment_scenario_data_xy.csv"

# Approximate neighborhood centroids used only for prototype visualization.
# Replace with observed coordinates or formal geocoding before publication.
LOCATION_COORDINATES = {
    "Tenderloin": (37.7842, -122.4142),
    "Embarcadero": (37.7955, -122.3937),
    "SOMA": (37.7785, -122.4056),
    "Mission District": (37.7599, -122.4148),
    "Financial District": (37.7946, -122.3999),
    "Castro": (37.7609, -122.4350),
}


def find_input_path() -> Path:
    for path in INPUT_PATHS:
        if path.exists():
            return path
    raise FileNotFoundError(
        "Could not find simulated_sentiment_scenario_data.csv. "
        "Place it in data/ or the repository root."
    )


def deterministic_jitter(row_number: int, location: str, service: str, scenario: str) -> tuple[float, float]:
    """Return a tiny deterministic coordinate offset so points do not fully overlap."""
    seed = f"{row_number}-{location}-{service}-{scenario}"
    digest = hashlib.md5(seed.encode("utf-8")).hexdigest()
    value = int(digest[:8], 16)
    angle = (value % 360) * math.pi / 180
    radius = ((value // 360) % 100) / 100 * 0.0012
    return math.sin(angle) * radius, math.cos(angle) * radius


def build_xy_dataset(df: pd.DataFrame) -> pd.DataFrame:
    records = df.copy()

    latitudes: list[float] = []
    longitudes: list[float] = []

    for idx, row in records.iterrows():
        location = str(row.get("Location", ""))
        base_lat, base_lon = LOCATION_COORDINATES.get(location, (37.7749, -122.4194))
        lat_offset, lon_offset = deterministic_jitter(
            idx,
            location,
            str(row.get("Service", "")),
            str(row.get("Scenario", "")),
        )
        latitudes.append(base_lat + lat_offset)
        longitudes.append(base_lon + lon_offset)

    # Keep the geocoded version lighter by excluding the synthetic narrative text.
    if "Text" in records.columns:
        records = records.drop(columns=["Text"])

    records.insert(0, "record_id", [f"SIM-{i + 1:04d}" for i in range(len(records))])
    records["Latitude"] = latitudes
    records["Longitude"] = longitudes
    records["X"] = records["Longitude"]
    records["Y"] = records["Latitude"]
    records["Data_Type"] = "Simulated"
    records["Coordinate_Method"] = "Approximate neighborhood centroid plus deterministic jitter"
    return records


def main() -> None:
    input_path = find_input_path()
    df = pd.read_csv(input_path)
    output = build_xy_dataset(df)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_PATH, index=False)
    print(f"Loaded {len(df)} rows from {input_path}")
    print(f"Wrote {len(output)} geocoded rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
