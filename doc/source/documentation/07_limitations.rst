.. _limitations:

Limitations
-----------

The developed tool consists of several processing steps, relies on preprocessed data and existing tools.
The selection of tools and design of the process allows an execution in near real-time with also limited computing capacities.

Therefore the resulting rasters have some limitations and have to be treated with respect to the different accuracies:

* The interpolation of in-situ measurements considers urban topography but does not model microclimatic processes of air temperature and relative humidity.
* Urban wind fields are not given in a high resolution, therefore the given wind speed from ICON-D2 is used.
* ICON-D2 incorporates urban effects with the TERRA_URB module, but has a resolution of about 2 km.
* For the original SOLWEIG an RMSE of 4.8K was repoorted in 2008 [1]_; since then multiple upgrades were incorporated, such as the vegetation scheme, which reduced the RMSE to 3.1K [2]_.
* The processing pipeline is run once per hour on a 3m grid.
* Information on the urban form is rarely available and only some land cover classes can be considered with SOLWEIG.

The final accuracies for this service are currently being investigated.

.. [1] Fredrik Lindberg, Björn Holmer, Sofia Thorsson, SOLWEIG 1.0 – Modelling spatial variations of 3D radiant fluxes and mean radiant temperature in complex urban settings, 2008, International Journal of Biometeorology
.. [2] Fredrik Lindberg, C. Sue Grimmond, The influence of vegetation and building morphology on shadow patterns and mean radiant temperatures in urban areas: model development and evaluation, 2011, Theoretical and Applied Climatology