FROM python:3.12-alpine

LABEL source_repository="https://github.com/sapcc/apic-exporter"
MAINTAINER Martin Vossen <martin.vossen@sap.com>

RUN pip3 install --upgrade pip

COPY . apic-exporter/
RUN pip3 install --upgrade -r apic-exporter/requirements.txt

WORKDIR apic-exporter
ENTRYPOINT ["python", "exporter.py"]