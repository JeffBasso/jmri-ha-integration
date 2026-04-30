ARG BUILD_ARCH=amd64
ARG BUILD_VERSION=0.1.0
FROM ghcr.io/home-assistant/${BUILD_ARCH}-base:latest

ARG BUILD_ARCH
ARG BUILD_VERSION

LABEL \
    io.hass.version="${BUILD_VERSION}" \
    io.hass.type="app" \
    io.hass.arch="${BUILD_ARCH}"

RUN apk add --no-cache bash curl openjdk17-jre coreutils xvfb ttf-dejavu fontconfig python3 py3-aiohttp

# pin to a specific production release — update both when upgrading
ARG JMRI_VERSION="5.14"
ARG JMRI_FILE="JMRI.5.14+Rdea51dcccf.tgz"
ENV JMRI_VERSION=${JMRI_VERSION}

WORKDIR /opt/jmri

RUN curl -fsSL \
    "https://github.com/JMRI/JMRI/releases/download/v${JMRI_VERSION}/${JMRI_FILE}" \
    -o /tmp/jmri.tgz \
    && tar -xzf /tmp/jmri.tgz --strip-components=1 -C /opt/jmri \
    && rm /tmp/jmri.tgz

COPY default-profile /opt/jmri/default-profile
COPY proxy.py /opt/proxy.py
COPY run.sh /run.sh
RUN chmod +x /run.sh

EXPOSE 12080

CMD ["/run.sh"]
