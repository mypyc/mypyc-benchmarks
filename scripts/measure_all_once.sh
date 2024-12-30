#!/bin/bash

# Script that collects a single measurement for all benchmarks. Run as root.
#
# Run this to collect a measurement needed for normalization, after a Python
# version or hardware upgrade.
#
# See doc/benchmarks_runner.rst for more information.

repo=/srv/mypyc-benchmarks

commit="$1"
if [ -z "$commit" ]; then
    echo "usage: measure_all_once.sh <mypy-commit>"
    exit 2
fi

# Tweak settings for running benchmarks
$repo/scripts/tune.sh

sudo -u benchmark bash $repo/scripts/all_once_inner.sh "$commit"

# Restore normal settings
$repo/scripts/detune.sh
