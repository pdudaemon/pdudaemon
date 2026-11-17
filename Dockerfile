ARG DEBIAN_VERSION=trixie
FROM debian:$DEBIAN_VERSION AS base

ARG HTTP_PROXY
ARG http_proxy=${HTTP_PROXY}
ARG https_proxy=${HTTP_PROXY}

ARG PYTHON=python3

# Build pdudaemon into a venv that the later stages copy across
FROM base AS build

RUN apt-get update && apt-get install -y --no-install-recommends \
${PYTHON}-dev \
${PYTHON}-venv \
ca-certificates \
gcc \
git \
libc6-dev \
libsystemd-dev \
pkg-config \
&& rm -rf /var/lib/apt/lists/*

RUN git config --global --add safe.directory '*'

WORKDIR /pdudaemon
COPY . .
RUN ${PYTHON} -m venv /opt/pdudaemon \
&& /opt/pdudaemon/bin/pip install --no-cache-dir .

FROM build AS build-test
RUN /opt/pdudaemon/bin/pip install --no-cache-dir .[test]

# Packages and configuration shared by the test and final images
FROM base AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
${PYTHON} \
ca-certificates \
libsystemd0 \
libusb-1.0-0 \
openssh-client \
supervisor \
telnet \
snmp \
uhubctl \
&& rm -rf /var/lib/apt/lists/*

ENV PATH=/opt/pdudaemon/bin:$PATH

COPY share/pdudaemon.conf /config/
COPY share/supervisord.conf /etc/supervisor/supervisord.conf
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]

# Image used by the tests workflow: docker build --target test
FROM runtime AS test

RUN apt-get update && apt-get install -y --no-install-recommends \
curl \
git \
&& rm -rf /var/lib/apt/lists/*

RUN git config --global --add safe.directory '*'

COPY --from=build-test /opt/pdudaemon /opt/pdudaemon

FROM runtime
COPY --from=build /opt/pdudaemon /opt/pdudaemon

RUN useradd --system --create-home --home-dir /var/lib/pdudaemon \
--shell /usr/sbin/nologin pdudaemon
USER pdudaemon
WORKDIR /var/lib/pdudaemon
