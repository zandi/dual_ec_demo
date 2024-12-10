import socketserver
import json
import threading
import random
from importlib import import_module
import time
import ssl
import logging

#NOTE: if we don't provide one of these variables in our extra dict to a logging call, the line WON'T be logged!
FORMAT = '%(asctime)-15s [%(ip)s:%(port)s] %(team)s %(message)s'
logging.basicConfig(filename='log',level=logging.INFO,format=FORMAT)
LOGGER = logging.getLogger('server');

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain("serv_cert.pem", keyfile="serv_key.pem")
ssl_context.check_hostname = False

class GameHandler(socketserver.StreamRequestHandler):
    """
    handle each connection, playing the game
    """
    def setup(self):
        """
        based on server, set up our
        prng and key
        """
        super().setup()
        rhost, rport = self.request.getpeername()
        LOGGER.info('setting up level %s', self.server.level,extra={'ip':rhost,'port':rport,'team':None})
        level = self.server.level
        valid = [1,2,3,4]
        MAX = {1: 104729, 2: 104729, 3: 331337, 4: 331337}
        MIN = 1 # just not 0
        if level == 0:
            # demo/test level.
            self._key = "this is the key!"
            # ew. but, it works
            self.prng = type("",(),dict(get_num=lambda: 42))
        elif level in valid:
            Mod = import_module("prng_%d" % level)
            r = random.Random()
            seed = r.randint(MIN, MAX[level])
            self.prng = Mod.prng(seed=seed)
            with open("key_%d" % level,"r") as f:
                self._key = f.read().strip()
        else:
            raise Exception("Invalid level to handle: %d" % level)

    #TODO: implement a timeout? connection limit?
    def handle(self):
        """
        play the game

        once they've guessed 50 consecutive outputs,
        they win.

        If there's 2 bad guesses, they lose
        """
        self.log_extra = {'ip': None, 'port': None, 'team': None}
        LOGGER.debug('set log_extra', extra=self.log_extra)

        self.ssl_sock = ssl_context.wrap_socket(self.request, server_side=True)
        self.log_extra['ip'], self.log_extra['port'] = self.ssl_sock.getpeername()
        LOGGER.info('connected', extra=self.log_extra)

        guessed=0
        bad=0
        self.num = self.prng.get_num()
        msg = {
                "num": self.num,
                "correct": guessed,
                "key": None
                }
        team = None
        team_has_been_set = None
        while bad < 2:
            # update info given to challenger
            msg["num"] = self.num
            msg["correct"] = guessed

            # only let them set the team once
            if not team_has_been_set and team:
                if len(team) > 50:
                    # please don't
                    return
                msg["team"] = team
                self.log_extra["team"] = team
                team_has_been_set = True
                LOGGER.debug('team name given',extra=self.log_extra)

            if guessed >= 50:
                msg["key"] = self._key
                LOGGER.info('team beat challenge!', extra=self.log_extra)

            # make a new secret for them to guess
            self.num = self.prng.get_num()

            self.ssl_sock.sendall(bytes(json.dumps(msg), "UTF-8"))
            if msg["key"]:
                LOGGER.info('closing connection', extra=self.log_extra)
                return

            try:
                byte_line = self.ssl_sock.recv(4096)
                line = str(byte_line,"UTF-8").strip()
                result = json.loads(line)
                team = result["team"]

                if result["guess"] == self.num:
                    guessed += 1
                else:
                    bad += 1
                LOGGER.debug('received: %s', result, extra=self.log_extra)
            except (ValueError, KeyError, UnicodeEncodeError) as e:
                # some form of bad input.
                # give error message, kill connection
                LOGGER.error('exception: %s', type(e).__name__+": "+str(e), extra=self.log_extra)
                err = json.dumps({"error": type(e).__name__+": "+str(e)})
                self.ssl_sock.sendall(bytes(err,"UTF-8"))
                LOGGER.info('disconnecting', extra=self.log_extra)
                return
            except ConnectionResetError:
                LOGGER.debug('client disconnected')
                return
        

#TODO: test the forking mixin gives better performance than the threading mixin
class GameServer(socketserver.ForkingMixIn, socketserver.TCPServer):
    level=0
    def __init__(self, server_address, RequestHandlerClass, level):
        good = [0,1,2,3,4]
        if level in good:
            super().__init__(server_address, RequestHandlerClass)
            self.level = level
        else:
            raise Exception("Invalid level to serve: %d" % level)

if __name__ == "__main__":
    levels = [1,2,3,4]
    HOST = ""
    PORTS = [1337 + i-1 for i in levels]
    servers = [GameServer((HOST, PORTS[i-1]), GameHandler, i) for i in levels]
    server_threads = [threading.Thread(target=s.serve_forever) for s in servers]
    for t in server_threads:
        t.start()
        print("thread started:",t.name)
