# KMedia Wasm Runtime

This is the deliberately small public compliance repository for the native
WebAssembly runtime used by Suvio through KMediaPlayer. It is not a standalone
player and has no supported public API.

The repository contains only:

- the inherited C/C++ native shim and Emscripten I/O library under `wasm/`;
- the exact FFmpeg 9.0.1 and dav1d 1.5.3 source archives used by the build;
- a digest-pinned Emscripten build recipe;
- the generated loader, Wasm binary, ABI manifest, checksums, and licenses;
- a minimal Gradle publisher for
  `io.github.shusek:kmedia-wasm-engine-runtime-assets`.

There is intentionally no Kotlin implementation, TypeScript layer, npm
package, UI, application test suite, or `compose.yaml` in this repository.
The proprietary Kotlin/Wasm engine lives elsewhere and is not linked into the
native Wasm binary.

## Verify and package

JDK 25 is used by CI:

```shell
./gradlew check
./gradlew publishAllPublicationsToProjectLocalRepository
```

The local Maven repository is written to
`build/project-local-repository/`. The primary publication is a ZIP with
the three runtime files. Its real `-sources.jar` contains the native source,
build recipe, exact upstream source archives, checksums, and license material.

## Rebuild the native runtime

Docker is the only additional requirement:

```shell
./gradlew verifyThirdPartySources
mkdir -p dist/wasm
docker build --file docker/Dockerfile --tag kmedia-wasm-runtime-build .
docker run --rm --volume "$PWD:/src" kmedia-wasm-runtime-build
```

The output is written to `dist/wasm/`. See
[LGPL_RELINKING.md](LGPL_RELINKING.md) for the exact relinking and release
procedure.

## Scope and support

Suvio is the only supported consumer. This repository exists to keep the
redistributable runtime and legally required source material durably public;
it does not create an npm/JavaScript product or compatibility commitment.

The native shim retains its inherited Apache-2.0 terms. FFmpeg, dav1d,
Signalsmith, Emscripten, musl, and zlib remain under their own licenses; see
[LICENSE](LICENSE), [NOTICE](NOTICE), and [LICENSES/LGPL-2.1.txt](LICENSES/LGPL-2.1.txt).
