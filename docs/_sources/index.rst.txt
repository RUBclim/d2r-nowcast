.. test_sphinx documentation master file, created by
   sphinx-quickstart on Wed Mar 27 10:14:23 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. Landing page for the documentation

.. title:: D2R Nowcasting Service Manual

D2R Nowcasting Service Manual
=============================


Extreme heat poses risks to human health, well-being, and public spaces.
The `ICLEI Action Fund 2.0 <https://iclei-europe.org/funding-opportunities/action-fund/>`__ project Data2Resilience aims to enhance Dortmund’s heat resilience through a three-part approach: measurement, modelling, and communication.
D2R is collaborating with the city of Dortmund to co-deploy a **state-of-the-art biometeorological sensor network**, that measures the air temperature, relative humidity, wind speed, and mean radiant temperature.
To monitor thermal discomfort across the city, D2R developed a nowcasting service that models the **Universal Thermal Climate Index (UTCI) at street level resolution**,
using as a basis the biometeorological weather station data and numerical weather predictions from DWD.
At its core, the nowcasting service uses the Urban Multi-scale Environmental Predictor (UMEP).
Specifically, the SOLWEIG model is utilized for thermal comfort calculations.
The final product of the nowcasting service is an interactive dashboard (:numref:`dashboard`) whose features and maps are developed according to the collected requirements and feedback from stakeholders.

.. figure:: documentation/data/00_dashboard_screenshot.png
   :align: center
   :width: 90%
   :alt: A screenshot of the developed Dashboard for the city of Dortmund.
   :name: dashboard

   A screenshot of the developed Dashboard for the city of Dortmund.


This document provides an overview of the D2R Nowcasting Service, including the data sources, processing steps, algorithms, and other relevant information.

Get started in the :ref:`overview` section.


.. Structure by topic
.. toctree::
   :numbered:
   :caption: Introduction
   :maxdepth: 4
   :hidden:

   documentation/01_overview
   documentation/06_install_and_use

.. toctree::
   :numbered:
   :caption: Model
   :maxdepth: 4
   :hidden:


   documentation/02_data_sources
   documentation/03_methods
   documentation/04_output_format

.. toctree::
   :numbered:
   :caption: Background
   :maxdepth: 4
   :hidden:

   documentation/05_scientific_background
   documentation/07_limitations
