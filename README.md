## Basics

This is a modular server designed to teach the basics of the
backdoor in DUAL_EC_DRBG by providing a simplified version
of the cipher to attack. The setup is a series of jeapordy-style
CTF challenges, each level introducing a new concept building
up to the final level. The goal is to write a program to prove
to the server that you have cracked each level's RNG.

Also, I am not a cryptographer, so if you see some mistakes please
let me know!

## Usage

`python3 server.py` to start the server

`python3 attack.py` to demo the attacks

## Design

The server uses SSL to protect communication from potential eavesdroppers
on the same LAN. This was with typical jeapordy-style CTFs in mind,
where competing teams were potentially on the same LAN. This way one team
solving the challenge doesn't mean everyone who's sniffing the network
also gets the flag. Things should be fine so long as a fresh cert is
generated, and teams know to verify the fingerprint. Of course, now that
the attack code is also published to demonstrate the attack/test the setup,
directly using this in a CTF may not be useful.

Each level's RNG is loaded dynamically (terrible hack) from a separate python
module, so things are mostly modular. The first two levels use finite field
elements instead of elements from the group on an elliptic curve, turning
the hard part of the attack into simply applying the multiplicative inverse.
Similarly, the harder of the finite field/elliptic curve levels implement
masking, forcing hte user to perform multiple calculations to determine which
preimage is correct, and therefore which recovered state is correct.

The standard allows for additional input to be XORed with the state
before getting random bits, and DUAL_EC_DRBG 2007 (there's two versions)
has another elliptic curve computation that DUAL_EC_DRBG 2006 didn't.
This is currently most similar to DUAL_EC_DRBG 2006 without any additional
input.

### Elliptic Curve Stuff

For the elliptic curve challenges, discovering the backdoor is not computationally
feasible, so we instead use much smaller subgroups. This way the attacker can
feasibly brute-force the backdoor from the published points in real-time. Originally
developed on a single-core netbook, basically any modern machine should be capable
of doing the challenges.

The actual process of choosing smaller finite fields/curve subgroups involved some 
hand-waving, trial-and-error, and math background (Cauchy's theorem, abstract algebra, etc.).
While I can justify the choice of finite field/curve points, choosing a curve is beyond
me; I just fooled around and got lucky.

## References/links

I make use of Jeremy Kun's awesome elliptic curve math library. Go read more
math (intersect) programming! (http://jeremykun.com/2014/02/08/introducing-elliptic-curves/).

The original inspiration for this was coming across "The NSA Back Door to NIST" by
Thomas C. Hales, published in the AMS. Being the first technical info I found on the
backdoor, the simplicity surprised me. Sure, it still required an above-average math
background, but wasn't completely opaque black magic. (http://www.ams.org/notices/201402/rnoti-p190.pdf)

Additionally, the more recently published projectbullrun site's info on dual-ec is
superb. For a proper, in-depth look at the algorithm, how it was standardized, the
differences between the versions, and emperical evidence on cracking, go there. It's 
really cool. (http://projectbullrun.org/dual-ec/index.html) (http://projectbullrun.org/dual-ec/documents/dual-ec-20150731.pdf)
