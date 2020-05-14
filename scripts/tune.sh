#!/bin/bash
# Tune Linux for more repeatable measurements.
# This assumes a 4-core/8-thread CPU.
#
# Adapted from https://easyperf.net/blog/2019/08/02/Perf-measurement-environment-on-Linux

# Disable address space randomization
echo 0 | sudo tee /proc/sys/kernel/randomize_va_space

# Use performance scaling governor
for f in /sys/devices/system/cpu/cpu[0123]/cpufreq/scaling_governor
do
    echo performance | sudo tee $f
done

# Disable hyperthreading
for f in /sys/devices/system/cpu/cpu[4567]/online
do
    echo 0 | sudo tee $f
done
