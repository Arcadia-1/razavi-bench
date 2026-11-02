# Only the public task inputs, each task's instruction and figures, reach the
# image. Golden solutions, the rubric, data/tasks.jsonl (which embeds the golden
# solutions), netlists, sources, website data, experiments and git history stay
# out, so an agent with a shell cannot find them. The first stage drops the
# golden solutions before anything is copied into the final image.
FROM python:3.11-slim-bookworm AS tasks

COPY tasks /benchmark/tasks
RUN find /benchmark/tasks -type f ! -name instruction.md ! -name 'figure-*.png' -delete

FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=tasks /benchmark/tasks /benchmark/tasks

WORKDIR /app
CMD ["/bin/bash"]
