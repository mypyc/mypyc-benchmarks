Benchmarks runner documentation
*******************************

This explains how to setup and maintain a server than runs benchmarks
continuously (at least daily) using the latest mypy revisions to keep
track of performance over time and posts performance reports to a GitHub
repository.

System configuration
--------------------

Big picture:

 * Use Ubuntu LTS
 * User ``benchmark`` used is for the benchmark job, GitHub ssh access
   configured as GitHub user mypyc-bot
 * The measurements are performed via ``scripts/cronjob.sh`` as a root
   cron job
 * State is maintained under ``/srv``
 * Report generation scripts live under ``reporting/`` in this repository

Use ``scripts/configure-server.sh`` to perform basic server configuration.
