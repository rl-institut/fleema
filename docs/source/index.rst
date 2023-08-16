Advantage Documentation
==============
A tool for the energy management of an autonomous vehicle fleet in the ADVANTAGE project.

Link to GitHub-Project: `Click <https://github.com/rl-institut/advantage-tool>`_

- The program uses inductive charging for autonomous electric fleets.
- automatic inductive charging station
- scenarios for grid beneficial applications are analysed
- autonomous electric vehicle fleets, pathways, charging stations, grid connections and local renewable energy sources

Simulation:
    1. simulation takes place in one minute steps
    2. first charging slots are allocated from breaks in the schedule of every vehicle through the use of SpiceEV
    3. then every charging slots gets a score
    4. in the end the best charging slots that fit together are chosen
    5. calculations are made
    6. outputs are being made

- as main input a config file is used that specifies parameters for charging, outputs, files, cost options, etc.
- the intput files that consist the fleet-scenario are: charging_points.json, vehicle_types.json, consumption.csv, schedule.csv, etc.


.. toctree::
   :maxdepth: 1
   :caption: Contents

   getting_started
   simulating
   code


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
