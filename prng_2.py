from ecff.finitefield.finitefield import FiniteField

class prng:
    def __init__(self,n=104729,seed=42):
        """
        create a new prng using a finite field
        of order n. n must be prime, as we basically
        use the integers mod some prime (Z mod p).
        Jeremy Kun's code lets us make this actual
        arithmetic code quite nice. We do take a
        performance hit, but not a *ton*

        note that a seed of 88993 w/ default order
        gives an early repeated value
        """
        self.group = FiniteField(n,1) #guarantees we use integers mod p
        #e = 5
        #TODO: perhaps dynamically pick p and q?
        self.state = self.group(seed)
        self.P = self.group(7)
        self.Q = self.group(2)

    def get_num(self):
        """
        produce a number, and update our
        internal state

        try to copy the EC_DRBG algorithm

        THIS IS SUPER BROKEN.
        """
        """
        r = self.group.star(self.state,self.P)
        self.state = self.group.star(r,self.P)
        t = self.group.star(r,self.Q)
        """
        r = self.state * self.P
        self.state = r * self.P
        t = r * self.Q
        return t.n & 0x7fff # throw 2 leading bits away

    def find_repeat(self):
        """
        get random numbers until we receive a 
        number which we've already seen.

        given the mask, we no longer have
        simple cycles in output. Instead,
        we may repeat a number, then proceed
        with different output than 'expected'
        had we found a cycle. So, this function
        isn't terribly useful anymore.
        """
        vals = {}
        output = self.get_num()
        while output not in vals:
            vals[output] = self.get_num()
            output = vals[output]
        return len(vals)

    def test_output(self):
        """
        Given the default finite field
        of order 104729, we almost always
        observe a cycle of 26182 elements.

        get this many random numbers, and see
        which are most frequent
        """
        vals = {}
        for i in range(26182):
            key = self.get_num()
            if key in vals:
                vals[key]+=1
            else:
                vals[key]=1
        sorted_vals = sorted(vals.items(), key=lambda x:x[1], reverse=True)
        top_ten = sorted_vals[:10]
        print("top 10: ",top_ten)
        bottom_ten = sorted_vals[-10:]
        bottom_ten.reverse()
        print("bottom 10: ",bottom_ten)
        for i in range(len(sorted_vals)-1):
            if sorted_vals[i+1] < sorted_vals[i]:
                print("break: ",i,", ",sorted_vals[i:i+2])

