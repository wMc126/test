import re

# 正面词（强度）
POS_WORDS = {
    "good": 1, "great": 2, "excellent": 3, "amazing": 3, "wonderful": 2,
    "love": 2, "happy": 1, "nice": 1, "fantastic": 3, "awesome": 2,
}

# 负面词（强度）
NEG_WORDS = {
    "bad": 1, "terrible": 3, "awful": 3, "horrible": 3, "sad": 1,
    "hate": 2, "annoying": 1, "useless": 2,
}

# 否定词
NEGATORS = {"not", "no", "never", "isn't", "aren't", "wasn't"}

def analyze_sentiment(text: str):
    text = text.lower()
    words = re.findall(r"\b[\w']+\b", text)

    score = 0
    negate = False

    for w in words:
        if w in NEGATORS:
            negate = True
            continue

        val = 0
        if w in POS_WORDS:
            val = POS_WORDS[w]
        elif w in NEG_WORDS:
            val = -NEG_WORDS[w]

        if negate:
            val = -val
            negate = False

        score += val

    if score > 0:
        return "Positive 😊"
    elif score < 0:
        return "Negative 😡"
    else:
        return "Neutral 😐"
