# KMedia Wasm runtime fork

KMedia Wasm Engine is derived from
[`mrujjwalg/movi-player`](https://github.com/mrujjwalg/movi-player) and is not affiliated with or
endorsed by its maintainer. The last historical npm fork release, `0.3.5-kmp.3`, was based on
upstream commit `dfa30c95f59a8aa118b507639cff6ddb049878b8`.

The historical standalone TypeScript/npm product is not part of this repository. This repository
contains only the native C/C++ runtime, its generated loader/Wasm payload, and the source and build
materials needed to reproduce and relink that payload.

There is no player API or compatibility promise here. Inherited material remains subject to its
original Apache-2.0 terms, while third-party components remain under the terms recorded in
[LICENSE](LICENSE), [NOTICE](NOTICE), and [LGPL_RELINKING.md](LGPL_RELINKING.md).
