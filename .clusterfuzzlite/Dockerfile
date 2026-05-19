FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:e24e8e50612617101dd10038502f68268ab45f31d79a3722c230464277a951b3

# Install minimal build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
    && rm -rf /var/lib/apt/lists/*

# Copy the project sources
COPY . $SRC/aigis
WORKDIR $SRC/aigis

# Copy build.sh into the canonical location ClusterFuzzLite expects
COPY .clusterfuzzlite/build.sh $SRC/
