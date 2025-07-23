.. _install_and_use:

Install and Use
===============

.. _setup:

Setup
-----

The backend is developed in Python 3.12

For running the pipeline (see ``src/process_next_timestep.sh``) as the backend service the following steps need to be taken:

1. Setup the structure

   a. The project runs in Python 3.12, which can be seen in the base image used in the Dockerfile for the backend, ``backend.Dockerfile``.

   b. We import modules from a separate project called ``UMEP-processing-fork``.
      It keeps the standalone files of the required UMEP tool along with the original code of the toolbox. (See also :numref:`methods_and_processes` in the
      documentation for a more detailed description of the methods and processes.)

   c. For frequently downloading NWP GRIB2 data from the DWD file server, the DWD ``downloader`` has to be installed (current version 0.2.0).
      This happens within ``backend.Dockerfile`` but requires a clone of that project next to ``d2r-nowcast`` (see folder structure below).

   d. For downloading relevant ICON-D2 data and cropping it to the city extent, we use the functions placed in ``src/icon_d2``.

.. note::
   DWD announced a change in accessing DWD open data `Release Notes <https://www.dwd.de/DE/leistungen/opendata/neuigkeiten/opendata_april2025_1.html>`__
   in April 2025, which also affects the ``downloader`` tool and expected data format used in this project.
   At some point the ``downloader`` will not be functional anymore due to changes in the data format and this step will have to be adjusted.
   The tool's repository was already converted to a public archive on github and no further changes or updates are expected.


2. The project structure now has to look like:

   .. code-block:: text

      Common Parent Folder
      ├── d2r-nowcast
      ├── downloader
      └── UMEP-processing-fork

	

3. Build the Docker image

   Build the repository into a Docker image using the following command from the parent folder of ``d2r-nowcast``:

   ``docker build -f d2r-nowcast/src/backend.Dockerfile -t d2r-backend:<version> .``

   .. note::

      The flag ``-f`` allows to define a specific Dockerfile to be used.
      The container tag indicated with the ``-t`` flag can be set individually but needs to be consistent throughout the references in later steps.

4. Setup a script to run the Docker container

   Create a script to run the Docker container at an arbitrary path ``<path>/<to>/cronscript_<version>.sh``. To do this, copy and adjust the
   Docker run and Docker log commands in ``src/cronscript_template.sh`` to your needs. Adjust the paths to the datasets on your machine, set up available memory and CPU, etc.

   .. note::

      The SOLWEIG processes are run in multiprocessing mode, and the number of processes should match the defined available CPUs. Within the code,
      the number of processes is fixed to 32 in ``umep_wrapper/solweig_multi_processing.py`` with this line: 

      ``with Pool(processes=32, initializer=worker_init, initargs=[q]) as pool``

      The number of available CPUs is set with the ``docker run`` command in the above-mentioned script, using the ``--cpus`` flag. For our current
      setup, the following configuration is useful: ``--memory=128gb --cpus=32``, but this can be adjusted according to your requirements and limitations.

5. Edit the crontab

   Edit the crontab for your user on your machine using ``crontab -e`` and set up an hourly cron job by adding the following line:

   ``0 * * * * <path>/<to>/cronscript_<version>.sh 1> /dev/null 2> <path>/<to>/<error_file>.err``

   This command executes the prepared script from the previous step every hour, redirecting standard output (``1>``) to ``/dev/null`` and standard
   errors (``2>``) to ``<path>/<to>/<error_file>.err``.

   There is a ``src/cronscript_template.sh`` as guide for the specific docker run command executed on cron call.


.. _structure:

Structure
---------

The project is structured as follows:

``src/umep_wrapper``: 
   Contains scripts that can be run separately on the server to generate new data and corresponding Dockerfiles.

``src/umep_wrapper/config-templates``: 
   Contains config templates to run algorithms of the UMEP toolbox: Wall, SVF, SOLWEIG.

``src/icon_d2``:
   Contains scripts to download and pre-process ICON-D2 NWP data from the DWD for our purposes.

``src/interpolate``:
   Contains scripts to interpolate data from the measurement network for our purposes.

``src/utils``:
   Contains utility scripts.

``tests``:
   Contains some tests for ensuring the functionality of the pipeline. Tests can be executed via ``pytest -s -v`` in a properly set up virtual environment.
