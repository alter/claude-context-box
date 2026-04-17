FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
COPY . /work/source
RUN chmod +x /work/source/tests/e2e/run_local_e2e.sh

CMD ["bash", "/work/source/tests/e2e/run_local_e2e.sh"]
