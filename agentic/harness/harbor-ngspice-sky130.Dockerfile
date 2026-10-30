# ngspice 47, the latest stable release (2026-08-11), built from the official
# source; Debian bookworm only packages ngspice 39. The checksum is the one
# Homebrew's ngspice formula pins for the same tarball.
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
    && apt-get install -y --no-install-recommends bash ca-certificates libfftw3-double3 libreadline8 \
    && rm -rf /var/lib/apt/lists/*

# The agent runs commands in a login shell, which resets PATH, so link ngspice
# into /usr/local/bin rather than extending PATH.
COPY --from=ngspice /opt/ngspice /opt/ngspice
RUN ln -s /opt/ngspice/bin/ngspice /usr/local/bin/ngspice

# Only the public simulator bundle and skill. tools/export_harbor_tasks.py copies
# this Dockerfile and just these paths into each Harbor task's environment and
# adds the task's instruction and figures, so golden solutions, rubrics and the
# curated netlists never reach the agent.
COPY simulator/ngspice-sky130 /tools/ngspice-sky130
COPY agentic/skills/ngspice-sky130 /app/.claude/skills/ngspice-sky130

WORKDIR /app
CMD ["/bin/bash"]
