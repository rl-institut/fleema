FLEEMA
==============
A tool for the flexible fleet energy management of an autonomous vehicle fleet in the ADVANTAGE project

|tests|

.. |tests| image:: https://github.com/rl-institut/fleema/actions/workflows/python-package.yml/badge.svg
      :target: https://github.com/rl-institut/fleema/actions/workflows/python-package.yml

Get started
-----------

Clone this repository and start contributing

Documentation
-------------

The full documentation can be found `[here] <https://fleema.readthedocs.io/en/latest/index.html>`_

Setting up an environment
-------------------------
As a User
^^^^^^^^
| Create a new virtual environment (for example in PyCharm or via the command line ``python3 -m venv venv``). Activate it with:
| Terminal:  ``source venv/bin/activate``
| Windows: ``venv\Scripts\activate``
| Note: You need to be in the project folder to activate the environment
|
| Install the requirements with ``pip install -e .``

As a Developer
^^^^^^^^^^^^^^
* Create a new virtual environment and activate it
* Install the project and its dependencies with ``pip install -e .[dev]``
* For testing use the following commands
    * ``flake8 src``
    * ``mypy src``
    * ``pytest``
    * ``tox``
* For autoformatting your code:
    * ``black src``

| Note: PyCharm might tell you that it can't find the fleema module.
| In that case you have to right click the folder "src" and select
| "Mark Directory as" -> "Sources Root"


Running the program
-------------------


To run this from the command line, go to the root folder of this repository,
then type ``python -m fleema`` into the terminal. A config path can be given as 
an additional argument.

In PyCharm, this can be set up as a run configuration:

* create a new python configuration
* choose module name instead of script path
* input the module name ``fleema``
* set the root directory of this repository as the working directory

Features
--------

- charging strategies: schedule, balanced market, on-demand
- vehicle-to-grid
- feed-in
- variety of input and output

Contribute
----------

- Issue Tracker: https://github.com/rl-institut/fleema/issues
- Source Code: https://github.com/rl-institut/fleema

License
-------

The project is licensed under the MIT license.