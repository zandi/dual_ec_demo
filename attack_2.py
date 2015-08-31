from prng_2 import prng
from ecff.finitefield.finitefield import FiniteField
import random
import socket
import json
import ssl

class Guesser:
    
    def __init__(self, output):
        """
        given the initial output,
        init out guesser so we can guess
        all remaining outputs

        This requires some guessing, since
        there are multiple possible states
        """
        F = FiniteField(104729,1)
        P = F(7)
        Q = F(2)
        PQ_inverse = (P*Q).inverse()
        #recover 'potential' outputs
        outputs = [(i<<15) | output for i in range(4)]
        Ts = [F(o) for o in outputs]
        oldstates = [T*PQ_inverse for T in Ts]
        print("old states:",oldstates)
        curstates = [o*P*P for o in oldstates]
        self.candidates = [prng(seed=c.n) for c in curstates]
        self.refine_step = 0

    def guess(self):
        """
        by the nature of level 1, we
        don't have to 'modify' our guesses.
        we're guaranteed to get precisely 
        the right prng
        """

        print("generating number")
        return self.p.get_num()

    def refine(self, num):
        """
        based on next output (num)
        determine which candidate prng
        is correct.
        """
        for i in range(len(self.candidates)):
            if self.candidates[i].get_num() == num:
                print("old state found!")
                self.p = self.candidates[i]

    
# ok. To attack, let's adapt the old attack,
# but handle the reduced state leakage

# we know the order, P, Q, and the algorithm.
# use single output to generate candidate states,
# then test which candidate state is accurate

#output = state * P * Q
def get_states(p):
    """
    Given the (assumed default) prng
    with various known public constants,
    recover candidates for the prng's internal state
    """
    #TODO: pull these from prng object ?
    #note: 104729 requires 17 bits
    F = FiniteField(104729,1)
    P = F(7)
    Q = F(2)
    PQ_inverse = (P*Q).inverse()
    t = p.get_num()
    T = F(t)
    # we only get 16 of 17 possible bits of output
    # thus, have 2 candidate old states
    oldstates = [t*PQ_inverse, F(t | 0x10000)*PQ_inverse]
    curstates = [(oldstate*P*P).n for oldstate in oldstates]
    return curstates

def transpose(A):
    """
    assuming we are given an nxm matrix
    (not a jagged array) return a transposed
    version
    """
    return [[row[i] for row in A] for i in range(len(A[0]))]

def test():
    print("randomly generating/recovering 5 prngs")
    seeds = [random.randint(1,104729-1) for i in range(0,5)]
    print("seeds: ",seeds)
    prngs = [prng(seed=s) for s in seeds]
    curstates = [get_states(p) for p in prngs]
    curstates = transpose(curstates) #transpose, so it's easier to work with.
    candidate_prngs = [[prng(seed=s) for s in states] for states in curstates]

    # check candidates against expected output to pick which prng is right
    good_output = [p.get_num() for p in prngs]
    synced_prngs = []
    print("choosing correct candidate prng...")
    for i in range(len(good_output)):
        for candidates in candidate_prngs:
            if candidates[i].get_num() == good_output[i]:
                synced_prngs.append(candidates[i])

    good_output = [p.get_num() for p in prngs]
    synced_output = [p.get_num() for p in synced_prngs]
    print("good output: ",good_output)
    print("test output: ",synced_output)

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

    # first, let's build our guesser, then 
    # determine which prng is correct
    buf = str(s.recv(1024), "UTF-8")
    print("recvd:",buf)
    try:
        response = json.loads(buf)
    except ValueError as e:
        print("bad json from server:", e)
        return
    guess_machine = Guesser(response["num"])
    msg["guess"] = 42 #doesn't matter
    s.sendall(bytes(json.dumps(msg)+"\n","UTF-8"))
    print("sending: "+json.dumps(msg))

    buf = str(s.recv(1024), "UTF-8")
    print("recvd:",buf)
    try:
        response = json.loads(buf)
    except ValueError as e:
        print("bad json from server:", e)
        return

    guess_machine.refine(response["num"])
    msg["guess"] = guess_machine.guess()
    s.sendall(bytes(json.dumps(msg)+"\n","UTF-8"))

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
    attack("127.0.0.1", 1338)

