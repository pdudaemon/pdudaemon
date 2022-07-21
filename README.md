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

There is an official Docker container updated from tip:
```
$ docker pull pdudaemon/pdudaemon:latest
$ vi pdudaemon.conf
```
To create a config file, use [share/pdudaemon.conf](https://github.com/pdudaemon/pdudaemon/blob/master/pdudaemon/share/pdudaemon.conf) as a base, then mount your config file on top of the default:
```
$ docker run -v `pwd`/pdudaemon.conf:/config/pdudaemon.conf pdudaemon/pdudaemon:latest
```

Or you can build your own:
```
$ git clone https://github.com/pdudaemon/pdudaemon
$ cd pdudaemon
$ vi share/pdudaemon.conf
	- configure your PDUs
$ sudo docker build -t pdudaemon --build-arg HTTP_PROXY=$http_proxy -f Dockerfile.dockerhub .
$ docker run --rm -it -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e NO_PROXY="$no_proxy" --net="host" pdudaemon:latest
```

## Config file
An example configuration file can be found [here](https://github.com/pdudaemon/pdudaemon/blob/master/share/pdudaemon.conf).
The section `daemon` is pretty self explanatory. The interesting part is the `pdus` section, where
all managed PDUs are listed and configured. For example:

```json
  "pdus": {
      "hostname_or_ip": {
          "driver": "driver_name",
          "additional_parameter": "42"
      },
      "test": {
          "driver": "localcmdline",
          "cmd_on": "echo '%s on' >> /tmp/pdu",
          "cmd_off": "echo '%s off' >> /tmp/pdu"
      },
      "energenie": {
          "driver": "EG-PMS",
          "device": "01:01:51:a4:c3"
      },
      "192.168.0.42": {
          "driver": "brennenstuhl_wspl01_tasmota"
      }
  }
```
It is important to mention, that `hostname` can be an arbitrary name for a locally connected device (like `energenie` in this example).
For some (or most) network connected devices, it needs to be the actual hostname or IP address the PDU responds to (see `query-string` in [next section](#making-a-power-control-request)).
The correct value for `driver` is highly dependent on the used child class and the specific implementation.
Check the imported [Python module](https://github.com/pdudaemon/pdudaemon/tree/main/pdudaemon/drivers) for that class and look for `drivername` to be sure.
Some drivers require additional parameters (like a device ID).
Which parameters are required can also be extracted from the associated python module and child class definition.
It is also worth checking out the [share](https://github.com/pdudaemon/pdudaemon/tree/main/share) folder for some driver specific example configuration files and helpful scripts that can help prevent major headaches!

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
      - **delay**: delay between power off and on during reboot (optional, by default 5 seconds)

  Some example requests would be:
  ```
  $ curl "http://localhost:16421/power/control/on?hostname=192.168.10.2&port=1"
  $ curl "http://localhost:16421/power/control/off?hostname=192.168.10.2&port=1"
  $ curl "http://localhost:16421/power/control/reboot?hostname=192.168.10.2&port=1&delay=10"
  ```

  ***Return Codes***

    - HTTP 200 - Request Accepted
    - HTTP 503 - Invalid Request, Request not accepted

- **TCP (legacy pduclient)**
The bundled client is used when PDUDaemon is configured to listen to 'tcp' requests. TCP support is considered legacy but will remain functional.
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

- **non-daemon (also called drive)**
If you would just like to use pdudaemon as an executable to drive a PDU without needing to run a daemon, you can use the --drive option.
Configure the PDU in the config file as usual, then launch pdudaemon with the following options
```
$ pdudaemon --conf=share/pdudaemon.conf --drive --hostname pdu01 --port 1 --request reboot
```

## Adding drivers
Drivers are implemented children of the "PDUDriver" class and many example
implementations can be found inside the
[drivers](https://github.com/pdudaemon/pdudaemon/tree/master/pdudaemon/drivers)
directory.
Any new driver classes should be added to [strategies.py](https://github.com/pdudaemon/pdudaemon/blob/master/pdudaemon/drivers/strategies.py).

External implementation of PDUDriver can also be registered using the python
entry_points mechanism. For example add the following to your setup.cfg:
```
[options.entry_points]
pdudaemon.driver =
    mypdu = mypdumod:MyPDUClass
```

## Why can't PDUDaemon do $REQUIREMENT?
Patches welcome, as long as it keeps the system simple and lightweight.
## Contact
#pdudaemon on Freenode
