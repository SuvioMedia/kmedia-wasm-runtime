# KMedia Wasm Runtime

This is the deliberately small public compliance repository for the native
WebAssembly runtime used by Suvio through KMediaPlayer. It is not a standalone
player and has no supported public API.

The repository contains only:

- the exact FFmpeg 9.0.1 source archive used by the build;
- machine-readable native object files and a prebuilt dav1d SDK sufficient to
  relink a modified FFmpeg without publishing the native shim source;
- a digest-pinned Emscripten build recipe;
- the generated loader, Wasm binary, ABI manifest, checksums, and licenses;
- a minimal Gradle publisher for
  `io.github.shusek:kmedia-wasm-engine-runtime-assets`.

There is intentionally no Kotlin implementation, TypeScript layer, npm
package, UI, application test suite, or `compose.yaml` in this repository.
The proprietary Kotlin/Wasm engine and private native sources live elsewhere.
No Kotlin/application code is linked into the native Wasm binary.

## Verify and package

JDK 25 is used by CI:

```shell
./gradlew check
./gradlew publishAllPublicationsToProjectLocalRepository
```

The local Maven repository is written to
`build/project-local-repository/`. The primary publication is a ZIP with
the three runtime files. Its real `-sources.jar` contains complete FFmpeg
source, non-LGPL relinking objects, the dav1d SDK, build recipe, checksums, and
license material.

## Rebuild the native runtime

Docker is the only additional requirement:

```shell
./gradlew verifyThirdPartySources verifyRelinkingKit
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

This repository is not licensed as a whole under Apache-2.0. Inherited
movi-player portions embedded in the object files retain Apache-2.0; the
SuvioMedia-authored portions are supplied only under the narrow permission in
[RELINKING_TERMS.md](RELINKING_TERMS.md). FFmpeg, dav1d, Signalsmith,
Emscripten, musl, LLVM runtime components, and zlib retain their own terms; see
[LICENSE](LICENSE), [NOTICE](NOTICE), and [LICENSES](LICENSES/).
