Performance testing
===================

Patchwork provides the ``generate_perf_data`` management command to create
synthetic projects, submitters, series, patches and replies for local performance
testing. You can use this with a disposable database, configured like the
database backend of the instance you want to measure. You can use the command
like so:

.. code-block:: shell

    python manage.py migrate
    python manage.py loaddata default_states
    python manage.py generate_perf_data --projects 12 --patches-per-project 100000

The defaults create 1.2 million patches in batches of 1,000, with up to ten
patches per series and 100 shared submitters. Each patch has between 1 and 10
replies (roughly 6.6 million replies with the defaults), with randomly chosen
submitters and dates after the patch. Reply counts and contents are reproducible
with ``--seed``. Patch dates span a year. All patches contain the same small
diff: this is a query-performance dataset, not a
realistic simulation of database storage requirements or mail parsing.

Generated projects have names such as ``perf-1``. The command refuses to reuse
existing project names or generated submitter addresses. Use a different prefix
for another dataset, or recreate the disposable database. It never deletes data.
Batches are committed independently, so an interrupted run leaves partial data.
Save hooks and signals are bypassed: events, tags, checks and cover letters are
not generated.
