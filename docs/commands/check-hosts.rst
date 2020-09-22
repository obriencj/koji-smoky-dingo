koji check-hosts
================

.. highlight:: none

::

 usage: koji check-hosts [-h] [--timeout TIMEOUT] [--channel CHANNEL]
                         [--arch ARCHES] [--ignore IGNORE]
                         [--ignore-file IGNORE_FILE] [-q] [-s]

 Show enabled builders which aren't checking in

 optional arguments:
   -h, --help            show this help message and exit
   --timeout TIMEOUT     Timeout in minutes before builder is considered AWOL
                         (default: 60)
   --channel CHANNEL     Limit check to builders in this channel
   --arch ARCHES         Limit check to builders of this architecture. Can be
                         specified multiple times
   --ignore IGNORE       Hostname pattern to ignore. Can be specified multiple
                         times
   --ignore-file IGNORE_FILE
                         File containing ignore patterns
   -q, --quiet           Only print builder names, not checkin time or summary
   -s, --shush           Only print summary when 1 or more builders are failing
                         to check in (cron-job friendly)


This command is used to identify problems with your builders, showing
those hosts which are enabled but which have stopped checking in with
the hub. AWOL builders may need to be restarted, or may have some
underlying hardware failure which needs attention.

The command's ``--shush`` option makes it cron-job friendly, so that
output is only produced when problems are discovered.


References
----------

* :py:obj:`kojismokydingo.cli.hosts.CheckHosts`
* :py:func:`kojismokydingo.cli.hosts.cli_check_hosts`
