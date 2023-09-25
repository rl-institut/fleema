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

.. image:: advantage_overview.jpg
   :width: 80 %
   :alt: Advantage Overview


Folder structure of inputs and outputs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Except the folder results/ that gets created when running the program, everything is part of inputs.

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

+-----------------+---------------------------------------------------------------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **File**        | **Description**                                                                 | **Data Type** | **Columns**                                                                                                                                                         |
+-----------------+---------------------------------------------------------------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| charging_points | gathers the plug types and charging points in the simulation                    | json          |                                                                                                                                                                     |
+-----------------+---------------------------------------------------------------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| consumption     | a consumption table that has for the vehicles every consumption value           | csv           | vehicle_type, level_of_loading, incline,mean_speed,t_amb,consumption                                                                                                |
+-----------------+---------------------------------------------------------------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| cost            | a price time series for electricity in one minute steps                         | csv           | datetime, cost                                                                                                                                                      |
+-----------------+---------------------------------------------------------------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| distance        | a matrix for all distances between every two locations                          | csv           |                                                                                                                                                                     |
+-----------------+---------------------------------------------------------------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| emission        | factors for emission for every minute of the simulation                         | csv           | emission_factor                                                                                                                                                     |
+-----------------+---------------------------------------------------------------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| incline         | a matrix for all inclines between every two locations                           | csv           |                                                                                                                                                                     |
+-----------------+---------------------------------------------------------------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| pv              | time series of feed-ins for every hour                                          | csv           | timestamp, total_kW                                                                                                                                                 |
+-----------------+---------------------------------------------------------------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| schedule        | input schedule with trips                                                       | csv           | line, departure_name, departure_time, arrival_time, arrival_name, distance, driving_time, pause, rotation_id, vehicle_typ, vehicle_id, occupation, level_of_loading |
+-----------------+---------------------------------------------------------------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| temperature     | spectrum of temperature values for every hour of the day                        | csv           | hour, lowest, highest, median                                                                                                                                       |
+-----------------+---------------------------------------------------------------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| vehicle_types   | data about vehicle types like name, capacity, charging curve and charging power | json          |                                                                                                                                                                     |
+-----------------+---------------------------------------------------------------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+


Output
^^^^^^
+-----------------------+-----------------------------------------------------------------------------------------------------+---------------+-------------------------------------+
| **File**              | **Description**                                                                                     | **Data Type** | **Columns**                         |
+-----------------------+-----------------------------------------------------------------------------------------------------+---------------+-------------------------------------+
| inputs/inputs         | basic information about the simulation like input files, paths, vehicle types and charging stations | json          |                                     |
+-----------------------+-----------------------------------------------------------------------------------------------------+---------------+-------------------------------------+
| <vehicle>_events      | every used vehicle that has events like driving and charging creates a csv                          | csv           | timestamp                           |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | event_start                         |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | event_time                          |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | end_location                        |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | status                              |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | soc_start                           |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | soc_end                             |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | energy                              |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | actual_energy_from_grid             |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | station_charging_capacity           |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | average_charging_power              |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | distance                            |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | energy_from_feed_in                 |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | energy_from_grid                    |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | energy_cost                         |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | emission                            |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | consumption                         |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | level_of_loading                    |
+-----------------------+-----------------------------------------------------------------------------------------------------+---------------+-------------------------------------+
| accumulated_results   | basic results like consumption, emission, cost, energy, etc.                                        | json          |                                     |
+-----------------------+-----------------------------------------------------------------------------------------------------+---------------+-------------------------------------+
| power_grid_timeseries | for every hourly timestep the drawn energy from the charging locations are shown here               | csv           | timestamp                           |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | total_power                         |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | total_connected_vehicles            |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | Marktplatz_total_power              |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | Marktplatz_total_connected_vehicles |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | Bahnhof_total_power                 |
|                       |                                                                                                     |               | ,                                   |
|                       |                                                                                                     |               | Bahnhof_total_connected_vehicles    |
+-----------------------+-----------------------------------------------------------------------------------------------------+---------------+-------------------------------------+