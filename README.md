# PDUDaemon
Python daemon for controlling/sequentially executing commands to PDUs (Power Distribution Units)
## License
PDUDaemon is licensed under GPL 2.0 or any later version.
## Why is this needed?
#### Queueing
Most PDUs have a very low power microprocessor, or low quality software, which cannot handle multiple requests at the same time. This quickly becomes an issue in environments that use power control frequently, such as board farms, and gets worse on PDUs that have a large number of controllable ports.
#### Standardising
Every PDU manufacturer has a different way of controlling their PDUs. Though many support SNMP, there's still no single simple way to communicate with all PDUs if you have a mix of brands.
## Supported devices list
APC, Devantech and ACME are well supported, however there is no official list yet. The [strategies.py](https://github.com/pdudaemon/pdudaemon/blob/main/pdudaemon/drivers/strategies.py) file is a good place to see all the current drivers.
## Installing
Debian packages are on the way, hopefully.

## Device access
Before installing, create a dedicated system user and group for pdudaemon:

```
sudo groupadd --system pdudaemon
sudo useradd --system --gid pdudaemon --home-dir /nonexistent --shell /usr/sbin/nologin --comment "pdudaemon service user" pdudaemon
```

Then install the udev rules for any devices you wish for pdudaemon to access:

```
sudo cp share/80-*.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

For now, make sure the requirements are met and then:

```python3 setup.py install```

There is an official Docker container updated from tip:
```
$ docker pull pdudaemon/pdudaemon:latest
$ vi pdudaemon.conf
```
To create a config file, use [share/pdudaemon.conf](https://github.com/pdudaemon/pdudaemon/blob/main/share/pdudaemon.conf) as a base, then mount your config file on top of the default:
```
$ docker run -v `pwd`/pdudaemon.conf:/config/pdudaemon.conf pdudaemon/pdudaemon:latest
```

Or you can build your own:
```
$ git clone https://github.com/pdudaemon/pdudaemon
$ cd pdudaemon
$ vi share/pdudaemon.conf
	- configure your PDUs
$ sudo docker build -t pdudaemon --build-arg HTTP_PROXY=$http_proxy -f Dockerfile .
$ docker run --rm -it -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e NO_PROXY="$no_proxy" --net="host" pdudaemon:latest
```

## Config file
An example configuration file can be found [here](https://github.com/pdudaemon/pdudaemon/blob/main/share/pdudaemon.conf).
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
Each PDU name must be unique, pdudaemon refuses to start if a name is used more than once.
For the `localcmdline` driver, a `%` placeholder such as `%s` or `%i` in `cmd_on`/`cmd_off` is replaced with the requested port number; it can be left out entirely for devices which only have a single port.
Named placeholders such as `%(serial)s` are replaced with the PDU setting of that name, and `%(port)s` and `%(hostname)s` with the requested port and the PDU name.
An optional `cmd_state` command, using the same placeholders, implements `get-port-state`: it must exit with status 0 and print `on` when the port is powered on, or `off` when it is powered off. Any other exit status or output is an error.
Any PDU can have an optional `port_count` setting, the number of ports of the PDU, which is used if the driver doesn't already know how many ports the PDU has. The ports are numbered from 1, or from the driver's first port if it knows it; `"first_port"` (0 or 1) overrides this.
An optional `port_names` setting lists the names of the ports of the PDU, for drivers which identify ports by name rather than number (e.g. `"port_names": ["switch.board1", "switch.board2"]`). It is independent of `port_count`.
Both settings are used to list the ports in [Port Status](#making-a-power-control-request), and requests for a port the PDU doesn't have are rejected. If neither is set and the driver doesn't know the ports of the PDU, a warning is logged at startup and shown in Port Status and the Web UI, and requests can't be checked, so a warning is logged for every request.
Drivers which talk to the PDU over HTTP or a TCP socket give up on a request if the PDU doesn't connect or respond within 10 seconds (60 for `servertechpro2`); an optional `timeout` setting, in seconds, overrides this. A request which times out is retried like any other failed request.
For some (or most) network connected devices, it needs to be the actual hostname or IP address the PDU responds to (see `query-string` in [next section](#making-a-power-control-request)).
The correct value for `driver` is highly dependent on the used child class and the specific implementation.
Check the imported [Python module](https://github.com/pdudaemon/pdudaemon/tree/main/pdudaemon/drivers) for that class and look for `drivername` to be sure.
Some drivers require additional parameters (like a device ID).
Which parameters are required can also be extracted from the associated python module and child class definition.
It is also worth checking out the [share](https://github.com/pdudaemon/pdudaemon/tree/main/share) folder for some driver specific example configuration files and helpful scripts that can help prevent major headaches!

The optional `aliases` section names ports of the PDUs, so requests can use the alias (`alias=<name>` in HTTP requests, or `--alias <name>` with `--drive`) instead of the hostname and port. For example:

```json
  "aliases": {
      "board1": {
          "hostname": "192.168.0.42",
          "port": 1
      },
      "board2": {
          "hostname": "test",
          "port": "board2"
      }
  }
```
The `port` can be a port number or a port name (e.g. one of the `port_names` of the PDU).
Each alias name must be unique, its `hostname` must be one of the PDUs in the `pdus` section, and its `port` must be one of the ports of that PDU if they are known (see `port_count` and `port_names` above), otherwise pdudaemon refuses to start.

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
      - **get-cached-port-state**: return the last known powered state of the port (see the `Get cached port state` section below)
      - **get-port-state**: retrieve the powered state of the port (see the `Get port state` section below)
    - query-string can have 3 parameters (same as pduclient, see below)
      - **hostname**: the PDU hostname or IP address used in the [configuration file](https://github.com/pdudaemon/pdudaemon/blob/main/share/pdudaemon.conf) (e.g.: "192.168.10.2")
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

  ***Port Status***

  The cached state of each port (see the `Get cached port state` section below) is available as JSON from `/power/status` (or `/power/status/json`). Every PDU in the config file is listed with its driver and ports. Ports are listed if the driver knows the PDU has them, if they are in the `aliases` section of the config file, or if their state is known; they show as `unknown` until their state is known. Ports in the `aliases` section also include their alias name. `get_port_state` is `true` if the driver supports [`get-port-state`](#get-port-state) for the PDU. A PDU whose ports aren't known from the driver, `port_count` or `port_names` also has a `warning`. Add `?hostname=<pdu-hostname>` to only show one PDU.
  ```
  $ curl "http://localhost:16421/power/status"
  {"192.168.10.2": {"driver": "tasmota", "get_port_state": true, "ports": {"1": {"state": "on", "alias": "board1"}, "2": {"state": "off"}}}}
  ```

  ***Daemon Info***

  Information about the daemon itself is available as JSON from `/power/info`: `hostname` is the hostname of the machine running PDUDaemon and `version` is the version of PDUDaemon, or `unknown` if it isn't installed as a package, and `uptime` is the number of seconds since the daemon started.
  ```
  $ curl "http://localhost:16421/power/info"
  {"hostname": "lab-host", "version": "1.2.0", "uptime": 3600}
  ```

  ***Web UI***

  A web page showing the same status and the hostname, version and uptime from [Daemon Info](#making-a-power-control-request), with buttons to switch each port on or off, to reset it (off, then on again after 5 seconds), or to read its state from the PDU (disabled if the driver doesn't support `get-port-state`), is available from `/power/dashboard`, which `/` also redirects to. The result of each request is shown above the table, in red if it failed. It refreshes the status every 5 seconds, and also accepts `?hostname=<pdu-hostname>`. It is disabled by default; to enable it, set `"web_ui": true` in the 'daemon' section of the config file.

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
  --command=PDUCOMMAND  PDU command (ex: reboot|on|off|get-cached-port-state|get-port-state)
  --delay=PDUDELAY      Delay before command runs, or between off/on when
                        rebooting (ex: 5)
```

- **non-daemon (also called drive)**
If you would just like to use pdudaemon as an executable to drive a PDU without needing to run a daemon, you can use the --drive option.
Configure the PDU in the config file as usual, then launch pdudaemon with the following options
```
$ pdudaemon --conf=share/pdudaemon.conf --drive --hostname pdu01 --port 1 --request reboot
```

If requesting reboot, the delay between turning the port off and on can be modified with `--delay`
and is by default 5 seconds.

## Get cached port state
pdudaemon remembers the last known powered state of each port. It is updated every time an `on`, `off`,
`reboot` or `get-port-state` request succeeds. `get-cached-port-state` returns this cached state without
querying the PDU, so it works with every driver and returns immediately.

The cached state is lost when pdudaemon restarts, and it can be out of date if the port was switched
by something other than pdudaemon. A port with no known state reports `unknown`. Use
`get-port-state` to read the actual state from the PDU.

- **HTTP**

  ```
  $ curl "http://localhost:16421/power/control/get-cached-port-state?hostname=192.168.10.2&port=1"
  {"state": "on"}
  ```

  The response body is a JSON object with a single `state` key, one of `on`, `off` or `unknown`.

- **pduclient (TCP)**

  ```
  $ pduclient --daemon localhost --hostname 192.168.10.2 --port 1 --command get-cached-port-state
  Port state: unknown
  ```

## Get port state
pdudaemon can retrieve a port's powered state (on or off), if it is supported by the driver.
Not all drivers implement status retrieval; unsupported drivers will return an error.

- **HTTP**

  Send a `GET` request to the `get-port-state` endpoint with the same `hostname` and `port` query parameters used for control commands:

  ```
  $ curl "http://localhost:16421/power/control/get-port-state?hostname=192.168.10.2&port=1"
  {"state": "on"}
  ```

  The response body is a JSON object with a single `state` key:
  - `on` - port is powered **on**
  - `off` - port is powered **off**

  HTTP 200 is returned when the state was read from the PDU. HTTP 500 is returned if the request is invalid or the driver does not support status retrieval.

- **pduclient (TCP)**

  Use `get-port-state` as the command, with or without the `--http` flag:

  ```
  $ pduclient --daemon localhost --hostname 192.168.10.2 --port 1 --command get-port-state
  Port state: on
  ```

- **non-daemon (--drive)**

  ```
  $ pdudaemon --conf=share/pdudaemon.conf --drive --hostname pdu01 --port 1 --request get-port-state
  ```

## Adding drivers
Drivers are implemented children of the "PDUDriver" class and many example
implementations can be found inside the
[drivers](https://github.com/pdudaemon/pdudaemon/tree/main/pdudaemon/drivers)
directory.
Any new driver classes should be added to [strategies.py](https://github.com/pdudaemon/pdudaemon/blob/main/pdudaemon/drivers/strategies.py).

External implementation of PDUDriver can also be registered using the python
entry_points mechanism. For example add the following to your setup.cfg:
```
[options.entry_points]
pdudaemon.driver =
    mypdu = mypdumod:MyPDUClass
```

## Why can't PDUDaemon do $REQUIREMENT?
Patches welcome, as long as it keeps the system simple and lightweight.
