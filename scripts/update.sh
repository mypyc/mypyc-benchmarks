#!/bin/bash

# Script that collects benchmarks results for all new mypy commits and benchmarks
# on a server. This can be run from a cron job.
#
# For more repeatable results, run tune.sh (as root) before running this.

user=benchmark

if [ "$(whoami)" != $user ]; then
    echo "error: This script must be run as user '$user'"
    exit 1
fi

set -eux

base=/srv
logfile=$base/log/benchmarks.log

source $base/venv/bin/activate

cd $base/mypyc-benchmarks

python -m reporting.update $base/mypy $base/mypyc-benchmark-results 2>&1 | \
    tee -a $logfile

echo "<< success >>" >> $logfile
