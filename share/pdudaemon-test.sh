#!/bin/bash
./setup.py install
pdudaemon --loglevel=DEBUG --conf=share/pdudaemon.conf --dbfile=/tmp/dbfile &
sleep 5
curl -q "http://localhost:16421/power/control/reboot?hostname=test&port=1&delay=5" &> /dev/null
sleep 15
LINES=`cat /tmp/pdu | wc -l`
if [[ $LINES -eq 2 ]]
then
  echo "localcmdline executed ok"
  cat /tmp/pdu
  exit 0
else
  echo "localcmdline test failed"
  cat /tmp/pdu
  exit 1
fi

