# tippecanoe, for building the dashboard's PMTiles archives.
#   docker build -t tippecanoe:local build/
FROM debian:bookworm-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential git libsqlite3-dev zlib1g-dev ca-certificates \
 && git clone --depth 1 https://github.com/felt/tippecanoe.git /src \
 && make -C /src -j"$(nproc)" && make -C /src install \
 && rm -rf /src /var/lib/apt/lists/*
WORKDIR /data
ENTRYPOINT []
