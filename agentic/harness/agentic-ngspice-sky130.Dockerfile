# Only public files reach the image: each task's instruction and figures, the
# Sky130 simulator bundle and the ngspice-sky130 skill. Golden solutions, the
# rubric, data/tasks.jsonl (which embeds the golden solutions), netlists,
# sources, website data, experiments and git history stay out, so an agent with
# a shell cannot find them. The first stage drops the golden solutions before
# anything is copied into the final image.
FROM python:3.11-slim-bookworm AS tasks

COPY tasks /benchmark/tasks
RUN find /benchmark/tasks -type f ! -name instruction.md ! -name 'figure-*.png' -delete

# ngspice 47, the latest stable release (2026-08-11), built from the official
# source as in harbor-ngspice-sky130.Dockerfile; Debian bookworm only packages
# ngspice 39. The checksum is the one Homebrew's ngspice formula pins for the
# same tarball.
FROM python:3.11-slim-bookworm AS ngspice

ARG NGSPICE_VERSION=47
ARG NGSPICE_SHA256=894e649651f1838a14095e5a5439e7d3aa63e87ede14d283173fda4fcdef675f

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential bison flex ca-certificates curl libfftw3-dev libreadline-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL -o /tmp/ngspice.tar.gz "https://downloads.sourceforge.net/project/ngspice/ng-spice-rework/${NGSPICE_VERSION}/ngspice-${NGSPICE_VERSION}.tar.gz" \
    && echo "${NGSPICE_SHA256}  /tmp/ngspice.tar.gz" | sha256sum -c - \
    && tar -xzf /tmp/ngspice.tar.gz -C /tmp \
    && cd "/tmp/ngspice-${NGSPICE_VERSION}" \
    && ./configure --prefix=/opt/ngspice --with-x=no --with-readline=yes \
        --enable-cider --enable-xspice --enable-pss --enable-osdi --disable-openmp --disable-debug \
    && make -j"$(nproc)" \
    && make install

FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates git libfftw3-double3 libreadline8 \
    && rm -rf /var/lib/apt/lists/*

# Agents may run commands in a login shell, which resets PATH, so link ngspice
# into /usr/local/bin rather than extending PATH.
COPY --from=ngspice /opt/ngspice /opt/ngspice
RUN ln -s /opt/ngspice/bin/ngspice /usr/local/bin/ngspice

COPY --from=tasks /benchmark/tasks /benchmark/tasks
COPY simulator/ngspice-sky130 /benchmark/simulator/ngspice-sky130
COPY agentic/skills/ngspice-sky130 /benchmark/agentic/skills/ngspice-sky130
COPY simulator/ngspice-sky130 /tools/ngspice-sky130

WORKDIR /app
CMD ["/bin/bash"]
