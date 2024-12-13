Benchmarks runner documentation
*******************************

This explains how to setup and maintain a server than runs benchmarks
continuously (at least daily) using the latest mypy revisions, to keep
track of performance over time. The server also generates performance
reports and commits them to a GitHub repository.

System configuration
--------------------

Big picture:

* Use Ubuntu LTS
* User ``benchmark`` is used for the benchmark job; GitHub ssh access
  is configured as GitHub user 'mypyc-bot'
* The measurements are performed via ``scripts/cronjob.sh`` as a root
  cron job
* State is maintained under ``/srv``
* Report generation scripts live under ``reporting/`` in this repository

Use ``scripts/configure-server.sh`` to perform basic server configuration.

Performing system upgrades
--------------------------

Periodically we need to upgrade to newer Ubuntu and Python versions or
to newer hardware. Here the main complication is that we want to avoid
a discontinuity in benchmark timings so that we can track long-term
trends over upgrades.

Re-running old measurements using a newer OS/Python/hardware isn't
practical, since old mypy revisions generally don't work on newer
Python versions. Additionally, re-running measurements would take too
much time.

Instead, we calculate relative performance deltas between the old and
new system configurations, and scale the old measurements suitably so
that we can present a continuous timeline.

Let's say our new hardware is 50% faster than the old hardware. We can
divide the old measurements by 1.5 to get measurements comparable to
ones taken on the new hardware. This won't be exactly right, but it's
good enough for our purposes.

This section explains how to do this.

First, disable the cron job:

* ``sudo su``
* ``crontab -e``
* Comment out cron job

Then perform any upgrades you want. It's recommended to perform both
the OS upgrade and Python version upgrade together, if a newer Ubuntu
LTS version is available. Also if you upgrade hardware, you should
also upgrade Python and Ubuntu at the same time.

After you've finished any hardware and/or OS upgrades, install or
compile a newer Python version as needed. Use
``./configure --enable-optimizations --with-lto``
when building Python to get an optimized build. We generally prefer
the Python that is distributed with Ubuntu, if it's recent enough.

Update venv in ``/srv/venv`` to use the new Python version. See
``scripts/configure-server.sh`` for how it's configured.

Next collect new baselines on the server:

* ``sudo su`` (the script must be run as root)
* ``cd /srv/mypyc-benchmarks``
* ``bash scripts/collect_all_baselines.sh``
* The script should output ``<< success >>`` when complete
* ``exit``
* Commit and push new baselines under ``/srv/mypyc-benchmark-results``

This also acts as a basic sanity check to make sure that benchmarks
still work.

Finally, re-enable the cron:

* ``sudo su``
* ``crontab -e``
* Uncomment the cron job

Push an empty commit to the mypy repo and check that it is measured
correctly (once the cron job runs), and there is no abrupt change in
reported performance for the empty commit.
