from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "simulated_sentiment_scenario_data.csv"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs"


def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load the simulated scenario dataset."""
    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {path}. Move simulated_sentiment_scenario_data.csv into the data/ directory."
        )
    return pd.read_csv(path)


def plot_counts(df: pd.DataFrame, column: str, title: str, filename: str) -> None:
    """Create a grouped count bar chart using matplotlib only."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    counts = df.groupby([column, "Service"]).size().unstack(fill_value=0)
    ax = counts.plot(kind="bar", figsize=(10, 6))
    ax.set_title(title)
    ax.set_xlabel(column)
    ax.set_ylabel("Count")
    ax.tick_params(axis="x", rotation=30)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=200)
    plt.close()


def main() -> None:
    df = load_data()
    print("Rows:", len(df))
    print("Columns:", list(df.columns))

    plot_counts(
        df,
        column="Scenario",
        title="Scenario Mentions by Service",
        filename="scenario_mentions_by_service.png",
    )
    plot_counts(
        df,
        column="Sentiment",
        title="Sentiment Distribution by Service",
        filename="sentiment_distribution_by_service.png",
    )
    print(f"Charts saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
