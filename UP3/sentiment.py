import subprocess
import sys

from textblob import TextBlob


def analyze_sentiment(text):

    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0:
        return "😊 [P+]"
    elif polarity < 0:
        return "😡 [N-]"
    else:
        return "😐 [N]"



