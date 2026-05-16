#!/bin/bash -eu
# ClusterFuzzLite build script: install aigis + compile each fuzz harness.
# https://google.github.io/clusterfuzzlite/build-integration/python-lang/

cd "$SRC/aigis"

# Install aigis itself (zero-dependency package, very fast).
pip3 install --no-cache-dir .

# Compile each fuzz harness in .clusterfuzzlite/ into an OSS-Fuzz-compatible
# binary. `compile_python_fuzzer` is provided by the base-builder-python image.
for fuzzer in .clusterfuzzlite/fuzz_*.py; do
    fuzzer_name=$(basename "$fuzzer" .py)
    compile_python_fuzzer "$fuzzer"
    if [ -d "$SRC/aigis/.clusterfuzzlite/corpus/$fuzzer_name" ]; then
        zip -j "$OUT/${fuzzer_name}_seed_corpus.zip" \
            "$SRC/aigis/.clusterfuzzlite/corpus/$fuzzer_name"/* || true
    fi
done
