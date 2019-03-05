# PDUDaemon
Python daemon for controlling/sequentially executing commands to PDUs (Power Distribution Units)
## Why is this needed?
#### Queueing
Most PDUs have a very low power microprocessor, or low quality software, which cannot handle multiple requests at the same time. This quickly becomes an issue in environments that use power control frequently, such as board farms, and gets worse on PDUs that have a large number of controllable ports.
#### Standardising
Every PDU manufacturer has a different way of controlling their PDUs. Though many support SNMP, there's still no single simple way to communicate with all PDUs if you have a mix of brands.
## Supported devices list
APC, Devantech and ACME are well supported, however there is no official list yet. The [strategies.py](https://github.com/pdudaemon/pdudaemon/blob/master/pdudaemon/drivers/strategies.py) file is a good place to see all the current drivers.
## Installing
Debian packages are on the way, hopefully.
For now, make sure the requirements are met and then:
```python3 setup.py install```
## Config file
To be added.
## Making a power control request
- **HTTP**
The daemon can accept requests over plain HTTP. The port is configurable, but defaults to 16421
There is no encryption or authentication, consider yourself warned.
To enable, change the 'listener' setting in the 'daemon' section of the config file to 'http'. This will break 'pduclient' requests.
An HTTP request URL has the following syntax:

  ```http://<pdudaemon-hostname>:<pdudaemon-port>/power/control/<command>?<query-string>```

  Where:
    - pdudaemon-hostname is the hostname or IP address where pdudaemon is running (e.g.: localhost)
    - pdudaemon-port is the port used by pdudaemon (e.g.: 16421)
    - command is an action for the PDU to execute:
      - **on**: power on
      - **off**: power off
      - **reboot**: reboot
    - query-string can have 3 parameters (same as pduclient, see below)
      - **hostname**: the PDU hostname or IP address used in the [configuration file](https://github.com/pdudaemon/pdudaemon/blob/master/share/pdudaemon.conf) (e.g.: "192.168.10.2")
      - **port**: the PDU port number
      - **delay**: delay before a command runs (optional, by default 5 seconds)

  Some example requests would be:
  ```
  $ curl "http://localhost:16421/power/control/on?hostname=192.168.10.2&port=1"
  $ curl "http://localhost:16421/power/control/off?hostname=192.168.10.2&port=1"
  $ curl "http://localhost:16421/power/control/reboot?hostname=192.168.10.2&port=1&delay=10"
  ```

  ***Return Codes***

    - HTTP 200 - Request Accepted
    - HTTP 503 - Invalid Request, Request not accepted

- **pduclient**
The bundled client is used when PDUDaemon is configured to listen to 'tcp' requests.
```
Usage: pduclient --daemon deamonhostname --hostname pduhostname --port pduportnum --command pducommand

PDUDaemon client

Options:
  -h, --help            show this help message and exit
  --daemon=PDUDAEMONHOSTNAME
                        PDUDaemon listener hostname (ex: localhost)
  --hostname=PDUHOSTNAME
                        PDU Hostname (ex: pdu05)
  --port=PDUPORTNUM     PDU Portnumber (ex: 04)
  --command=PDUCOMMAND  PDU command (ex: reboot|on|off)
  --delay=PDUDELAY      Delay before command runs, or between off/on when
                        rebooting (ex: 5)
```
## Adding drivers
PDUDaemon was written to accept "plugin" style driver files. There's no official example yet, so take a look in the [drivers](https://github.com/pdudaemon/pdudaemon/tree/master/pdudaemon/drivers) directory and see if you can adapt one.
## Why can't PDUDaemon do $REQUIREMENT?
Patches welcome, as long as it keeps the system simple and lightweight.
## Contact
#pdudaemon on Freenode
