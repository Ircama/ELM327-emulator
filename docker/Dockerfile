# ELM327-emulator image built from the local source tree.
# Build context is the repository root (see docker-compose.yaml):
#   docker build -f docker/Dockerfile -t elm327-emulator .
FROM python:3.14-slim

WORKDIR /src
# Copy only what is needed to build and install the package
COPY setup.py pyproject.toml MANIFEST.in README.md ./
COPY elm ./elm
COPY obd_dictionary ./obd_dictionary
RUN pip install --no-cache-dir . && rm -rf /src

WORKDIR /
EXPOSE 35000
# TCP server on all interfaces, port 35000, "car" scenario
CMD ["python3", "-m", "elm", "-n", "35000", "-i", "0.0.0.0", "-s", "car"]
