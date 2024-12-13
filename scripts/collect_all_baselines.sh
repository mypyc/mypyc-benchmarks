#!/bin/bash

# Script that collects new baselines for all benchmarks. Run as root.
#
# Run this to collect baselines after a Python version, operating system
# or hardware upgrade.
#
# See doc/benchmarks_runner.rst for more information.

repo=/srv/mypyc-benchmarks

# Tweak settings for running benchmarks
$repo/scripts/tune.sh

sudo -u benchmark bash $repo/scripts/baselines_inner.sh

# Restore normal settings
$repo/scripts/detune.sh
