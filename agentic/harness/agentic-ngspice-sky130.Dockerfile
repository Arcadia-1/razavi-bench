FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates git ngspice \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /benchmark
COPY . /benchmark/

RUN mkdir -p /tools \
    && cp -a /benchmark/simulator/ngspice-sky130 /tools/ngspice-sky130

WORKDIR /app
CMD ["/bin/bash"]
