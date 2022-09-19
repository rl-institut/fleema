advantage-tool
==============
A tool for the energy management of an autonomous vehicle fleet in the ADVANTAGE project

|tests|

.. |tests| image:: https://github.com/rl-institut/advantage-tool/actions/workflows/python-package.yml/badge.svg
      :target: https://github.com/rl-institut/advantage-tool/actions/workflows/python-package.yml

Get started
-----------

Clone this repository and start contributing

Setting up an environment
-------------------------
As a User
^^^^^^^^
| Create a new virtual environment (for example in PyCharm). Activate it with:
| Terminal:  ``source venv/bin/activate``
| Windows: ``venv\Scripts\activate``
| Note: You need to be in the project folder to activate the environment
|
| Install the requirements with ``pip install -e .``

As a Developer
^^^^^^^^^^^^^^
* Create a new virtual environment and activate it
* Install the project and its dependencies with ``pip install -e .``
* Install dev requirements with ``pip install -r dev_requirements.txt``
* For testing use the following commands
    * ``flake8 src``
    * ``mypy src``
    * ``pytest``
    * ``tox``

| Note: PyCharm might tell you that it can't find the advantage module.
| In that case you have to right click the folder "src" and select
| "Mark Directory as" -> "Sources Root"


Running the program
-------------------


To run this from the command line, go to the root folder of this repository,
then type ``python -m advantage`` into the terminal

In PyCharm, this can be set up as a run configuration:

* create a new python configuration
* choose module name instead of script path
* input the module name ``advantage``
* set the root directory of this repository as the working directory
