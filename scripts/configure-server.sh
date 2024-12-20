#!/bin/bash

# This configures some things for running all new benchmarks periodically on a server.
# Some additional manual steps will also be required. The script will give instructions
# about some of the manual steps.
#
# This has been tested on Ubuntu 20.04.

user=benchmark
base=/srv

if [ "$(whoami)" != root ]; then
    echo "error: This script must be run as root"
    exit 1
fi

if [ ! -d /home/$user ]; then
    echo "error: User '$user' does not exist"
    echo
    echo "Follow these steps:"
    echo " * Create the user"
    echo " * Give it ssh access to GitHub as user mypyc-bot"
    echo " * Set up git identity for the user:"
    echo "   * git config --global user.email 'mypyc-bot@users.noreply.github.com'"
    echo "   * git config --global user.name 'mypyc bot'"
    echo " * Disable automatic package updates"
    exit 1
fi

set -eux

apt install git pkg-config python3 python3-dev build-essential clang gdb lcov \
      libbz2-dev libffi-dev libgdbm-dev libgdbm-compat-dev liblzma-dev \
      libncurses5-dev libreadline6-dev libsqlite3-dev libssl-dev \
      lzma lzma-dev uuid-dev zlib1g-dev

if [ ! -d $base ]; then
    echo "Setting up $base"
    mkdir $base
fi

if [ ! -d $base/log ]; then
    echo "Setting up $base/log"
    mkdir $base/log
    chown $user:$user $base/log
fi

for bm in mypyc-benchmark-results mypyc-benchmarks; do
    if [ ! -d $base/$bm ]; then
        echo "Setting up $base/$bm"
        mkdir $base/$bm
        chown $user:$user $base/$bm
        sudo -u $user git clone git@github.com:mypyc/$bm.git $base/$bm
    fi
done

if [ ! -d $base/mypy ]; then
    echo "Setting up $base/mypy"
    mkdir $base/mypy
    chown $user:$user $base/mypy
    sudo -u $user git clone --recurse-submodules git@github.com:python/mypy.git $base/mypy
fi

if [ ! -d $base/venv ]; then
    echo "Setting up $base/venv"
    mkdir $base/venv
    chown $user:$user $base/venv
    cat > /tmp/venv.sh <<EOF
virtualenv -p python3 $base/venv
source $base/venv/bin/activate
pip install typing_extensions six attrs mypy_extensions
EOF
    sudo -u $user bash /tmp/venv.sh
fi

set +x

echo
echo "Done setting up directories under $base."
echo
echo "You should also create a root cron job that runs 'scripts/cronjob.sh'."
