# FFmpeg/WebAssembly source and relinking

The `io.github.shusek:kmedia-wasm-engine-runtime-assets` Maven artifact contains
`kmedia-wasm-runtime/kmedia-wasm.wasm` and its Emscripten loader. The WebAssembly binary combines
the open native C/C++ shim with FFmpeg libraries configured under LGPL-2.1-or-later. GPL and
non-free FFmpeg components are not enabled. No proprietary player code is linked into this native
WebAssembly binary.

Every runtime version publishes its corresponding source and relinking materials as the durable
Maven Central classifier
`io.github.shusek:kmedia-wasm-engine-runtime-assets:<version>:sources@jar`. It contains:

- `wasm/` — the open native C/C++ shim and JavaScript I/O library;
- `third-party-sources/ffmpeg-9.0.1.tar.gz` — exact FFmpeg commit
  `bf1b838f2ab88b4f8fd83443325c782ea0e0f7fa`;
- `third-party-sources/dav1d-1.5.3.tar.gz` — exact dav1d commit
  `b546257f770768b2c88258c533da38b91a06f737`;
- `third-party-sources.properties` — archive origins, commits, and SHA-256 values;
- `docker/Dockerfile` — Emscripten 6.0.4 pinned to a multi-architecture image digest;
- `docker/build-ffmpeg.sh` — the complete configure, compile, export, and link commands;
- the applicable notices and full LGPL 2.1 license text.

Download and extract that sources JAR, then run from its root:

```shell
./gradlew verifyThirdPartySources
mkdir -p dist/wasm
docker build --file docker/Dockerfile --tag kmedia-wasm-runtime-build .
docker run --rm --volume "$PWD:/src" kmedia-wasm-runtime-build
```

The native build produces `dist/wasm/kmedia-wasm.js` and `dist/wasm/kmedia-wasm.wasm`. To prepare a
new runtime release, copy those outputs to `cdn/chunks/kmedia-wasm.js` and
`cdn/chunks/kmedia-wasm.wasm`, update `cdn/chunks/kmedia-wasm-runtime.json` with the exact FFmpeg
version and Wasm SHA-256, refresh their entries in `cdn/SHA256SUMS`, and run:

```shell
./gradlew check runtimeArchive
```

Gradle verifies the pinned bytes and the complete corresponding-source classifier before creating
the Maven ZIP. The source JAR is published beside that ZIP and remains available from Maven
Central. The same materials are retained in this public repository and its immutable release tag.

FFmpeg licensing information is at `https://ffmpeg.org/legal.html`. Nothing in this document
changes the terms of LGPL-2.1-or-later or any other included license.
