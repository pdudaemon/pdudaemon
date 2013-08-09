import SocketServer
import sqlite3
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)
conn=sqlite3.connect('pdu.db', check_same_thread = False)
c=conn.cursor()

class ListenerServer():
    HOST='0.0.0.0'
    PORT=16421

    def __init__(self):
        ### read loglevel here
        self.server = TCPServer((self.HOST, self.PORT), TCPRequestHandler)
        log.info("listening on %s:%s" % (self.HOST, self.PORT))
        self.create_db()

    def create_db(self):
        sql = "create table if not exists pdu_queue (id integer primary key, hostname text, port int, request text)"
        log.debug("Creating pdu_queue table: %s" % sql)
        c.execute(sql)
        conn.commit()

    def start(self):
        print("Starting the ListenerServer")
        self.server.serve_forever()

class TCPRequestHandler(SocketServer.BaseRequestHandler):
    "One instance per connection.  Override handle(self) to customize action."
    def insert_request(self, data):
        array = data.split(" ")
        hostname = array[0]
        port = int(array[1])
        request = array[2]
        sql = "insert into pdu_queue values (NULL,'%s',%i,'%s')" % (hostname,port,request)
        log.debug("executing sql: %s" % sql)
        c.execute(sql)
        conn.commit()

    def handle(self):
        data = self.request.recv(4096).strip()
        #write to sql db here
        log.debug("got request: %s" % data)
        self.insert_request(data)
        self.request.sendall("ack\n")
        self.request.close()

class TCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    allow_reuse_address = True
    daemon_threads = True
    pass

if __name__ == "__main__":
    ss = ListenerServer()
    ss.start()