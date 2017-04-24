FROM python:2.7-alpine

ADD / /energy-monitor
ADD /etc/energy-monitor.cfg.example /root/.energy-monitor.cfg

RUN pip install /energy-monitor

RUN apk add --update avahi && \
    sed -i 's/#enable-dbus=yes/enable-dbus=no/g' /etc/avahi/avahi-daemon.conf && \
    rm -rf /var/cache/apk/*

EXPOSE 5353/udp


CMD energy-monitor -s --debug
