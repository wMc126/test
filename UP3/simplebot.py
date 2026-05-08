import json
import urllib.request

# 手写一个简易 Bot 类，不需要安装任何库
class SimpleBot:
    def __init__(self, model="phi4-mini"):
        self.url = "http://localhost:11434/api/chat"
        self.model = model
        self.history = []

    def chat(self, user_message):
        self.history.append({"role": "user", "content": user_message})
        data = {
            "model": self.model,
            "messages": self.history,
            "stream": False
        }
        try:
            # 使用 Python 自带的 urllib 发送请求
            req = urllib.request.Request(self.url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                reply = result['message']['content']
                self.history.append({"role": "assistant", "content": reply})
                return reply
        except Exception as e:
            return f"连接 Ollama 失败: {e}"

# 在这里初始化
bot = SimpleBot(model="phi4-mini")
