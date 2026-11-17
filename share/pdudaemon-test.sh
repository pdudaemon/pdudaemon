#!/bin/bash

PDUD_BINARY=pdudaemon
TMPFILE=/tmp/pdu

rm $TMPFILE

# support the -l option for running the tests locally
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
fi

$PDUD_BINARY --loglevel=DEBUG --conf=share/pdudaemon.conf &
PDU_PID=$!

sleep 3
# Test standard HTTP request
curl -q "http://localhost:16421/power/control/reboot?hostname=http&port=2&delay=1" &> /dev/null
sleep 10

# Test alias HTTP request
curl -q "http://localhost:16421/power/control/reboot?alias=aliastesthttp01&delay=5" &> /dev/null
sleep 10

# Test pduclient
./pduclient --daemon localhost --hostname pduclient --port 3 --command reboot --delay 1
sleep 10

# the listener tests are done, and leaving it running would hold the port
# and make the next run of this script fail
kill $PDU_PID
sleep 5

# Test drive feature
$PDUD_BINARY --loglevel=DEBUG --conf=share/pdudaemon.conf --drive --hostname drive --port 4 --request reboot
# Test drive feature with alias feature
$PDUD_BINARY --loglevel=DEBUG --conf=share/pdudaemon.conf --drive --alias aliastestdrive02 --request reboot

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
