FROM python:3.14-slim

LABEL source_repository="https://github.com/sapcc/apic-exporter"
LABEL maintainer="Tommy Sauer <tommy.sauer@sap.com>"

RUN apt-get update \
 && apt-get upgrade -y \
 && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --upgrade pip "setuptools>=78.1.1"

WORKDIR /apic-exporter

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

USER 1000
ENTRYPOINT ["python", "exporter.py"]
