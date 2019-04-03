FROM debian:buster

ARG HTTP_PROXY
ENV http_proxy ${HTTP_PROXY}
ENV https_proxy ${HTTP_PROXY}

RUN apt-get update && apt-get install -y \
curl \
cython3 \
libffi-dev \
libhidapi-dev \
libsystemd-dev \
libudev-dev \
libusb-1.0-0-dev \
pkg-config \
psmisc \
python3-pip \
python3-setuptools \
python3-usb \
python3-wheel \
supervisor \
telnet \
snmp

ADD share/pdudaemon.conf /config/
WORKDIR /pdudaemon
COPY . .
RUN pip3 install --user -r ./requirements.txt
RUN python3 ./setup.py install
CMD ["/usr/bin/supervisord", "-c", "/pdudaemon/share/supervisord.conf"]
