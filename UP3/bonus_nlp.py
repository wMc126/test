from collections import Counter
import re
chat_history = []
def add_message(message):
    chat_history.append(message)

def generate_summary(bot):
    if len(chat_history) == 0:
        return "No chat history"
    text = " ".join(chat_history[-20:])
    prompt = "Summarize this conversation briefly: " + text
    return bot.chat(prompt)


def extract_keywords():

    if len(chat_history) == 0:
        return []
    text = " ".join(chat_history).lower()
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text)
    stopwords = {
        'this', 'that', 'have', 'with',
        'from', 'your', 'what', 'about',
        'there', 'would', 'could',
        'should', 'their', 'hello'}

    filtered = [w for w in words if w not in stopwords]
    counter = Counter(filtered)
    return counter.most_common(5)