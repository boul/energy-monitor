FROM python:2

ADD / /energy-monitor
ADD /etc/energy-monitor.cfg.example /root/.energy-monitor.cfg

RUN pip install /energy-monitor


CMD energy-monitor -s --debug