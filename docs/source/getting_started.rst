Getting started
===============


You can clone the current repository of SpiceEV to your local machine using HTTPS:

.. code:: bash

    git clone https://github.com/rl-institut/fleema.git

Or SSH:

.. code:: bash

    git clone git@github.com:rl-institut/fleema.git


Setting up an environment
-------------------------
As a User
^^^^^^^^^
* `Download Python <https://www.python.org/downloads/>`_
* Create a new virtual environment (for example in PyCharm or via the command line).

.. code:: bash

    python3 -m venv venv

Activate it with:

.. code:: bash

    source venv/bin/activate

* Windows:

.. code:: bash

    venv\Scripts\activate

* Note: You need to be in the project folder to activate the environment
* Install the requirements with

.. code:: bash

    pip install -e .

As a Developer
^^^^^^^^^^^^^^
* Create a new virtual environment and activate it
* Install the project and its dependencies with

.. code:: bash

    pip install -e .[dev]

* For testing use the following commands

.. code:: bash

    flake8 src
    mypy src
    pytest
    tox

* For autoformatting your code

.. code:: bash

    black src

| Note: PyCharm might tell you that it can't find the fleema module.
| In that case you have to right click the folder "src" and select
| "Mark Directory as" -> "Sources Root"


Running the program
-------------------

To run this from the command line, go to the root folder of this repository, then type

.. code:: bash

    python -m fleema

into the terminal. A config path can be given as
an additional argument.

In PyCharm, this can be set up as a run configuration:

* create a new python configuration
* choose module name instead of script path
* input the module name ``fleema``
* set the root directory of this repository as the working directory

