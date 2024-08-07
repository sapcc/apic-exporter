FROM python:3.12-slim

LABEL source_repository="https://github.com/sapcc/apic-exporter"
MAINTAINER Martin Vossen <martin.vossen@sap.com>

RUN apt update && apt upgrade
RUN pip3 install --no-cache-dir --upgrade --force-reinstall pip
RUN pip3 install --no-cache-dir --upgrade --force-reinstall setuptools>=70.0.0

COPY . apic-exporter/
RUN pip3 install --no-cache-dir --upgrade --force-reinstall -r apic-exporter/requirements.txt

USER 1000
WORKDIR apic-exporter
ENTRYPOINT ["python", "exporter.py"]
