# KMedia Wasm runtime fork

KMedia Wasm Engine is derived from
[`mrujjwalg/movi-player`](https://github.com/mrujjwalg/movi-player) and is not affiliated with or
endorsed by its maintainer. The last historical npm fork release, `0.3.5-kmp.3`, was based on
upstream commit `dfa30c95f59a8aa118b507639cff6ddb049878b8`.

The historical standalone TypeScript/npm product is not part of this repository. This repository
contains the generated loader/Wasm payload, complete FFmpeg source, and the minimal object/build
materials needed to reproduce and relink that payload. Native shim and Signalsmith source are
maintained privately.

There is no player API or compatibility promise here. Inherited portions embedded in the object
files remain subject to Apache-2.0, while other components and the relinking objects remain under
the terms recorded in [LICENSE](LICENSE), [RELINKING_TERMS.md](RELINKING_TERMS.md),
[NOTICE](NOTICE), and [LGPL_RELINKING.md](LGPL_RELINKING.md).
