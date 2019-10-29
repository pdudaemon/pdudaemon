#!/bin/bash

PDUD_BINARY=pdudaemon
TMPFILE=/tmp/pdu

while getopts l option
do
  case "${option}" in
    l)
      LOCAL=true
      ;;
  esac
done

#empty the tempfile, helpful if running locally
if [ $LOCAL ]
then
  cp pdudaemon/__init__.py ./pdudaemon-test-bin
  chmod +x ./pdudaemon-test-bin
  PDUD_BINARY=./pdudaemon-test-bin
  echo -n "" > $TMPFILE
fi

$PDUD_BINARY --loglevel=DEBUG --conf=share/pdudaemon.conf --dbfile=/tmp/dbfile &
PDU_PID=$!

sleep 2
curl -q "http://localhost:16421/power/control/reboot?hostname=test&port=1&delay=5" &> /dev/null
sleep 10

if [ $LOCAL ]
then
  # kill the running daemon after first test, helpful if running locally
  kill $PDU_PID
  sleep 5
fi

$PDUD_BINARY --loglevel=DEBUG --conf=share/pdudaemon.conf --drive --hostname drivetest --port 1 --request reboot

if [ $LOCAL ]
then
  rm $PDUD_BINARY
fi

echo "#### Created output ####"
cat $TMPFILE
echo ""
echo "#### Expected output ####"
cat share/expected_output.txt
echo ""

diff -q -u share/expected_output.txt $TMPFILE
exit $?
