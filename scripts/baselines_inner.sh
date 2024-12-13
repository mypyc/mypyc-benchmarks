#!/bin/bash

user=benchmark

if [ "$(whoami)" != $user ]; then
    echo "error: This script must be run as user '$user'"
    exit 1
fi

set -eux

base=/srv

source $base/venv/bin/activate

cd $base/mypyc-benchmarks

python -m reporting.collect_all_baselines $base/mypyc-benchmark-results

echo "<< success >>"
