Simulating
==========

Command line options
--------------------

There is only one positional command line option that specifies the configuration file.
This call happens from the root directory.

.. code:: bash

    python -m advantage ``<path-to-config/scenario.cfg>``


Input and output file formats
-----------------------------

Folder structure of inputs and outputs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Expect the folder results/ that gets created when running the program, everything is part of inputs.

.. code-block::

    ├── scenario_data
           └── scenario1
                ├── config
                │   ├──scenario_short.cfg
                │   └──scenario_long.cfg
                ├── results (outputs)
                ├── charging_points.json
                ├── consumption.csv
                ├── cost.csv
                ├── distance.csv
                ├── emission.csv
                ├── incline.csv
                ├── pv.csv
                ├── schedule.csv
                ├── temperature.csv
                └── vehicle_types.json


The example inputs in the GitHub repository are a great way to familiarize yourself with the data:

`Bad Birnbach <https://github.com/rl-institut/advantage-tool/tree/dev/scenario_data/bad_birnbach>`_


Input
^^^^^

charging_points.json
- Gathers the plug types and charging points in the simulation

consumption.csv
- a consumption table that has for the vehicles every consumption value with inputs like level of loading and incline


Output
^^^^^^


