FROM python:3.7
COPY . /asperathos-monitor
WORKDIR /asperathos-monitor
RUN pip install setuptools tox flake8
ENTRYPOINT ./run.sh
