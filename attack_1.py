from prng_1 import prng
from ecff.finitefield.finitefield import FiniteField
import socket
import random
import json
import ssl

class Guesser:
    def __init__(self, output):
        """
        given the initial output,
        init out guesser so we can guess
        all remaining outputs
        """
        F = FiniteField(104729,1)
        P = F(7)
        Q = F(2)
        PQ_inverse = (P*Q).inverse()
        T = F(output)
        oldstate = T*PQ_inverse
        curstate = oldstate*P*P 
        self.p = prng(seed=curstate.n)

    def guess(self):
        """
        by the nature of level 1, we
        don't have to 'modify' our guesses.
        we're guaranteed to get precisely 
        the right prng
        """
        return self.p.get_num()


# we know the order, P, Q, and the algorithm.
# let's see if we can determine state from just 
# a single output

#output = state * P * Q
def get_state(p):
    """
    Given the (assumed default) prng
    with various known public constants,
    recover the prng's current state
    """
    #TODO: pull these from prng object ?
    F = FiniteField(104729,1)
    P = F(7)
    Q = F(2)
    PQ_inverse = (P*Q).inverse()
    t = p.get_num()
    T = F(t)
    oldstate = T*PQ_inverse
    curstate = oldstate*P*P
    return curstate.n

def test():
    print("randomly generating/recovering 5 prngs")
    seeds = [random.randint(1,104729) for i in range(0,5)]
    print("seeds: ",seeds)
    prngs = [prng(seed=s) for s in seeds]
    curstates = [get_state(p) for p in prngs]
    print("recovered states: ",curstates)
    synced_prngs = [prng(seed=s) for s in curstates]
    good_output = [p.get_num() for p in prngs]
    synced_output = [p.get_num() for p in synced_prngs]
    print("good output: ",good_output)
    print("test output: ",synced_output)
    if good_output == synced_output:
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
    attack("127.0.0.1", 1337)

