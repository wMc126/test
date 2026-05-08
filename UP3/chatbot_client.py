import json
import urllib.request

class ChatBotClient:
    def __init__(self, name="imai", model="sam860/phi4-mini:3.8b", host='http://localhost:11434'):
        self.url = f"{host}/api/chat"
        self.model = model
        self.name = name
        self.messages = []
        self.set_personality("You are a helpful assistant.")

    def chat(self, message: str):
        self.messages.append({"role": "user", "content": message})
        
        # 构建发送给 Ollama 的原始数据包
        data = {
            "model": self.model,
            "messages": self.messages,
            "stream": False
        }
        
        try:
            # 使用 Python 最底层的联网工具，绝对不会因为库不兼容而崩溃
            req = urllib.request.Request(
                self.url, 
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                reply = result['message']['content']
                self.messages.append({"role": "assistant", "content": reply})
                return reply
                
        except Exception as e:
            return f"连接本地Ollama失败，请检查软件是否开启: {e}"

    def should_respond(self, message):
        return "@bot" in message.lower()

    def set_personality(self, description):
        system_msg = {"role": "system", "content": description}
        self.messages = [system_msg] 
        print(f"系统消息已更新: {description}")
