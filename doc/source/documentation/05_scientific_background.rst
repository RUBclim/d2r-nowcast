.. _scientific_background:

Scientific Background
=====================

This section covers the topic of scientific background, what is thermal comfort, what drives it and how it can be modeled.




.. _thermal_comfort:

Thermal Comfort
---------------

The ANSI/ASHRAE Standard [1]_ defines Thermal Comfort as follows:

.. epigraph::

   "Thermal comfort is defined as the condition of mind that expresses satisfaction with the thermal environment and is assessed by subjective evaluation."

Oke et al. [2]_ complement this definition by emphasizing the individual, psychological, and cultural aspects of comfort assessment,
which further complicate an objective valuation of this condition. This becomes even more difficult when considering the different
conditions of spaces where people spend time, such as a constant indoor climate or changing microclimates outdoors. The complexity
resulted in a variety of indices, which were comprehensively reviewed in the literature in general [3]_ [4]_ [5]_ and for specific regions [6]_ [7]_ [8]_.

One of the most prominent indices is the Universal Thermal Climate Index (UTCI) [9]_. It is driven by the four meteorological variables:
Air Temperature, Relative Humidity, Wind Speed, and Radiation. Human behavior also plays a role in the sensation of thermal comfort in
terms of clothing selection, health condition, activity, etc. These factors are considered and parameterized differently in different indices.


.. _utci:

UTCI
----

The UTCI is categorized as a rational model [2]_ and considers the Fiala model for the biophysical processes, but uses an *outdoor reference* situation and a walking person [2]_ [9]_ .

"The UTCI is defined as the air temperature [..] of the reference condition causing the same model response as actual conditions." [9]_

So the approach of calculating UTCI is similar to that of PET, but the reference conditions and the underlying energy model differ. For UTCI, the reference conditions are [2]_:

- Outdoor reference where the individual is walking.
- Tair = TMRT (Air Temperature equals Mean Radiant Temperature).
- Wind Speed (V) is 0.5 m/s.
- Relative Humidity is 50% (capped at 20 hPa).




UTCI comes with a classification of the temperature ranges into thermal (dis)comfort categories.
See the table below for the different ranges:

.. list-table:: UTCI classification into thermal stress levels (derived from [9]_).
   :header-rows: 1
   :name:

   * - UTCI [°C]
     - Description
   * - 
     -
   * - [< -40]
     - Extreme Cold Stress
   * - [-40 to -27]
     - Very Strong Cold Stress
   * - [-27 to -13]
     - Strong Cold Stress
   * - [-13 to 0]
     - Moderate Cold Stress
   * - [0 to 9]
     - Slight Cold Stress
   * - [9 to 26]
     - No Thermal Stress
   * - [26 to 32]
     - Slight Heat Stress
   * - [32 to 38]
     - Moderate Heat Stress
   * - [38 to 46]
     - Strong Heat Stress
   * - [ > 46]
     - Extreme Heat Stress








----

.. Sources

.. [1] "ANSI/ASHRAE Standard 55-2010, Thermal Environmental Conditions for Human Occupancy"
.. [2] "T. R. Oke, G. Mills, A. Christen, and J. A. Voogt, Urban Climates. Cambridge: Cambridge University Press, 2017. https://doi.org/10.1017/9781139016476"
.. [3] "I. Charalampopoulos, A comparative sensitivity analysis of human thermal comfort indices with generalized additive models. Theor Appl Climatol 137, 1605–1622, 2019. https://doi.org/10.1007/s00704-019-02900-1 "
.. [4] "M. Migliari, R. Babut, C. De Gaulmyn, L. Chesne, O. Baverel, The Metamatrix of Thermal Comfort: A compendious graphical methodology for appropriate selection of outdoor thermal comfort indices and thermo-physiological models for human-biometeorology research and urban planning, Sustainable Cities and Society, Volume 81, 2022, https://doi.org/10.1016/j.scs.2022.103852. "
.. [5] "J. Shaeri, A Comparative Study of Outdoor and Indoor Thermal Comfort Indices, 2023, http://dx.doi.org/10.2139/ssrn.4489293 (preprint)"
.. [6] "F. Binarti, M. D. Koerniawan, S. Triyadi, S. Sesotya Utami, A. Matzarakis, A review of outdoor thermal comfort indices and neutral ranges for hot-humid regions, Urban Climate, Volume 31, 2020, https://doi.org/10.1016/j.uclim.2019.100531. "
.. [7] "S. Patle, V.V. Ghuge, Evolution and performance analysis of thermal comfort indices for tropical and subtropical region: a comprehensive literature review. Int. J. Environ. Sci. Technol., 2024. https://doi.org/10.1007/s13762-024-05703-8. "
.. [8] "Z. Tao, X. Zhu, G. Xu, D. Zou, G. Li, A Comparative Analysis of Outdoor Thermal Comfort Indicators Applied in China and Other Countries. Sustainability, 2023, 15, https://doi.org/10.3390/su152216029. "
.. [9] "K. Blazejczyk, G. Jendritzky, P. Bröde, J. Baranowski, D. Fiala, G. Havenith,Y. Epstein, A. Psikuta, B. Kampmann, An introduction to the Universal Thermal Climate Index (UTCI), Geographia Polonica, 86, 2013, https://doi.org/10.7163/GPol.2013.1. "
.. .. [10] "P. Höppe, The physiological equivalent temperature – a universal index for the biometeorological assessment of the thermal environment, Int J Biometeorol, 43, 1998, https://doi.org/10.1007/s004840050118 "
.. .. [11] "(Only German) Deutscher Wetterdienst (DWD), Erläuterungen zur Gefühlten Temperatur, 2024, https://www.dwd.de/DE/leistungen/gefahrenindizesthermisch/gefuehltetemp.html "
.. .. [12] "H. Staiger, G. Laschewski, A. Grätz,  The perceived temperature - a versatile index for the assessment of the human thermal environment. Part A: scientific basics. Int J Biometeorol. 2012, 56(1), https://doi.org/10.1007/s00484-011-0409-6. "