FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Nothing from the repository is copied in: tools/export_harbor_tasks.py adds
# each Harbor task's instruction and figures to /app.
WORKDIR /app
CMD ["/bin/bash"]
