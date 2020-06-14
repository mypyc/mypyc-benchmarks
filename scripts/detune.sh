#!/bin/bash
# Disable Linux tunings for more repeatable measurements.
# This assumes a 4-core/8-thread CPU.

# Enable hyperthreading
for f in /sys/devices/system/cpu/cpu[4567]/online
do
    echo 1 | sudo tee "$f"
done

# Enable address space randomization
echo 2 | sudo tee /proc/sys/kernel/randomize_va_space

# Use performance scaling governor
for f in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
do
    echo powersave | sudo tee "$f"
done
