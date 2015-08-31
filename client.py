"""
I'm just going to be VERY generous here. You should
be breaking prngs, not writing boilerplate
socket code.

Of course, you can solve this however you want.
"""
import socket
import json

def make_guess(response):
    """
    given the json response from
    the server, make a guess for what
    the next number will be

    this is just an example, you aren't 
    forced to use just a function or something
    """
    return 42

def attack(ip, port):
    """
    attack the service at ip:port
    """
    key = None
    msg={"team": "teamnamehere"}
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("connecting")
    s.connect((ip, port))

    while key is None:
        buf = str(s.recv(1024), "UTF-8")
        print("recvd:",buf)
        try:
            response = json.loads(buf)
            if "error" in response.keys():
                # print error, quit
                print("Error:",response["error"])
                return
            key = response["key"]
        except ValueError as e:
            print("bad json from server:",e)
            return

        msg["guess"] = make_guess(response)
        print("guessing:",msg["guess"])
        s.sendall(bytes(json.dumps(msg)+"\n","UTF-8"))

    print("key:",key)





if __name__ == "__main__":
    attack("localhost",1337)
