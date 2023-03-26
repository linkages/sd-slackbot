FROM python:3.10.10-slim
COPY requirements.txt /
RUN apt-get update && \
    apt-get install -y xz-utils procps
RUN pip3 install --upgrade pip && \
    pip3 install -r /requirements.txt
RUN mkdir /app
COPY app.py /app
COPY logging.conf /app
COPY worker.py /app

# set version for s6 overlay
ARG S6_OVERLAY_VERSION="3.1.2.1"
ARG S6_OVERLAY_ARCH="x86_64"

ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz /tmp
RUN tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-${S6_OVERLAY_ARCH}.tar.xz /tmp
RUN tar -C / -Jxpf /tmp/s6-overlay-x86_64.tar.xz

COPY s6-overlay /etc/s6-overlay

EXPOSE 8080 8000
ENTRYPOINT ["/init"]
