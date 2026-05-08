"""
Created on Tue Jul 22 00:47:05 2014

@author: alina, zzhang
"""

import time
import socket
import select
import sys
import string
import indexer
import json
import pickle as pkl
from chat_utils import *
import chat_group as grp
import requests
from chatbot_client import ChatBotClient
from sentiment import analyze_sentiment
import bonus_nlp

class Server:
    def __init__(self):
        self.new_clients = []  # list of new sockets of which the user id is not known
        self.logged_name2sock = {}  # dictionary mapping username to socket
        self.logged_sock2name = {}  # dict mapping socket to user name
        self.all_sockets = []
        self.group = grp.Group()
        # start server
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(SERVER)
        self.server.listen(5)
        self.all_sockets.append(self.server)
        # initialize past chat indices
        self.indices={}
        # sonnet
        self.sonnet = indexer.PIndex("AllSonnets.txt")
        self.bot = ChatBotClient()
        self.bots = {}
        self.user_db = {}
        with open("users.txt", "r") as f:
                for line in f:
                    name, pwd = line.strip().split(":")
                    self.user_db[name] = pwd

    def new_client(self, sock):
        # add to all sockets and to new clients
        print('new client...')
        sock.setblocking(0)
        self.new_clients.append(sock)
        self.all_sockets.append(sock)

    def login(self, sock):
            msg = json.loads(myrecv(sock))
            if len(msg) > 0:
                if msg["action"] == "login":
                    name = msg["name"]
                    password = msg.get("password", "") # 获取客户端传来的密码

                    if name in self.user_db:
                        if self.user_db[name] != password:
                            print(f"Login failed: {name} (Wrong Password)")
                            mysend(sock, json.dumps({"action": "login", "status": "wrong_password"}))
                            # 注意：这里不需要移除 new_clients，让用户留在登录页面重试
                            return 
                    else:
                        # 新用户注册
                        self.user_db[name] = password
                        with open("users.txt", "a") as f:
                         f.write(f"{name}:{password}\n")
                        print(f"New user registered: {name}")

                    # --- 检查重复登录 ---
                    if name in self.logged_name2sock:
                        mysend(sock, json.dumps({"action": "login", "status": "duplicate"}))
                        return

                    # --- 验证通过：移动 socket 到已登录列表 ---
                    print(name + ' logged in')
                    # 只有在这里成功 remove，它才不会下次又进 login
                    self.new_clients.remove(sock) 
                    self.logged_name2sock[name] = sock
                    self.logged_sock2name[sock] = name
                    
                    if name not in self.indices.keys():
                        try:
                            self.indices[name] = pkl.load(open(name + '.idx', 'rb'))
                        except IOError:
                            self.indices[name] = indexer.Index(name)
                    
                    self.group.join(name)
                    mysend(sock, json.dumps({"action": "login", "status": "ok"}))
                else:
                    print('wrong code received')

    def logout(self, sock):
        # remove sock from all lists
        name = self.logged_sock2name[sock]
        pkl.dump(self.indices[name], open(name + '.idx', 'wb'))
        del self.indices[name]
        del self.logged_name2sock[name]
        del self.logged_sock2name[sock]
        self.all_sockets.remove(sock)
        self.group.leave(name)
        sock.close()
# ==============================================================================
# main command switchboard
    def handle_msg(self, from_sock):
        # read msg code
        msg = myrecv(from_sock)
        if len(msg) > 0:
            # handle connect request this is implemented for you
            # ==============================================================================
            msg = json.loads(msg)
            if msg["action"] == "connect":
                to_name = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                if to_name == from_name:
                    msg = json.dumps({"action": "connect", "status": "self"})
                # connect to the peer
                elif self.group.is_member(to_name):
                    to_sock = self.logged_name2sock[to_name]
                    self.group.connect(from_name, to_name)
                    the_guys = self.group.list_me(from_name)
                    msg = json.dumps(
                        {"action": "connect", "status": "success"})
                    for g in the_guys[1:]:
                        to_sock = self.logged_name2sock[g]
                        mysend(to_sock, json.dumps(
                            {"action": "connect", "status": "request", "from": from_name}))
                else:
                    msg = json.dumps(
                        {"action": "connect", "status": "no-user"})
                mysend(from_sock, msg)
# handle messeage exchange: IMPLEMENT THIS
# ==============================================================================
            elif msg["action"] == "exchange":
                from_name = self.logged_sock2name[from_sock]
                """
                Finding the list of people to send to and index message
                """
                # IMPLEMENTATION 
                # # ---- start your code ---- #
                self.indices[from_name].add_msg_and_index(msg['message'])
                sentiment_display = analyze_sentiment(msg['message'])
                msg['message'] += " " + sentiment_display
                # ---- end of your code --- #
                the_guys = self.group.list_me(from_name)[1:]
                for g in the_guys:
                    to_sock = self.logged_name2sock[g]
                    # IMPLEMENTATION
                    # ---- start your code ---- #
                    mymsg=json.dumps({
    "action": "exchange",
    "from": from_name,
    "message": msg["message"]
})
                    mysend(to_sock,mymsg)
                if "@bot" in msg["message"].lower():
                    group_name = self.group.find_group(from_name)
                    if group_name not in self.bots:
                     self.bots[group_name] = ChatBotClient()
                     self.bots[group_name].set_personality("你现在在一个多人聊天室里。")
                    ai_input = msg["message"].replace("@bot", "").strip()
                    print(f"正在为 {from_name} 调用 AI...")
                    ai_reply = self.bots[group_name].chat(ai_input)
                    ai_msg = json.dumps({
                        "action": "exchange",
                        "from": "imai", 
                        "message": ai_reply
                    })
                    all_guys = self.group.list_me(from_name)
                    for g in all_guys:
                        to_sock = self.logged_name2sock[g]
                        mysend(to_sock, ai_msg)
                    # ---- end of your code --- #
# ==============================================================================
# the "from" guy has had enough (talking to "to")!
# ==============================================================================
            elif msg["action"] == "disconnect":
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                self.group.disconnect(from_name)
                the_guys.remove(from_name)
                if len(the_guys) == 1:  # only one left
                    g = the_guys.pop()
                    to_sock = self.logged_name2sock[g]
                    mysend(to_sock,json.dumps(
                        {"action": "disconnect", "msg": "everyone left, you are alone"}))
                    self.group.disconnect(g)
# ==============================================================================
#                 listing available peers: IMPLEMENT THIS
            elif msg["action"] == "list":
                # ---- start your code ---- #
                result=self.group.list_all()
                # ---- end of your code --- #
                mysend(from_sock, json.dumps(
                    {"action": "list", "results": result}))
# ==============================================================================
#   ok          retrieve a sonnet : IMPLEMENT THIS  
            elif msg["action"] == "poem":
                # IMPLEMENTATION
                # ---- start your code ---- #
                pdex=int(msg['target'])
                from_name = self.logged_sock2name[from_sock]
                print(from_name + ' asks for ', pdex)
                poem = str(self.sonnet.get_poem(pdex))
                print('here:\n', poem)
                # ---- end of your code --- #
                mysend(from_sock, json.dumps(
                    {"action": "poem", "results": poem}))
# ==============================================================================
#                 time
# ==============================================================================
            elif msg["action"] == "time":
                ctime = time.strftime('%d.%m.%y,%H:%M', time.localtime())
                mysend(from_sock, json.dumps(
                    {"action": "time", "results": ctime}))
# ==============================================================================
#                 search: : IMPLEMENT THIS
# ==============================================================================
            elif msg["action"] == "search":

                # IMPLEMENTATION
                # ---- start your code ---- #
                target=msg['target']
                search_rslt = ''
                for name in self.indices.keys():
                    for find in self.indices[name].search(target):
                      search_rslt+=str(find)
                print('server side search: ' + search_rslt)                
                # ---- end of your code --- #
                mysend(from_sock, json.dumps(
                    {"action": "search", "results": search_rslt}))

# ==============================================================================
#                 pic generation
# ==============================================================================
            elif msg["action"] == "aipic":
                # IMPLEMENTATION
                # ---- start your code ---- #
                prompt=msg['target']
                url = f"https://image.pollinations.ai/prompt/{prompt}"
                img = requests.get(url).content
                with open(prompt+'.png', "wb") as f:
                    f.write(img)
                # ---- end of your code --- #
                mysend(from_sock, json.dumps(
                    {"action": "aipic", "results": prompt+'.png'}))
# ==============================================================================
            elif msg["action"] == "bot":
                # IMPLEMENTATION
                # ---- start your code ---- #
                from_name = self.logged_sock2name[from_sock]
                if from_name not in self.bots:
                    print(f"为用户 {from_name} 创建了独立的 AI 实例")
                    self.bots[from_name] = ChatBotClient()
                prompt=msg['target']
                sentiment_display = analyze_sentiment(prompt)
                prompt += " " + sentiment_display
                print(f"Your ai chatbot imai is coming...")
                ai_reply = self.bots[from_name].chat(prompt)
                print(f"imai: {ai_reply}")
                # ---- end of your code --- #
                mysend(from_sock, json.dumps(
                    {"action": "bot", "results": ai_reply}))
            elif msg["action"] == "set_personality":
                prompt=msg['target']
                self.bots[from_name].set_personality(prompt)
                mysend(from_sock, json.dumps(
                    {"action": "set_personality", "results": "Personality updated."}))
#                 the "from" guy really, really has had enough
# ==============================================================================
        else:
            # client died unexpectedly
            self.logout(from_sock)
# ==============================================================================
# main loop, loops *forever*
# ==============================================================================
    def run(self):
        print('starting server...')
        while(1):
            read, write, error = select.select(self.all_sockets, [], [])
            print('checking logged clients..')
            for logc in list(self.logged_name2sock.values()):
                if logc in read:
                    self.handle_msg(logc)
            print('checking new clients..')
            for newc in self.new_clients[:]:
                if newc in read:
                    self.login(newc)
            print('checking for new connections..')
            if self.server in read:
                # new client request
                sock, address = self.server.accept()
                self.new_client(sock)


def main():
    server = Server()
    server.run()


if __name__ == '__main__':
    main()
