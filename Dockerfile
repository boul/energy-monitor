FROM python:2.7-alpine

ADD / /energy-monitor
ADD /etc/energy-monitor.cfg.example /root/.energy-monitor.cfg

RUN pip install /energy-monitor



EXPOSE 5353/udp


CMD energy-monitor -s --debug
