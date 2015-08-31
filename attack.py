import socket
import random
import json
import ssl
from importlib import import_module

class Guesser:
    def __init__(self, output):
        """
        given the first number, set up our guesser

        be dumb and guess the same number
        """
        self.num = output
    
    def guess(self, num):
        """
        make a guess, and get the most recent
        num. hooray off-by-one slip-ups!
        """
        guess = self.num
        self.num = num
        return guess

def attack(ip, port, guesser):
    """
    attack the service at the port using
    the provided guesser (guesser is a class)
    """
    key = None
    msg={"team": "cobra"}
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ssl_sock = ssl.wrap_socket(s,cert_reqs=ssl.CERT_REQUIRED,ca_certs="serv_cert.pem")
    print("connecting")
    ssl_sock.connect((ip, port))
    guess_machine = None

    while key is None:
        buf = str(ssl_sock.recv(1024), "UTF-8")
        print("recvd:",buf)
        try:
            response = json.loads(buf)
            if "error" in response.keys():
                # print error, quit
                print("Error:",response["error"])
                return
            if guess_machine is None:
                guess_machine = guesser(response["num"])
            key = response["key"]
        except ValueError as e:
            print("bad json from server:",e)
            return

        msg["guess"] = guess_machine.guess(response["num"])
        print("guessing:",msg["guess"])
        ssl_sock.sendall(bytes(json.dumps(msg)+"\n","UTF-8"))
    print("key:",key)


if __name__ == "__main__":
    # attack various services
    # TODO: dynamically import our guessers,
    # use the common attack code to handle sockets and
    # comms logic

    # placeholder/example
    #attack("localhost",1337,Guesser)

    # real attacks, since having some level-specific logic makes things easier
    levels = [1,2,3,4]
    mods = [import_module("attack_%d" % i) for i in levels]
    for i in levels:
        mods[i-1].attack("localhost",1337+i-1)
