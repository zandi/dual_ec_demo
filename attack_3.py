from prng_3 import prng, tonelli_shanks
from ecff.finitefield.finitefield import FiniteField
from ecff.elliptic import EllipticCurve, Point
import random
import socket
import json
import time
import ssl

# try to implement attack described int
# "The NSA Back Door to NIST" by Thomas C. Hales
# Notices of the AMS, V. 61 No. 2

# basically, output is x(r*Q), and the
# current state (after output) is x(r*P)
# so, if we know e s.t. P = e*Q then...
# r*P = r*(e*Q) = re * Q = e*(r*Q)
# so, given two candidate points from x(r*Q),
# we have two canddiates for r*P. simply make
# 2 prngs seeded by either candidate, then test
# their next output against target prng
class Guesser:
    def __init__(self, out):
        """
        given the initial output,
        init out guesser so we can guess
        all remaining outputs
        """
        prime=331337
        F = FiniteField(prime,1)
        C = EllipticCurve(a=F(1),b=F(1))
        e = F(3) #backdoor! we'd have to pre-compute this
        val = out*out*out + C.a * out + C.b
        print(time.time(),":","finding points...")
        points = [Point(C,F(out),F(y)) for y in tonelli_shanks(val.n,prime)]
        #print("points: ",points)
        print(time.time(),":","recovering states...")
        states = [(e.n*T).x.n for T in points]
        #as both candidates are additive inverses of
        #one another, they have the same x coordinates
        print(time.time(),":","making prng")
        self.p = prng(seed=states[0])

    def guess(self):
        """
        by the nature of level 3, we
        don't have to 'modify' our guesses.
        we're guaranteed to get precisely 
        the right prng
        """
        return self.p.get_num()

def get_state(p):
    """
    given the prng p, get the 2 candidate
    current states of p
    """
    out = p.get_num()
    F = p.P.x.field
    C = p.P.curve
    e = F(3) #backdoor!
    prime = p.P.x.p
    val = out*out*out + C.a * out + C.b
    points = [Point(C,F(out),F(y)) for y in tonelli_shanks(val.n,prime)]
    #print("points: ",points)
    states = [(e.n*T).x.n for T in points]
    #as both candidates are additive inverses of
    #one another, they have the same x coordinates
    return states[0] 

def test():
    """
    randomly generate a couple prng seeds, then
    test syncing up with them
    """
    seeds = [random.randint(1,6257-1) for i in range(5)]
    prngs = [prng(seed=i) for i in seeds]
    cur_states = [get_state(p) for p in prngs]
    good_states = [p.state for p in prngs]
    print("good states: ",good_states)
    print("recovered states: ",cur_states)
    if cur_states == good_states:
        return True
    else:
        return False


def attack(ip, port):
    """
    attack the service at ip:port
    """
    key = None
    msg={"team": "cobra"}
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s = ssl.wrap_socket(sock)
    print("connecting")
    s.connect((ip, port))
    guess_machine = None

    while key is None:
        buf = str(s.recv(1024), "UTF-8")
        print("recvd:",buf)
        try:
            response = json.loads(buf)
            if "error" in response.keys():
                # print error, quit
                print("Error:",response["error"])
                return
            if guess_machine is None:
                guess_machine = Guesser(response["num"])
            key = response["key"]
        except ValueError as e:
            print("bad json from server:",e)
            return

        msg["guess"] = guess_machine.guess()
        print("guessing:",msg["guess"])
        s.sendall(bytes(json.dumps(msg)+"\n","UTF-8"))
    print("key:",key)

if __name__ == "__main__":
    attack("127.0.0.1", 1339)

