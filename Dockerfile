ARG DEBIAN_VERSION=trixie
FROM debian:$DEBIAN_VERSION

ARG HTTP_PROXY
ENV http_proxy=${HTTP_PROXY}
ENV https_proxy=${HTTP_PROXY}

ARG PYTHON=python3
ENV PIPX_BIN_DIR=/usr/local/bin
ENV PIPX_DEFAULT_PYTHON=${PYTHON}

RUN apt-get update && apt-get install -y \
curl \
gcc \
git \
ipmitool \
libsystemd-dev \
libusb-1.0-0 \
pkg-config \
psmisc \
pipx \
python3-pycodestyle \
python3-setuptools \
python3-usb \
python3-wheel \
supervisor \
telnet \
snmp \
uhubctl

RUN apt-get update && apt-get install -y \
  ${PYTHON}-venv ${PYTHON}-dev

RUN git config --global --add safe.directory '*'

ADD share/pdudaemon.conf /config/
WORKDIR /pdudaemon
COPY . .
RUN pipx install .[test]
CMD ["/usr/bin/supervisord", "-c", "/pdudaemon/share/supervisord.conf"]
