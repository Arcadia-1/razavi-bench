FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Nothing from the repository is copied in: tools/run_agentic_miniswe.py copies
# each task's instruction and figures into /app per run.
WORKDIR /app
CMD ["/bin/bash"]
