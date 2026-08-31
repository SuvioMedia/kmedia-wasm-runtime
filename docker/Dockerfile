# Multi-arch manifest pinned to Emscripten 6.0.4. Docker still selects the
# host-native amd64/arm64 image, but the toolchain cannot move underneath us.
FROM emscripten/emsdk:6.0.4@sha256:3a0d11e50f072dc2c4bc92e3b05ab1340fb7d4dd152f80b8af35fc1c6f15e644

LABEL maintainer="SuvioMedia"
LABEL description="FFmpeg Wasm build environment for KMedia Wasm Engine"
LABEL org.opencontainers.image.source="https://github.com/SuvioMedia/kmedia-wasm-runtime"
LABEL io.suvio.ffmpeg.commit="bf1b838f2ab88b4f8fd83443325c782ea0e0f7fa"
LABEL io.suvio.dav1d.commit="b546257f770768b2c88258c533da38b91a06f737"

# Install only the tools needed to rebuild FFmpeg. dav1d is supplied as a
# prebuilt BSD-licensed library in the relinking kit.
RUN apt-get update && apt-get install -y \
    make \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src

# This is the exact LGPL source archive shipped in the Maven sources JAR.
COPY third-party-sources/ffmpeg-9.0.1.tar.gz /tmp/ffmpeg-9.0.1.tar.gz
RUN echo "fb1931fd4eb29297ee1c1017a24f800c4d8fbea35b4f2aaeb28308a48a9149b4  /tmp/ffmpeg-9.0.1.tar.gz" | sha256sum -c - \
    && mkdir -p /opt/FFmpeg \
    && tar -xzf /tmp/ffmpeg-9.0.1.tar.gz --strip-components=1 -C /opt/FFmpeg \
    && test "$(cat /opt/FFmpeg/RELEASE)" = "9.0.1" \
    && rm /tmp/ffmpeg-9.0.1.tar.gz

# Build script.
COPY docker/build-ffmpeg.sh /opt/build-ffmpeg.sh
RUN chmod +x /opt/build-ffmpeg.sh

ENV FFMPEG_SRC=/opt/FFmpeg

CMD ["/opt/build-ffmpeg.sh"]
