Advantage Documentation
=======================
A tool for the energy management of an autonomous vehicle fleet in the ADVANTAGE project.


Link to GitHub-Project: `Click <https://github.com/rl-institut/advantage-tool>`_


.. image:: https://github.com/rl-institut/advantage-tool/actions/workflows/python-package.yml/badge.svg
   :target: https://github.com/rl-institut/advantage-tool/actions/workflows/python-package.yml
   :alt: GitHub Workflow Status

.. image:: https://readthedocs.org/projects/4connect/badge/?version=latest
    :target: https://4connect.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status


Features
^^^^^^^^
- the program manages autonomous electric fleets.
- automatic inductive charging stations
- scenarios for grid beneficial applications are analysed
- autonomous electric vehicle fleets, pathways, charging stations, grid connections and local renewable energy sources (feed-in)

Simulation
^^^^^^^^^^

1. **Input:**
   Inputs are parsed into a `Simulation` object where components like vehicles and locations are created.

2. **Simulation**

    2.1. For every vehicle in the fleet, charging slots are allocated from breaks in the schedule.

    2.2. In order to find the best slot, the program runs every available slot through `SpiceEV <https://github.com/rl-institut/spice_ev>`_ and assigns it a score.

    2.3. Finally, the fleet simulates the best schedule step by step in one-minute increments for every vehicle. In each step, a vehicle can either drive or charge. Once again, `SpiceEV <https://github.com/rl-institut/spice_ev>`_ assists by simulating the vehicle's charging.

3. **Output:**
   Different outputs are created.

For more detailed information about the simulation check out :doc:`simulating`.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   getting_started
   simulating
   code


Index
    :ref:`genindex`
