import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the simulated dataset
df = pd.read_csv("simulated_sentiment_scenario_data.csv")

# Plot scenario mentions
sns.countplot(data=df, x="Scenario", hue="Service").set_title("Scenario Mentions by Service")
plt.xticks(rotation=30)
plt.show()

# Plot sentiment
sns.countplot(data=df, x="Sentiment", hue="Service").set_title("Sentiment Distribution")
plt.show()
