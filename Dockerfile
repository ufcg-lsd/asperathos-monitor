FROM python:2.7

RUN pip install setuptools tox flake8

COPY . /asperathos-monitor/

WORKDIR /asperathos-monitor

ENTRYPOINT ./run.sh
