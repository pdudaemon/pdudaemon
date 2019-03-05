FROM debian:buster

RUN apt-get update && apt-get install -y libsystemd-dev \
                                         curl \
                                         psmisc \
                                         pkg-config \
                                         libffi-dev \
                                         libhidapi-dev \
                                         libudev-dev \
                                         libusb-1.0-0-dev \
                                         cython3

RUN apt-get install --no-install-recommends -y python3-pip python3-setuptools python3-wheel
ADD requirements.txt /
RUN pip3 install --user -r /requirements.txt
RUN pip3 install --user pycodestyle
