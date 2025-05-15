[![Build and Test](https://github.com/bigladder/cachebin/actions/workflows/build-and-test.yaml/badge.svg)](https://github.com/bigladder/cachebin/actions/workflows/build-and-test.yaml)

cachebin
========

`cachebin` is a python package, inspired by [DotSlash](https://dotslash-cli.com/docs/), that is designed to facilitate fetching an executable binary, verifying it (eventually!), and then running it. It maintains a local cache of fetched binaries so that subsequent invocations are fast.

Binaries are managed by a `BinaryManager` object. A growing list of such objects is maintained in [recipies.py](cachebin/recipies.py). Example usage can be found in the [test directory](test/test_cachebin.py).
