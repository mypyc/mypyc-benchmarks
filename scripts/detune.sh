#!/bin/bash
# Disable Linux tunings for more repeatable measurements.
# This assumes a 4-core CPU (no hyperthreading, or hyperthreading disabled in BIOS).

# Enable address space randomization
echo 2 | sudo tee /proc/sys/kernel/randomize_va_space

# Use powersave scaling governor
for f in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
do
    echo powersave | sudo tee "$f"
done
