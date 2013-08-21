import SocketServer
import sqlite3
import logging


class DBHandler(object):
    db_file = "pdu.db"

    def __init__(self, db_file="pdu.db"):
        self.db_file = db_file
        logging.debug("Creating new DBHandler: %s" % self.db_file)
        logging.getLogger().name = "DBHandler"
        self.conn = sqlite3.connect(self.db_file, check_same_thread = False)
        self.cursor = self.conn.cursor()

    def do_sql(self, sql):
        logging.debug("executing sql: %s" % sql)
        self.cursor.execute(sql)
        self.conn.commit()

    def get_res(self, sql):
        return self.cursor.execute(sql)

    def get_one(self, sql):
        res = self.get_res(sql)
        return res.fetchone()

    def close(self):
        self.cursor.close()
        self.conn.close()


class ListenerServer(object):
#    conn = sqlite3.connect("/var/lib/lava-pdu/pdu.db", check_same_thread = False)
#    cursor = conn.cursor()

    def __init__(self, config):
        self.server = TCPServer((config["hostname"], config["port"]), TCPRequestHandler)
        logging.getLogger().name = "ListenerServer"
        logging.getLogger().setLevel(config["logging_level"])
        logging.info("listening on %s:%s" % (config["hostname"], config["port"]))
        self.db = DBHandler(config["dbfile"])
        self.create_db()
        self.server.db = self.db

    def create_db(self):
        sql = "create table if not exists pdu_queue (id integer primary key, hostname text, port int, request text)"
        self.db.do_sql(sql)

    def start(self):
        logging.info("Starting the ListenerServer")
        self.server.serve_forever()


class TCPRequestHandler(SocketServer.BaseRequestHandler):
    #"One instance per connection.  Override handle(self) to customize action."
    def insert_request(self, data):
        array = data.split(" ")
        hostname = array[0]
        port = int(array[1])
        request = array[2]
        db = self.server.db
        sql = "insert into pdu_queue values (NULL,'%s',%i,'%s')" % (hostname,port,request)
        db.do_sql(sql)
        #db.close()

    def handle(self):
        logging.getLogger().name = "TCPRequestHandler"
        try:
            data = self.request.recv(4096).strip()
            logging.debug("got request: %s" % data)
            self.insert_request(data)
            self.request.sendall("ack\n")
        except:
            self.request.sendall("nack\n")
        self.request.close()

class TCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    allow_reuse_address = True
    daemon_threads = True
    pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("Executing from __main__")
    starter = {"hostname": "0.0.0.0",
               "port":16421,
               "dbfile": "/var/lib/lava-pdu/pdu.db",
               "logging_level": logging.DEBUG}
    ss = ListenerServer(starter)
    ss.start()