#!/bin/bash

# Cron job, to be run as root, for running mypyc benchmarks.
#
# Don't run this directly from the repository to allow the script to be
# modified.

repo=/srv/mypyc-benchmarks

# Tweak settings for running benchmarks
$repo/scripts/tune.sh

# Copy script and then run it to avoid being modified while executing
cp $repo/scripts/update.sh /tmp
sudo -u benchmark bash /tmp/update.sh

# Restore normal settings
$repo/scripts/detune.sh
