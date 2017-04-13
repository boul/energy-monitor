FROM python:2.7-alpine

ADD / /energy-monitor
ADD /etc/energy-monitor.cfg.example /root/.energy-monitor.cfg

RUN pip install /energy-monitor


CMD energy-monitor -s --debug
