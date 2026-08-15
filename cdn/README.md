# Immutable browser distribution

This directory contains the native runtime payload used by Suvio. The
published `kmedia-wasm-engine-runtime-assets` ZIP exposes these files under
`kmedia-wasm-runtime/`:

- `kmedia-wasm.js`;
- `kmedia-wasm.wasm`;
- `kmedia-wasm-runtime.json`.

Runtime ABI 4 is declared in `kmedia-wasm-runtime.json`. A consumer must
reject a mismatched ABI before playback.

Only the three files above are tracked in `cdn/chunks/` and enter the
runtime-assets ZIP. There is no standalone JavaScript application bundle.

The complete native-shim source, exact upstream source archives, notices,
third-party licenses, build recipe, and relinking instructions are part of the
same Git tag and Maven `-sources.jar`. No proprietary player code is linked
into this runtime payload.
