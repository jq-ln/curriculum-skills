# Changelog

## [0.1.1](https://github.com/jq-ln/curriculum-skills/compare/v0.1.0...v0.1.1) (2026-11-24)


### Features

* **build-exercises:** add Domain reference contract and assets ([#97](https://github.com/jq-ln/curriculum-skills/issues/97)) ([7d33938](https://github.com/jq-ln/curriculum-skills/commit/7d3393821f84ffc2877769c284f1919a45760452))
* **build-exercises:** add exercise format and existing ([#96](https://github.com/jq-ln/curriculum-skills/issues/96)) ([a9381cd](https://github.com/jq-ln/curriculum-skills/commit/a9381cd8e7db641c5caed46ff15013616b8eb536))
* **build-exercises:** add exercises.py context ([#94](https://github.com/jq-ln/curriculum-skills/issues/94)) ([d0ae601](https://github.com/jq-ln/curriculum-skills/commit/d0ae60137cc4dfabd804660bb3bd6e5cb823a0df))
* **build-exercises:** add exercises.py renumber and rename ([#98](https://github.com/jq-ln/curriculum-skills/issues/98)) ([7d1524a](https://github.com/jq-ln/curriculum-skills/commit/7d1524a4bb127a09a0aadf693dba6536a0fa7771))
* **build-exercises:** add the gate subcommand ([#100](https://github.com/jq-ln/curriculum-skills/issues/100)) ([7d5aee5](https://github.com/jq-ln/curriculum-skills/commit/7d5aee5059186c77c67792396a6b3c5bfc405b97))
* **build-exercises:** add the Godot Domain reference ([#101](https://github.com/jq-ln/curriculum-skills/issues/101)) ([4a94f2c](https://github.com/jq-ln/curriculum-skills/commit/4a94f2ce672680a75a0ba08df0cbef103879729c))
* **build-exercises:** add the orchestrator and its prompts ([#102](https://github.com/jq-ln/curriculum-skills/issues/102)) ([93b3b69](https://github.com/jq-ln/curriculum-skills/commit/93b3b6938026859416b2de05092b0507d18bea53))
* **build-exercises:** ramp, steer and renumber on re-runs ([#103](https://github.com/jq-ln/curriculum-skills/issues/103)) ([2037444](https://github.com/jq-ln/curriculum-skills/commit/2037444b94f2e276d9fef7d5b6d62b6818240758))


### Bug Fixes

* **build-exercises:** time out each gate run of check.sh ([#105](https://github.com/jq-ln/curriculum-skills/issues/105)) ([0df4fd7](https://github.com/jq-ln/curriculum-skills/commit/0df4fd76adc52eac076741b48ae9b79f84636e9d))

## [0.1.0](https://github.com/jq-ln/curriculum-skills/compare/v0.0.1...v0.1.0) (2026-11-23)


### ⚠ BREAKING CHANGES

* **build-curriculum:** `check` and `derive` reject a Format version 1 doc set, naming both versions. Rebuild existing Curriculums with `build-curriculum` to get Format version 2. Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Features

* **build-curriculum:** fill units true but incomplete ([#60](https://github.com/jq-ln/curriculum-skills/issues/60)) ([45fa34e](https://github.com/jq-ln/curriculum-skills/commit/45fa34e9688071751e019980e245e8a35f99cbb1))
* **build-curriculum:** Format version 2 with Part-level Needs ([#58](https://github.com/jq-ln/curriculum-skills/issues/58)) ([d18e9d3](https://github.com/jq-ln/curriculum-skills/commit/d18e9d389dc46225bd6be8282ce22156c6854732))
* **build-curriculum:** outline adds internals and capstones ([#64](https://github.com/jq-ln/curriculum-skills/issues/64)) ([d38ef2f](https://github.com/jq-ln/curriculum-skills/commit/d38ef2f6cc45d30fa73f69fa2a81a3687b7a98ef))
* **build-curriculum:** outline draws a core Part first ([#63](https://github.com/jq-ln/curriculum-skills/issues/63)) ([6c8ecbe](https://github.com/jq-ln/curriculum-skills/commit/6c8ecbe2f82da71290a951e3445e4d34891b58b5))
* **build-curriculum:** show each unit beside dependants' Goals ([#72](https://github.com/jq-ln/curriculum-skills/issues/72)) ([1511ed7](https://github.com/jq-ln/curriculum-skills/commit/1511ed79a457a27101ddf06d7a7b7363fd410405))


### Bug Fixes

* **build-curriculum:** outline Goals stay true at their depth ([#71](https://github.com/jq-ln/curriculum-skills/issues/71)) ([de51d3c](https://github.com/jq-ln/curriculum-skills/commit/de51d3cb3b373a824e7b35ae09231e145452dcff))
* **build-curriculum:** qualify Scope rules a later Goal breaks ([#70](https://github.com/jq-ln/curriculum-skills/issues/70)) ([cf78c95](https://github.com/jq-ln/curriculum-skills/commit/cf78c95e1c8113cea265b56e659026c5c3b4a54e))

## 0.0.1 (2026-11-22)


### Features

* add the build script tracer: split, derive and check ([#31](https://github.com/jq-ln/curriculum-skills/issues/31)) ([f5b6810](https://github.com/jq-ln/curriculum-skills/commit/f5b68107f9a38dea45c6ebe43e82299f30985312))
* Appendices, batched Parts and merge blocks ([#35](https://github.com/jq-ln/curriculum-skills/issues/35)) ([ae3e1a8](https://github.com/jq-ln/curriculum-skills/commit/ae3e1a84683508a33d8f5d2e4f1d4236dff2632d))
* fill fan-out, build, fix loop and cleanup ([#37](https://github.com/jq-ln/curriculum-skills/issues/37)) ([e7dc03e](https://github.com/jq-ln/curriculum-skills/commit/e7dc03ef0298f28e03668ed99876f7ed43260bf8))
* package the plugin with a build-curriculum skeleton ([#29](https://github.com/jq-ln/curriculum-skills/issues/29)) ([a35e95d](https://github.com/jq-ln/curriculum-skills/commit/a35e95dee20884dd34277160fba59cb980d4d2cf))
* re-derive a doc set after hand edits ([#36](https://github.com/jq-ln/curriculum-skills/issues/36)) ([cd19dbf](https://github.com/jq-ln/curriculum-skills/commit/cd19dbff73cf9020060524daf4369fae5e8e5aa6))
* skill inputs, outline stage and checkpoint ([#34](https://github.com/jq-ln/curriculum-skills/issues/34)) ([c777158](https://github.com/jq-ln/curriculum-skills/commit/c777158e45182a53876f35dbec0ad459bc5cf97b))
* tags in the build script ([#33](https://github.com/jq-ln/curriculum-skills/issues/33)) ([454faab](https://github.com/jq-ln/curriculum-skills/commit/454faabb3b6299cd21a388f18c733950e6695cdf))
* unit links, Prereqs and nav lines in the build script ([#32](https://github.com/jq-ln/curriculum-skills/issues/32)) ([1882e0c](https://github.com/jq-ln/curriculum-skills/commit/1882e0cc7c00b6d513784861a58b5e74c2de6f3c))
