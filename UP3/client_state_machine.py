"""
Created on Sun Apr  5 00:00:32 2015

@author: zhengzhang
"""
from chat_utils import *
import json
from sentiment import analyze_sentiment

class ClientSM:
    def __init__(self, s):
        self.state = S_OFFLINE
        self.peer = ''
        self.me = ''
        self.out_msg = ''
        self.s = s

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me
    
    def login(self, name, password): 
     self.me = name
     msg = json.dumps({
        "action": "login", 
        "name": self.me, 
        "password": password  # <--- 关键：把密码塞进去
         })
     mysend(self.s, msg)
     res = json.loads(myrecv(self.s))
     if res["status"] == "ok":
        self.state = S_LOGGEDIN
        return True
     else:
        # 如果服务器返回 wrong_password，你可以在这里处理
        return False

    def connect_to(self, peer):
        msg = json.dumps({"action": "connect", "target": peer})
        mysend(self.s, msg)
        response = json.loads(myrecv(self.s))
        if response["status"] == "success":
            self.peer = peer
            self.out_msg += 'You are connected with ' + self.peer + '\n'
            return (True)
        elif response["status"] == "busy":
            self.out_msg += 'User is busy. Please try again later\n'
        elif response["status"] == "self":
            self.out_msg += 'Cannot talk to yourself (sick)\n'
        else:
            self.out_msg += 'User is not online, try again later\n'
        return(False)

    def disconnect(self):
        msg = json.dumps({"action": "disconnect"})
        mysend(self.s, msg)
        self.out_msg += 'You are disconnected from ' + self.peer + '\n'
        self.peer = ''

    def proc(self, my_msg, peer_msg):
        self.out_msg = ''
# ==============================================================================
# Once logged in, do a few things: get peer listing, connect, search
# And, of course, if you are so bored, just go
# This is event handling instate "S_LOGGEDIN"
# ==============================================================================
        if self.state == S_LOGGEDIN:
            # todo: can't deal with multiple lines yet
            if len(my_msg) > 0:
            
                if my_msg == 'q':
                    self.out_msg += 'See you next time!\n'
                    self.state = S_OFFLINE

                elif my_msg == 'time':
                    mysend(self.s, json.dumps({"action": "time"}))
                    time_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += "Time is: " + time_in

                elif my_msg == 'who':
                    mysend(self.s, json.dumps({"action": "list"}))
                    logged_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += 'Here are all the users in the system:\n'
                    self.out_msg += logged_in

                elif my_msg[0] == 'c':
                    peer = my_msg[1:]
                    peer = peer.strip()
                    if self.connect_to(peer) == True:
                        self.state = S_CHATTING
                        self.out_msg += 'Connect to ' + peer + '. Chat away!\n\n'
                        self.out_msg += '-----------------------------------\n'
                    else:
                        self.out_msg += 'Connection unsuccessful\n'

                elif my_msg[0] == '?':
                    term = my_msg[1:].strip()
                    mysend(self.s, json.dumps(
                        {"action": "search", "target": term}))
                    search_rslt = json.loads(myrecv(self.s))["results"].strip()
                    if (len(search_rslt)) > 0:
                        self.out_msg += search_rslt + '\n\n'
                    else:
                        self.out_msg += '\'' + term + '\'' + ' not found\n\n'

                elif my_msg[0] == 'p' and my_msg[1:].isdigit():
                    poem_idx = my_msg[1:].strip()
                    mysend(self.s, json.dumps(
                        {"action": "poem", "target": poem_idx}))
                    poem = json.loads(myrecv(self.s))["results"]
                    if (len(poem) > 0):
                        self.out_msg += poem + '\n\n'
                    else:
                        self.out_msg += 'Sonnet ' + poem_idx + ' not found\n\n'

                elif my_msg[:5]=='aipic':
                    prompt=my_msg[5:].strip()
                    mysend(self.s, json.dumps(
                        {"action": "aipic", "target": prompt}))
                    img_url=json.loads(myrecv(self.s))["results"]
                    if (len(img_url) > 0):
                        self.out_msg += "image generated successfully! "+img_url + '\n\n'

                elif my_msg[:3]=='bot':
                    self.state=S_BOT
                    self.out_msg += "You are now chatting with the bot.\n"
                    self.out_msg += "enter 'quit' to end the chat and return to the main menu.\n"
                    self.out_msg += "enter 'set_personality' to set the bot's personality.\n\n"
                else:
                    self.out_msg += menu

            if len(peer_msg) > 0:
                try:
                    peer_msg = json.loads(peer_msg)
                except Exception as err:
                    self.out_msg += " json.loads failed " + str(err)
                    return self.out_msg

                if peer_msg["action"] == "connect":
                    # ----------your code here------#
                    self.peer=peer_msg['from']
                    self.out_msg += 'Request from ' + self.peer + '\n'
                    self.out_msg += 'You are connected with ' + self.peer
                    self.out_msg += '. Chat away!\n\n'
                    self.out_msg += '------------------------------------\n'
                    self.set_state(S_CHATTING)
                    pass
                    # ----------end of your code----#
# ==============================================================================
# Start chatting, 'bye' for quit
# This is event handling instate "S_CHATTING"
# ==============================================================================
        elif self.state == S_CHATTING:
            if len(my_msg) > 0:     # my stuff going out
                if my_msg == 'bye':
                    self.disconnect()
                    self.state=S_LOGGEDIN
                    self.peer = ''
                sentiment = analyze_sentiment(my_msg)
                my_msg += f" (sentiment: {sentiment})"
                mysend(self.s, json.dumps(
                    {"action": "exchange", "from": "[" + self.me + "]", "message": my_msg}))
            if len(peer_msg) > 0:    # peer's stuff, coming in
                # ----------your code here------#
                peer_msg = json.loads(peer_msg)
        
                if peer_msg['action']=='exchange':
                     self.peer=peer_msg['from']
                     self.out_msg+=f"[{self.peer}]:{peer_msg['message']}\n"
                elif peer_msg['action']=='connect':
                     self.peer+=','+peer_msg['from']
                     self.out_msg+=f"({peer_msg['from']} joined)"
                elif peer_msg['action']=='disconnect':
                        self.set_state(S_LOGGEDIN)
                        self.peer = ''
                        try:
                            self.out_msg+=peer_msg['msg']
                        except:
                            pass
                # ----------end of your code----#

            # Display the menu again
            if self.state == S_LOGGEDIN:
                self.out_msg += menu
# ==============================================================================
# chatbot state
        elif self.state == S_BOT:
            prompt=my_msg.strip()
            if len(prompt)==0:
                    if len(peer_msg) > 0:
                     p_msg = json.loads(peer_msg)
                    if p_msg.get("action") == "bot":
                        self.out_msg += "imai: " + p_msg["results"] + "\n\n"
                    else:
                        self.out_msg += "Please provide a prompt for the bot.\n\n"
            else:
                if my_msg.lower() == 'quit':
                    self.state = S_LOGGEDIN
                    self.out_msg += menu
                elif my_msg.lower().startswith('set_personality'):  
                   prompt = my_msg[len('set_personality'):].strip()
                   mysend(self.s, json.dumps({"action": "set_personality", "target": prompt}))
                   self.out_msg += f"Personality updated.Now you can continue chatting:\n"  
                else:
                    sentiment = analyze_sentiment(prompt)
                    prompt += f" (sentiment: {sentiment})"
                    mysend(self.s, json.dumps(
                            {"action": "bot", "target": prompt}))
                    self.out_msg =''
# ==============================================================================
        else:
            self.out_msg += 'How did you wind up here??\n'
            print_state(self.state)

        return self.out_msg
