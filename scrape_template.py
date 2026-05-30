import tweepy
from textblob import TextBlob
import pandas as pd

# Authenticate with Twitter
auth = tweepy.OAuthHandler("API_KEY", "API_SECRET")
auth.set_access_token("ACCESS_TOKEN", "ACCESS_SECRET")
api = tweepy.API(auth)

# Search query
query = "Waymo OR Uber AND (ride OR safety OR crash OR panic)"
tweets = tweepy.Cursor(api.search_tweets, q=query, geocode="37.7749,-122.4194,10mi", lang="en").items(200)

data = []
for tweet in tweets:
    text = tweet.text
    sentiment = TextBlob(text).sentiment.polarity
    label = "Positive" if sentiment > 0.1 else "Negative" if sentiment < -0.1 else "Neutral"
    data.append({"text": text, "sentiment": label, "score": sentiment, "location": "San Francisco"})

df = pd.DataFrame(data)