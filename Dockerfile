ARG DEBIAN_VERSION=trixie
FROM debian:$DEBIAN_VERSION

ARG HTTP_PROXY
ARG http_proxy=${HTTP_PROXY}
ARG https_proxy=${HTTP_PROXY}

ARG PYTHON=python3
ENV PIPX_BIN_DIR=/usr/local/bin
ENV PIPX_DEFAULT_PYTHON=${PYTHON}

RUN apt-get update && apt-get install -y --no-install-recommends \
${PYTHON}-dev \
${PYTHON}-venv \
ca-certificates \
curl \
gcc \
git \
libc6-dev \
libsystemd-dev \
libusb-1.0-0 \
openssh-client \
pkg-config \
pipx \
supervisor \
telnet \
snmp \
uhubctl \
&& rm -rf /var/lib/apt/lists/*

RUN git config --global --add safe.directory '*'

COPY share/pdudaemon.conf /config/
WORKDIR /pdudaemon
COPY . .
RUN pipx install .[test]
CMD ["/usr/bin/supervisord", "-c", "/pdudaemon/share/supervisord.conf"]
