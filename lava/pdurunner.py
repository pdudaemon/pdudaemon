import logging
import time
from lava.engine import PDUEngine
from lava.socketserver import DBHandler

class PDURunner():

    def __init__(self, config):
        logging.basicConfig(level=config["logging_level"])
        logging.getLogger().setLevel(config["logging_level"])
        logging.getLogger().name = "PDURunner"
        self.db = DBHandler(config["dbfile"])

    def get_one(self):
        res = self.db.get_one("SELECT * FROM pdu_queue ORDER BY id asc limit 1")
        if res:
            id,hostname,port,request = res
            logging.debug("Processing queue item: (%s %s) on hostname: %s" % (request, port, hostname))
            #logging.debug(id, hostname, request, port)
            res = self.do_job(hostname,port,request)
            self.delete_row(id)

    def delete_row(self, id):
        logging.debug("deleting row %i" % id)
        self.db.do_sql("delete from pdu_queue where id=%i" % id)

    def do_job(self, hostname, port, request):
        retries = 5
        while retries > 0:
            try:
                logging.debug("creating a new PDUEngine")
                pe = PDUEngine(hostname, 23)
                if request == "reboot":
                    pe.driver.port_reboot(port)
                elif request == "on":
                    pe.driver.port_on(port)
                elif request == "off":
                    pe.driver.port_off(port)
                elif request == "delayed":
                    pe.driver.port_delayed(port)
                else:
                    logging.debug("Unknown request type: %s" % request)
                pe.pduclose()
                retries = 0
            except:
                logging.warn("Failed to execute job: %s %s %s (attempts left %i)" % (hostname,port,request,retries))
                #logging.warn(e)
                time.sleep(5)
                retries -= 1


    def run_me(self):
        print("Starting up the PDURunner")
        while 1:
            self.get_one()
            time.sleep(1)

if __name__ == "__main__":
    starter = {"logging_level": logging.DEBUG,
               "dbfile": "/var/lib/lava-pdu/pdu.db"}
    p = PDURunner(starter)
    p.run_me()