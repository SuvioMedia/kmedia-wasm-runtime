# FFmpeg/WebAssembly source and relinking

The `io.github.shusek:kmedia-wasm-engine-runtime-assets` Maven artifact contains
`kmedia-wasm-runtime/kmedia-wasm.wasm` and its Emscripten loader. The WebAssembly
binary statically combines FFmpeg libraries configured as LGPL-2.1-or-later
with a non-LGPL work. GPL and non-free FFmpeg components are not enabled.

LGPL-2.1 section 6(a) permits that non-LGPL work to be supplied as object code
rather than source, provided recipients can modify FFmpeg and relink a working
executable. Accordingly, every runtime version publishes this minimal kit in
the durable Maven Central classifier
`io.github.shusek:kmedia-wasm-engine-runtime-assets:<version>:sources@jar`:

- `third-party-sources/ffmpeg-9.0.1.tar.gz` — complete, unmodified source for
  exact FFmpeg commit `bf1b838f2ab88b4f8fd83443325c782ea0e0f7fa`;
- `relink/objects/*.o` — the complete machine-readable work that uses FFmpeg;
- `relink/dav1d/` — the exact prebuilt BSD-2-Clause dav1d library and public
  headers used by the FFmpeg build;
- `relink/SHA256SUMS` and `third-party-sources.properties` — pinned inputs;
- `docker/Dockerfile` and `docker/build-ffmpeg.sh` — the complete FFmpeg
  configure, compile, and final-link recipe using Emscripten 6.0.4;
- `RELINKING_TERMS.md`, notices, and all applicable license texts.

Native shim, Signalsmith, Kotlin, and TypeScript source are deliberately not
part of this kit. The object-code permission in `RELINKING_TERMS.md` allows the
modification and reverse engineering needed for a recipient's own relinking
and debugging, while all inherited and third-party rights remain intact.

## Reproduce the distributed binary

Download and extract the sources JAR, then run from its root:

```shell
echo "fb1931fd4eb29297ee1c1017a24f800c4d8fbea35b4f2aaeb28308a48a9149b4  third-party-sources/ffmpeg-9.0.1.tar.gz" | sha256sum -c -
(cd relink && sha256sum -c SHA256SUMS)
mkdir -p dist/wasm
docker build --file docker/Dockerfile --tag kmedia-wasm-runtime-relink .
docker run --rm --volume "$PWD:/src" kmedia-wasm-runtime-relink
```

The output is `dist/wasm/kmedia-wasm.js` and
`dist/wasm/kmedia-wasm.wasm`. Its checksums must match `cdn/SHA256SUMS`.

## Relink a modified FFmpeg

Extract `third-party-sources/ffmpeg-9.0.1.tar.gz` to a writable directory,
make the desired changes, and mount that directory over `/opt/FFmpeg`:

```shell
mkdir modified-ffmpeg
tar -xzf third-party-sources/ffmpeg-9.0.1.tar.gz \
  --strip-components=1 --directory modified-ffmpeg
docker build --file docker/Dockerfile --tag kmedia-wasm-runtime-relink .
docker run --rm \
  --env FORCE_FFMPEG=true \
  --volume "$PWD:/src" \
  --volume "$PWD/modified-ffmpeg:/opt/FFmpeg" \
  kmedia-wasm-runtime-relink
```

The same script rebuilds the modified LGPL libraries and combines them with
the supplied object files to produce a modified runtime. FFmpeg licensing
information is at `https://ffmpeg.org/legal.html`. Nothing in this document
changes LGPL-2.1-or-later or any other included license.
