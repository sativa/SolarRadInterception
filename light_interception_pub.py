#!/usr/bin/env python
'''Radiation interception methods'''
from __future__ import division
import numpy as np
import math
import matplotlib.pyplot as plt

def height_weight_fact(height_dom, dominant_fact, suppressed_fact,
                       number_species):
    """(float, float, float, int) -> float

    Height dominance weighing factor calculated as a linear interpolation
    between dominant and suppressed species for radiation interception between
    species

    height_dom: Species dominance factor based on height
    dominant_fact: Dominant weighing factor
    suppressed_fact: Suppressed weighing factor
    number_species: number of species

    Reference: Camargo, G.G.T. 2014. Ph.D. Dissertation. Penn State University

    >>> height_weight_fact(0.75, 1.52, 0.56, 3)
    0.89
    >>> height_weight_fact(1.5, 1.52, 0.56, 3)
    1.13
     """
    assert (height_dom and dominant_fact and suppressed_fact and
            number_species) > 0
    # One species or species of same height
    if height_dom == 1:
        return 1
    # If species in shorter than canopy average
    elif height_dom < 1:
        return ((height_dom - 1) * (suppressed_fact - 1)) / (0 - 1) + 1
    # If species in taller than canopy average
    else:
        return (1 + (height_dom - 1) / (number_species - 1) *
                (dominant_fact - 1))


def opt_air_mass(atm_press, solar_zenith_angle):
    """(float, float) -> float

    Return optical air mass, or the ratio of slant path length through the
    atmosphere to zenith path length

    atm_press: [kPa]
    solar_zenith_angle: [deg]

    Reference: Campbell, G. S., and J. M. Norman. 1998. Introduction to
     environmental biophysics. Springer, New York. Eq. 11.12

    >>> opt_air_mass(100, 50)
    1.5357589603755304
    >>> opt_air_mass(91.6, 30)
    1.0441319774485631
    """
    SEA_LEVEL_ATM_PRSSR = 101.3
    assert atm_press <= SEA_LEVEL_ATM_PRSSR and atm_press > 38
    assert solar_zenith_angle >= 0
    DEG_TO_RAD = math.pi / 180.
    solar_zenith_angle *= DEG_TO_RAD
    return atm_press / (SEA_LEVEL_ATM_PRSSR * math.cos(solar_zenith_angle))


def rad_ext_coeff_black_beam(solar_zenith_angle, x_area_ratio):
    """(float, float) -> float

    Return solar radiation extinction coefficient of a canopy of black leaves
     with an ellipsoidal leaf area distribution for beam radiation

    solar_zenith_angle: rad
    x_area_ratio: average area of canopy elements projected on to the
     horizontal plane divided by the average area projected on to a vertical
     plane

    Reference: Campbell, G.S., Norman, J.M., 1998. Introduction to
     environmental biophysics. Springer, New York. Eq. 15.4

    >>> rad_ext_coeff_black_beam(0.087, 0)
    0.055576591963547875
    >>> rad_ext_coeff_black_beam(0.087, 2)
    0.7254823957447912
    """
    assert (solar_zenith_angle >= 0 and x_area_ratio) >= 0
    assert x_area_ratio >= 0
    numerator = (x_area_ratio ** 2 + math.tan(solar_zenith_angle) ** 2) ** 0.5
    denominator = x_area_ratio + 1.774 * (x_area_ratio + 1.182) ** -0.733
    return numerator / denominator


def rad_ext_coeff_black_diff(x_area_ratio, leaf_area_index):
    """(float, float) -> float

    Return solar radiation extinction coefficient of a canopy of black leaves
     for diffuse radiation

    x_area_ratio: average area of canopy elements projected on to the
     horizontal plane divided by the average area projected on to a vertical
     plane
    leaf_area_index: m3/m3

    Reference: Campbell, G.S., Norman, J.M., 1998. Introduction to
     environmental biophysics. Springer, New York. Eq. 15.5

    >>> rad_ext_coeff_black_diff(2, 0.1)
    0.9710451784887358
    >>> rad_ext_coeff_black_diff(0, 0.1)
    0.9099461266386164
    """
    assert (x_area_ratio and leaf_area_index) >= 0
    STEP_SIZE = 90
    MAX_ANGLE = math.pi / 2
    transm_diff = 0
    diff_ang = MAX_ANGLE / STEP_SIZE
    diff_ang_center = 0.5 * diff_ang
    angle = diff_ang
    # Integration loop
    while True:
        angle = angle - diff_ang_center
        transm_beam = math.exp(-rad_ext_coeff_black_beam(angle, x_area_ratio) *
                               leaf_area_index)
        transm_diff += (2 * transm_beam * math.sin(angle) * math.cos(angle) *
                        diff_ang)
        angle = angle + diff_ang_center + diff_ang
        if angle > (MAX_ANGLE + diff_ang):
            break
    return -math.log(transm_diff) / leaf_area_index


def solar_beam_fraction(atm_press, solar_zenith_angle, atm_transmittance):
    """(float, float, float) -> (float, float, float)

    Return radiation beam fraction

    atm_press: [kPa]
    solar_zenith_angle: [deg]
    atm_transmittance: 0.75 for clear sky

    Reference: Campbell, G. S., and J. M. Norman. 1998. Introduction to
     environmental biophysics. Springer, New York. Ch. 11

    >>> solar_beam_fraction(101.3, 0, 0.75)
    0.75
    >>> solar_beam_fraction(101.3, 50, 0.45)
    0.2892276326469122
    """
    assert solar_zenith_angle >= 0 and solar_zenith_angle <= 90
    assert atm_transmittance >= 0 and atm_transmittance <= 1
    DEG_TO_RAD = math.pi / 180.
    solar_zenith_angle *= DEG_TO_RAD
    optical_air_mass = opt_air_mass(atm_press, solar_zenith_angle)  # 11.12
    solar_perpend_frac = atm_transmittance ** optical_air_mass  # Eq. 11.11
    return solar_perpend_frac * math.cos(solar_zenith_angle)  # 11.8


def solar_diffuse_fraction(atm_press, solar_zenith_angle, atm_transmittance):
    """(float, float, float) -> (float, float, float)

    Return radiation diffuse fraction

    atm_press: [kPa]
    solar_zenith_angle: [deg]
    atm_transmittance: 0.75 for clear sky

    Reference: Campbell, G. S., and J. M. Norman. 1998. Introduction to
     environmental biophysics. Springer, New York. Ch. 11

    >>> solar_diffuse_fraction(101.3, 0, 0.75)
    0.075
    >>> solar_diffuse_fraction(101.3, 50, 0.45)
    0.10606799311188815
    """
    assert solar_zenith_angle >= 0 and solar_zenith_angle <= 90
    assert atm_transmittance >= 0 and atm_transmittance <= 1

    DEG_TO_RAD = math.pi / 180.
    solar_zenith_angle *= DEG_TO_RAD
    optical_air_mass = opt_air_mass(atm_press, solar_zenith_angle)  # 11.12
    return (0.3 * (1 - atm_transmittance ** optical_air_mass) *
            math.cos(solar_zenith_angle))  # 11.13


def rad_intercpt_sub_daily(atm_transm, atm_press, leaf_transm, leaf_area_index,
                           x_sp1, x_sp2, angles_deg):
    """(float, float, float, float, float, float, float) -> (float, float)
    Return sub daily radiation interception for two species

    atm_transm: atmospheric transmission [0-1]
    atm_press: atmospheric pressure
    leaf_transm: leaf transmission [0-1]
    leaf_area_index: leaf area index array
    x_sp1: average area of canopy elements projected on to the
     horizontal plane divided by the average area projected on to a vertical
     plane for species 1
    x_sp2: average area of canopy elements projected on to the
     horizontal plane divided by the average area projected on to a vertical
     plane for species 2
    angles_deg: angles range in degrees

    Reference: Campbell, G. S., and J. M. Norman. 1998. Introduction to
     environmental biophysics. Springer, New York.

    >>> rad_intercpt_sub_daily(0.75, 101.3, 0.8,
                               [0.005, 0.39333333, 0.78166667, 1.17,
                                1.55833333,1.94666667, 2.335, 2.72333333,
                                3.11166667, 3.5], 0.5, 2,
                               np.linspace(0, 90, 19))
    (array([ 0.00308931,  0.16775233,  0.25474302,  0.30521083,  0.33553347,
             0.35400209,  0.36525766,  0.37203142,  0.3759791 ,  0.37812616]),
     array([ 0.00386786,  0.2287585 ,  0.36321216,  0.44815845,  0.5032327 ,
             0.53963175,  0.56408442,  0.58077185,  0.59235289,  0.60054507]))

    """
    DEG_TO_RAD = math.pi / 180
    angles = angles_deg * DEG_TO_RAD
    beam_frac = np.zeros(len(angles))
    diff_frac = np.zeros(len(angles))
    total_intercpt = np.zeros(len(angles))
    sp1_intercpt_alone = np.zeros([len(angles), len(leaf_area_index)])
    sp2_intercpt_alone = np.zeros([len(angles), len(leaf_area_index)])
    canopy_intercpt = np.zeros([len(angles), len(leaf_area_index)])
    sp1_intercpt = np.zeros([len(angles), len(leaf_area_index)])
    sp2_intercpt = np.zeros([len(angles), len(leaf_area_index)])
    sp1_intercpt_daily = np.zeros(len(leaf_area_index))
    sp2_intercpt_daily = np.zeros(len(leaf_area_index))

    for i, angle in enumerate(angles_deg):
        beam_frac[i] = solar_beam_fraction(atm_press, angle, atm_transm)
        diff_frac[i] = solar_diffuse_fraction(atm_press, angle, atm_transm)
        total_intercpt[i] = beam_frac[i] + diff_frac[i]

    for i, angle in enumerate(angles):
        for j, lai in enumerate(leaf_area_index):
            sp1_intercpt_alone[i, j] = ((
                1 - (beam_frac[i]/total_intercpt[i] *
                     math.exp(-(leaf_transm ** 0.5) * lai *
                     (rad_ext_coeff_black_beam(angle, x_sp1))) +
                     diff_frac[i] / total_intercpt[i] *
                     math.exp(-(leaf_transm ** 0.5) *
                     lai * rad_ext_coeff_black_diff(x_sp1, lai)))) *
                total_intercpt[i])
            sp2_intercpt_alone[i, j] = ((
                1 - (beam_frac[i]/total_intercpt[i] *
                     math.exp(-(leaf_transm ** 0.5) * lai *
                     (rad_ext_coeff_black_beam(angle, x_sp2))) +
                     diff_frac[i] / total_intercpt[i] *
                     math.exp(-(leaf_transm ** 0.5) *
                     lai * rad_ext_coeff_black_diff(x_sp2, lai)))) *
                total_intercpt[i])
            canopy_intercpt[i, j] = (
                (1 - (1 - sp1_intercpt_alone[i, j] / total_intercpt[i]) *
                 (1 - sp2_intercpt_alone[i, j] / total_intercpt[i])) *
                total_intercpt[i])
            sp1_intercpt[i, j] = (
                -math.log(1 - sp1_intercpt_alone[i, j] / total_intercpt[i]) /
                (-math.log(1 - sp1_intercpt_alone[i, j] / total_intercpt[i]) +
                 (-math.log(1 - sp2_intercpt_alone[i, j] /
                  total_intercpt[i])))) * canopy_intercpt[i, j]
            sp2_intercpt[i, j] = (
                -math.log(1 - sp2_intercpt_alone[i, j] / total_intercpt[i]) /
                (-math.log(1 - sp1_intercpt_alone[i, j] / total_intercpt[i]) +
                 (-math.log(1 - sp2_intercpt_alone[i, j] /
                  total_intercpt[i])))) * canopy_intercpt[i, j]
    for i in range(len(leaf_area_index)):
        sp1_intercpt_daily[i] = sp1_intercpt[:, i].sum() / total_intercpt.sum()
        sp2_intercpt_daily[i] = sp2_intercpt[:, i].sum() / total_intercpt.sum()
    return sp1_intercpt_daily, sp2_intercpt_daily


def rad_intercpt_cycles(crop_list):
    """(list,list,...) -> array

    Returns rad intercepted on each species

    crop_list: list of species characteristics
        extinction_coeff: rad extinction coefficient
        leaf_area_index: leaf area index [m2/m2]
        height: plant height [height_dom]

    Reference: Camargo, G.G.T. 2014. Ph.D. Dissertation. Penn State University

    >>> rad_intercpt_cycles(([0.5,1,1],[0.5,1,2],[0.5,1,1]))
    array([0.23758411, 0.30170163, 0.23758411])
    >>> rad_intercpt_cycles(([0.5,1,0.5],[0.6,1.2,1],[0.7,1.4,1.5]))
    array([0.13822214, 0.29363746, 0.45733724])
     """
    # Variables init
    number_species = len(crop_list)
    extinction_coeff = np.zeros(number_species)
    leaf_area_index = np.zeros(number_species)
    height = np.zeros(number_species)
    transm_rad = np.zeros(number_species)  # if plant was alone
    rad_intercpt_dom = np.zeros(number_species)  # dominant species
    rad_intercpt_suppr = np.zeros(number_species)  # supressed species
    rad_intercpt = np.zeros(number_species)  # species rad interception
    transm_rad_others = np.ones(number_species)  # non-domnt sp rad transm
    height_dom = np.zeros(number_species)  # species canopy dominance factor
    dominant_fact = np.zeros(number_species)  # Dominant weight factor
    suppressed_fact = np.zeros(number_species)  # Suppressed weight factor
    hght_wght_fct = np.zeros(number_species)
    hght_wght_fct_adj = np.zeros(number_species)
    k_lai_prod = np.zeros(number_species)
    k_lai_prod_adj = np.zeros(number_species)
    total_transm = 1
    # Read and store inputs
    for i in range(number_species):
        extinction_coeff[i] = crop_list[i][0]
        leaf_area_index[i] = crop_list[i][1]
        height[i] = crop_list[i][2]
        # Transmitted radiation if all species had same height
        transm_rad[i] = math.exp(-extinction_coeff[i] * leaf_area_index[i])
        # Intercepted radiation if species was dominant
        rad_intercpt_dom[i] = 1 - transm_rad[i]
        k_lai_prod[i] = extinction_coeff[i] * leaf_area_index[i]
    # Calculate total transmitance, interception and height dominance
    for i in range(number_species):
        # Total transmitance if all species had the same height
        total_transm *= transm_rad[i]
        # Height dominance factor
        height_dom[i] = number_species * height[i] / height.sum()
    # Total radiation interception if species had the same height
    total_interception = 1 - total_transm
    # All species but ith species rad transmission
    for i in range(number_species):
        all_species = range(number_species)  # list with all species
        all_species.pop(i)  # remove ith species from list
        all_species_but_ith = all_species  # list of non-dominant species
        total_transm_but_ith_sp = 1  # sum of non-dominant species transmission
        for j in all_species_but_ith:
            total_transm_but_ith_sp *= transm_rad[j]
        # Total transmitted radiation from all species but ith
        transm_rad_others[i] = total_transm_but_ith_sp

    # Radiation interception by suppressed species once all other species
    # intercepts the radiation first
    for i in range(number_species):
        rad_intercpt_suppr[i] = rad_intercpt_dom[i] * transm_rad_others[i]

    # Determine two extremes weighing factors: in dominant_fact species will
    # intercept all radiation than it can based on k and LAI, in
    # suppressed_factor, species will only intercept radiation after all the
    # other species intercepted all rad that was possible
    for i in range(number_species):
        dominant_fact[i] = (rad_intercpt_dom[i] / total_interception *
                            k_lai_prod.sum() / k_lai_prod[i])
        suppressed_fact[i] = (rad_intercpt_suppr[i] / total_interception *
                              k_lai_prod.sum() / k_lai_prod[i])
        # Based on species height determine a height weight factor in between
        # dominant_fact and suppressed_fact values usin linear interpolation
        hght_wght_fct[i] = height_weight_fact(height_dom[i],
                                              dominant_fact[i],
                                              suppressed_fact[i],
                                              number_species)
        # Adjust extinction coefficient and leaf area index product
        k_lai_prod_adj[i] = (extinction_coeff[i] * leaf_area_index[i] *
                             hght_wght_fct[i])
    for i in range(number_species):
        # Adjust height weighting factor
        hght_wght_fct_adj[i] = (hght_wght_fct[i] / k_lai_prod_adj.sum() *
                                k_lai_prod.sum())
        # Radiation interception for each species
        rad_intercpt[i] = (total_interception * hght_wght_fct_adj[i] *
                           k_lai_prod[i] / k_lai_prod.sum())
    return rad_intercpt


def rad_intercpt_wallace(crop_list):
    """(list,list) -> array

    Returns rad intercepted on each species

    crop_list: list of species characteristics:
        extinction_coeff: rad extinction coefficient
        leaf_area_index: leaf area index [m2/m2]
        height: plant height [m]

    Reference: Wallace, J.S., 1997. Evaporation and radiation interception
     by neighbouring plants. Quarterly Journal of the Royal Meteorological
     Society 123, 1885-1905.

    >>> rad_intercpt_wallace(([0.5, 1, 1], [0.7, 3, 1]))
    [0.22082609516300733, 0.7049003266226588]
    """
    # Checking input values
    assert len(crop_list) == 2, "Only two species allowed"
    assert len(crop_list[0]) == 3, "Only 3 inputs per species: ext_coeff, LAI,\
                                    height"
    assert len(crop_list[1]) == 3, "Only 3 inputs per species: ext_coeff, LAI,\
                                    height"
    # Read inputs
    extinction_coeff1 = crop_list[0][0]
    extinction_coeff2 = crop_list[1][0]
    leaf_area_index1 = crop_list[0][1]
    leaf_area_index2 = crop_list[1][1]
    height1 = crop_list[0][2]
    height2 = crop_list[1][2]
    transm_rad1 = (math.exp(-extinction_coeff1 * leaf_area_index1))
    transm_rad2 = (math.exp(-extinction_coeff2 * leaf_area_index2))
    # Dominant species rad interception
    rad_intercpt_dom1 = 1 - transm_rad1
    rad_intercpt_dom2 = 1 - transm_rad2
    height_fraction1 = height1 / (height1 + height2)
    height_fraction2 = height2 / (height1 + height2)
    # Suppressed species rad interception
    rad_intercpt_suppr1 = rad_intercpt_dom1 * transm_rad2
    rad_intercpt_suppr2 = rad_intercpt_dom2 * transm_rad1
    # Species rad interception
    rad_intercpt1 = (rad_intercpt_suppr1 + height_fraction1 *
                     (rad_intercpt_dom1 - rad_intercpt_suppr1))
    rad_intercpt2 = (rad_intercpt_suppr2 + height_fraction2 *
                     (rad_intercpt_dom2 - rad_intercpt_suppr2))
    return [rad_intercpt1, rad_intercpt2]


def rad_intercpt_apsim(crop_list):
    """(list,list,...) -> array

    Returns rad intercepted on each species

    crop_list: list of species characteristics:
        extinction_coeff: rad extinction coefficient
        leaf_area_index: leaf area index (m2/m2)

    Reference: Carberry, P.S., Adiku, S.G.K., McCown, R.L., Keating, B.A.,
     1996.Application of the APSIM cropping systems model to intercropping
     systems, in: Ito, C., Johansen, C., Adu-Gyamfi, K., Katayama, K.,
     Kumar-Rao, J.V.D.K., Rego, T.J. (Eds.), Dynamics of roots and nitrogen in
     cropping systems of the semi-arid tropics. Japan Int. Res. Centre Agric.
     Sci, pp. 637-648.

     >>> rad_intercpt_apsim(([0.5, 1],[0.7, 3]))
     [ 0.17802431  0.74770211]
    """
    # Variables init
    number_species = len(crop_list)
    transm_rad_temp = np.zeros(number_species)
    rad_intercpt_temp = np.zeros(number_species)
    ext_coeff_leaf_area_index_prod = np.zeros(number_species)
    leaf_area_index = 0.  # Leaf area index
    extinction_coeff = 0.  # Extinction coeff. for solar radiation init
    cum_transm_rad = 1.  # Cumulative fractional transmission
    rad_intercpt_list = np.zeros(number_species)
    # Temporarly rad interception
    for i in range(number_species):
        extinction_coeff = crop_list[i][0]
        leaf_area_index = crop_list[i][1]
        ext_coeff_leaf_area_index_prod[i] = (extinction_coeff *
                                             leaf_area_index)
        transm_rad_temp[i] = math.exp(-extinction_coeff * leaf_area_index)
        cum_transm_rad = cum_transm_rad * transm_rad_temp[i]
        rad_intercpt_temp[i] = 1 - transm_rad_temp[i]
    tot_rad_intercpt = 1 - cum_transm_rad
    # Actual rad interception of each crop weighted by k and LAI
    for i in range(number_species):
        if rad_intercpt_temp[i] > 0:
            rad_intercpt = (tot_rad_intercpt *
                            ext_coeff_leaf_area_index_prod[i] /
                            ext_coeff_leaf_area_index_prod.sum())
        else:
            rad_intercpt = 0
        rad_intercpt_list[i] = rad_intercpt
    return rad_intercpt_list

"""Graphs for Light interception publication"""

# Figure 0
plt.figure(0, figsize=[8,8])
plt.subplot(1, 1, 1).tick_params(axis='both', which='major', labelsize=12)

atm_transm = 0.75
atm_press = 101.3
leaf_transm = 0.8

leaf_area_index = np.array([0.005, 0.39333333, 0.78166667, 1.17, 1.55833333,
                            1.94666667, 2.335, 2.72333333, 3.11166667, 3.5])
X_SP1 = 0.5
X_SP2 = 2
angles_deg = np.linspace(0, 90, 19)

SP1, SP2 = rad_intercpt_sub_daily(atm_transm, atm_press, leaf_transm,
                                  leaf_area_index, X_SP1, X_SP2, angles_deg)

TOT_LAI = 2 * leaf_area_index
SP1_LAI_PERCENT = 0.5
SP2_LAI_PERCENT = 0.5
MIN_LAI = 0.01
MAX_LAI = 7
LAI_SPECIES1 = np.linspace(MIN_LAI * SP1_LAI_PERCENT, MAX_LAI *
                           SP1_LAI_PERCENT, num=10)
LAI_SPECIES2 = np.linspace(MIN_LAI * SP2_LAI_PERCENT, MAX_LAI *
                           SP2_LAI_PERCENT, num=10)
LAI_TOTAL = LAI_SPECIES1 + LAI_SPECIES2
ARRAY_SIZE = len(LAI_SPECIES1)
K_SP1 = 0.4
K_SP2 = 0.6
K_SPECIES1 = np.ones(ARRAY_SIZE) * K_SP1
K_SPECIES2 = np.ones(ARRAY_SIZE) * K_SP2
SP_HEIGHT = np.ones(ARRAY_SIZE)  # height equals 1
WALLACE_SP1 = np.zeros(ARRAY_SIZE)
WALLACE_SP2 = np.zeros(ARRAY_SIZE)
APSIM_SP1 = np.zeros(ARRAY_SIZE)
APSIM_SP2 = np.zeros(ARRAY_SIZE)
for i in range(ARRAY_SIZE):
    APSIM_SP1[i] = rad_intercpt_apsim([[K_SPECIES1[i], LAI_SPECIES1[i]],
                                       [K_SPECIES2[i], LAI_SPECIES2[i]]])[0]
    APSIM_SP2[i] = rad_intercpt_apsim([[K_SPECIES1[i], LAI_SPECIES1[i]],
                                       [K_SPECIES2[i], LAI_SPECIES2[i]]])[1]
plt.plot(TOT_LAI, SP1, label=r'Sub-daily sp1 %s=0.5 $L$%%=%.0f' %
         (r"$\chi$", SP1_LAI_PERCENT*100), marker='o', color='k',
         markerfacecolor='white')
plt.plot(TOT_LAI, SP2, label=r'Sub-daily sp2 %s=2 $L$%%=%.0f' %
         (r"$\chi$", SP1_LAI_PERCENT*100), marker='v', color='k',
         markerfacecolor='white')
plt.plot(LAI_TOTAL, APSIM_SP1, label=r'Daily Cycles sp1 $k$=%.1f $L$%%=%.0f' %
         (K_SP1, SP1_LAI_PERCENT * 100), marker='o', color='k')
plt.plot(LAI_TOTAL, APSIM_SP2, label=r'Daily Cycles sp2 $k$=%.1f $L$%%=%.0f' %
         (K_SP2, SP2_LAI_PERCENT * 100), marker='v', color='k')
plt.ylabel('Light interception', fontsize=14, labelpad=8)
plt.xlabel('Total leaf area index ' + r'(m$^2$ m$^{-2}$)', fontsize=14,
           labelpad=8)
plt.xlim(0, 7)
plt.ylim(0, 0.8)
plt.legend(loc='upper left', prop={'size': 14}, frameon=False)
plt.savefig('Figure1.svg')
# Figure 1
plt.figure(1, figsize=(8, 28))
# Graph 1.1 : 50 / 50 lai; k1 = 0.4, k2 = 0.6
SP1_LAI_PERCENT = 0.5
SP2_LAI_PERCENT = 0.5
MIN_LAI = 0.01
MAX_LAI = 7
LAI_SPECIES1 = np.linspace(MIN_LAI * SP1_LAI_PERCENT, MAX_LAI *
                           SP1_LAI_PERCENT, num=10)
LAI_SPECIES2 = np.linspace(MIN_LAI * SP2_LAI_PERCENT, MAX_LAI *
                           SP2_LAI_PERCENT, num=10)
LAI_TOTAL = LAI_SPECIES1 + LAI_SPECIES2
ARRAY_SIZE = len(LAI_SPECIES1)
K_SP1 = 0.4
K_SP2 = 0.6
K_SPECIES1 = np.ones(ARRAY_SIZE) * K_SP1
K_SPECIES2 = np.ones(ARRAY_SIZE) * K_SP2
SP_HEIGHT = np.ones(ARRAY_SIZE)  # height equals 1
WALLACE_SP1 = np.zeros(ARRAY_SIZE)
WALLACE_SP2 = np.zeros(ARRAY_SIZE)
APSIM_SP1 = np.zeros(ARRAY_SIZE)
APSIM_SP2 = np.zeros(ARRAY_SIZE)

for i in range(ARRAY_SIZE):
    WALLACE_SP1[i] = rad_intercpt_wallace([[K_SPECIES1[i],
                                            LAI_SPECIES1[i],
                                            SP_HEIGHT[i]],
                                           [K_SPECIES2[i],
                                            LAI_SPECIES2[i],
                                            SP_HEIGHT[i]]])[0]
    APSIM_SP1[i] = rad_intercpt_apsim([[K_SPECIES1[i], LAI_SPECIES1[i]],
                                       [K_SPECIES2[i], LAI_SPECIES2[i]]])[0]
    WALLACE_SP2[i] = rad_intercpt_wallace([[K_SPECIES1[i], LAI_SPECIES1[i],
                                            SP_HEIGHT[i]],
                                           [K_SPECIES2[i], LAI_SPECIES2[i],
                                            SP_HEIGHT[i]]])[1]
    APSIM_SP2[i] = rad_intercpt_apsim([[K_SPECIES1[i], LAI_SPECIES1[i]],
                                       [K_SPECIES2[i], LAI_SPECIES2[i]]])[1]

plt.subplot(3, 1, 1).tick_params(axis='both', which='major', labelsize=20)
plt.plot(LAI_TOTAL, WALLACE_SP1, label=r'Wallace sp1 $k$=%.1f $L$%%=%.0f' %
         (K_SP1, SP1_LAI_PERCENT * 100), marker='o', color='k',
         markerfacecolor='white')
plt.plot(LAI_TOTAL, APSIM_SP1, label=r'Cycles sp1 $k$=%.1f $L$%%=%.0f' %
         (K_SP1, SP1_LAI_PERCENT * 100), marker='o', color='k')
plt.plot(LAI_TOTAL, WALLACE_SP2, label=r'Wallace sp2 $k$=%.1f $L$%%=%.0f' %
         (K_SP2, SP2_LAI_PERCENT * 100), marker='v', color='k',
         markerfacecolor='white')
plt.plot(LAI_TOTAL, APSIM_SP2, label=r'Cycles sp2 $k$=%.1f $L$%%=%.0f' %
         (K_SP2, SP2_LAI_PERCENT * 100), marker='v', color='k')
plt.ylabel('Light interception', fontsize=22, labelpad=8)
#plt.xlabel('Total leaf area index ' + r'(m$^2$ m$^{-2}$)', fontsize=15,
#           labelpad=8)
plt.text(6, 0.9, 'A', bbox={'facecolor': 'white', 'alpha': 0, 'pad': 10},
         fontsize=22)
plt.xlim(0, 7)
plt.ylim(0, 1)
plt.legend(loc='upper left', prop={'size': 18}, frameon=False)
# Graph 1.2 : 80 / 20 lai; k1 = 0.4, k2 = 0.6
SP1_LAI_PERCENT = 0.8
SP2_LAI_PERCENT = 0.2
MIN_LAI = 0.01
MAX_LAI = 7
LAI_SPECIES1 = np.linspace(MIN_LAI * SP1_LAI_PERCENT, MAX_LAI *
                           SP1_LAI_PERCENT, num=10)
LAI_SPECIES2 = np.linspace(MIN_LAI * SP2_LAI_PERCENT, MAX_LAI *
                           SP2_LAI_PERCENT, num=10)
LAI_TOTAL = LAI_SPECIES1 + LAI_SPECIES2
ARRAY_SIZE = len(LAI_SPECIES1)
K_SP1 = 0.4
K_SP2 = 0.6
K_SPECIES1 = np.ones(ARRAY_SIZE) * K_SP1
K_SPECIES2 = np.ones(ARRAY_SIZE) * K_SP2
SP_HEIGHT = np.ones(ARRAY_SIZE)  # height equals 1
WALLACE_SP1 = np.zeros(ARRAY_SIZE)
WALLACE_SP2 = np.zeros(ARRAY_SIZE)
APSIM_SP1 = np.zeros(ARRAY_SIZE)
APSIM_SP2 = np.zeros(ARRAY_SIZE)
for i in range(ARRAY_SIZE):
    WALLACE_SP1[i] = rad_intercpt_wallace([[K_SPECIES1[i], LAI_SPECIES1[i],
                                            SP_HEIGHT[i]],
                                           [K_SPECIES2[i], LAI_SPECIES2[i],
                                            SP_HEIGHT[i]]])[0]
    APSIM_SP1[i] = rad_intercpt_apsim([[K_SPECIES1[i], LAI_SPECIES1[i]],
                                       [K_SPECIES2[i], LAI_SPECIES2[i]]])[0]
    WALLACE_SP2[i] = rad_intercpt_wallace([[K_SPECIES1[i], LAI_SPECIES1[i],
                                            SP_HEIGHT[i]],
                                           [K_SPECIES2[i], LAI_SPECIES2[i],
                                            SP_HEIGHT[i]]])[1]
    APSIM_SP2[i] = rad_intercpt_apsim([[K_SPECIES1[i], LAI_SPECIES1[i]],
                                       [K_SPECIES2[i], LAI_SPECIES2[i]]])[1]


plt.subplot(3, 1, 2).tick_params(axis='both', which='major', labelsize=20)
plt.plot(LAI_TOTAL, WALLACE_SP1, label=r'Wallace sp1 $k$=%.1f $L$%%=%.0f' %
         (K_SP1, SP1_LAI_PERCENT * 100), marker='o', color='k',
         markerfacecolor='white')
plt.plot(LAI_TOTAL, APSIM_SP1, label=r'Cycles sp1 $k$=%.1f $L$%%=%.0f' %
         (K_SP1, SP1_LAI_PERCENT * 100), marker='o', color='k')
plt.plot(LAI_TOTAL, WALLACE_SP2, label=r'Wallace sp2 $k$=%.1f $L$%%=%.0f' %
         (K_SP2, SP2_LAI_PERCENT * 100), marker='v', color='k',
         markerfacecolor='white')
plt.plot(LAI_TOTAL, APSIM_SP2, label=r'Cycles sp2 $k$=%.1f $L$%%=%.0f' %
         (K_SP2, SP2_LAI_PERCENT * 100), marker='v', color='k')
plt.ylabel('Light interception', fontsize=22, labelpad=8)
#plt.xlabel('Total leaf area index ' + r'(m$^2$ m$^{-2}$)', fontsize=15,
#           labelpad=8)
plt.text(6, 0.8, 'B', bbox={'facecolor': 'white', 'alpha': 0, 'pad': 10},
         fontsize=22)
plt.xlim(0, 7)
plt.ylim(0, 1)
plt.legend(loc='upper left', prop={'size': 18}, frameon=False)
# Graph 1.3 : 20 / 80 lai; k1 = 0.4, k2 = 0.6
SP1_LAI_PERCENT = 0.2
SP2_LAI_PERCENT = 0.8
MIN_LAI = 0.01
MAX_LAI = 7
LAI_SPECIES1 = np.linspace(MIN_LAI * SP1_LAI_PERCENT, MAX_LAI *
                           SP1_LAI_PERCENT, num=10)
LAI_SPECIES2 = np.linspace(MIN_LAI * SP2_LAI_PERCENT, MAX_LAI *
                           SP2_LAI_PERCENT, num=10)
LAI_TOTAL = LAI_SPECIES1 + LAI_SPECIES2
ARRAY_SIZE = len(LAI_SPECIES1)
K_SP1 = 0.4
K_SP2 = 0.6
K_SPECIES1 = np.ones(ARRAY_SIZE) * K_SP1
K_SPECIES2 = np.ones(ARRAY_SIZE) * K_SP2
SP_HEIGHT = np.ones(ARRAY_SIZE)  # height equals 1
WALLACE_SP1 = np.zeros(ARRAY_SIZE)
WALLACE_SP2 = np.zeros(ARRAY_SIZE)
APSIM_SP1 = np.zeros(ARRAY_SIZE)
APSIM_SP2 = np.zeros(ARRAY_SIZE)
for i in range(ARRAY_SIZE):
    WALLACE_SP1[i] = rad_intercpt_wallace([[K_SPECIES1[i], LAI_SPECIES1[i],
                                            SP_HEIGHT[i]],
                                           [K_SPECIES2[i], LAI_SPECIES2[i],
                                            SP_HEIGHT[i]]])[0]
    APSIM_SP1[i] = rad_intercpt_apsim([[K_SPECIES1[i], LAI_SPECIES1[i]],
                                       [K_SPECIES2[i], LAI_SPECIES2[i]]])[0]
    WALLACE_SP2[i] = rad_intercpt_wallace([[K_SPECIES1[i], LAI_SPECIES1[i],
                                            SP_HEIGHT[i]],
                                           [K_SPECIES2[i], LAI_SPECIES2[i],
                                            SP_HEIGHT[i]]])[1]
    APSIM_SP2[i] = rad_intercpt_apsim([[K_SPECIES1[i], LAI_SPECIES1[i]],
                                       [K_SPECIES2[i], LAI_SPECIES2[i]]])[1]
plt.subplot(3, 1, 3).tick_params(axis='both', which='major', labelsize=20)
plt.plot(LAI_TOTAL, WALLACE_SP1, label=r'Wallace sp1 $k$=%.1f $L$%%=%.0f' %
         (K_SP1, SP1_LAI_PERCENT * 100), marker='o', color='k',
         markerfacecolor='white')
plt.plot(LAI_TOTAL, APSIM_SP1, label=r'Cycles sp1 $k$=%.1f $L$%%=%.0f' %
         (K_SP1, SP1_LAI_PERCENT * 100), marker='o', color='k')
plt.plot(LAI_TOTAL, WALLACE_SP2, label=r'Wallace sp2 $k$=%.1f $L$%%=%.0f' %
         (K_SP2, SP2_LAI_PERCENT * 100), marker='v', color='k',
         markerfacecolor='white')
plt.plot(LAI_TOTAL, APSIM_SP2, label=r'Cycles sp2 $k$=%.1f $L$%%=%.0f' %
         (K_SP2, SP2_LAI_PERCENT * 100), marker='v', color='k')
plt.ylabel('Light interception', fontsize=22, labelpad=8)
plt.xlabel('Total leaf area index ' + r'(m$^2$ m$^{-2}$)', fontsize=22,
           labelpad=8)
plt.text(6, 0.9, 'C', bbox={'facecolor': 'white', 'alpha': 0, 'pad': 10},
         fontsize=22)
plt.xlim(0, 7)
plt.ylim(0, 1)
plt.legend(loc='upper left', prop={'size': 18}, frameon=False)
plt.setp(plt.subplot(3, 1, 1).get_xticklabels(), visible=False)
plt.setp(plt.subplot(3, 1, 2).get_xticklabels(), visible=False)
plt.subplots_adjust(hspace=0.05)
plt.savefig('Figure2.svg')


# Figure 2 Wallace with different heights
plt.figure(2, figsize=(16, 12))
# Graph 2.1: lai:50/50, k:0.5/0.5, SP_HEIGHT:1/0.5
plt.subplot(3, 3, 1).tick_params(axis='both', which='major', labelsize=16)
SP1_LAI_PERCENT = 0.5
SP2_LAI_PERCENT = 0.5
MIN_LAI = 0.01
MAX_LAI = 7
LAI_SPECIES1 = np.linspace(MIN_LAI * SP1_LAI_PERCENT, MAX_LAI *
                           SP1_LAI_PERCENT, num=10)
LAI_SPECIES2 = np.linspace(MIN_LAI * SP2_LAI_PERCENT, MAX_LAI *
                           SP2_LAI_PERCENT, num=10)
LAI_TOTAL = LAI_SPECIES1 + LAI_SPECIES2
ARRAY_SIZE = len(LAI_SPECIES1)
K_SP1 = 0.5
K_SP2 = 0.5
HEIGHT_SP1 = 1
HEIGHT_SP2 = 0.5
K_SPECIES1 = np.ones(ARRAY_SIZE) * K_SP1
K_SPECIES2 = np.ones(ARRAY_SIZE) * K_SP2
HEIGHT_SPECIES1 = np.ones(ARRAY_SIZE) * HEIGHT_SP1
HEIGHT_SPECIES2 = np.ones(ARRAY_SIZE) * HEIGHT_SP2
WALLACE_SP1 = np.zeros(ARRAY_SIZE)
WALLACE_SP2 = np.zeros(ARRAY_SIZE)
for i in range(ARRAY_SIZE):
    WALLACE_SP1[i] = rad_intercpt_cycles([[K_SPECIES1[i], LAI_SPECIES1[i],
                                            HEIGHT_SPECIES1[i]],
                                           [K_SPECIES2[i], LAI_SPECIES2[i],
                                            HEIGHT_SPECIES2[i]]])[0]
    WALLACE_SP2[i] = rad_intercpt_cycles([[K_SPECIES1[i], LAI_SPECIES1[i],
                                            HEIGHT_SPECIES1[i]],
                                           [K_SPECIES2[i], LAI_SPECIES2[i],
                                            HEIGHT_SPECIES2[i]]])[1]
plt.plot(LAI_TOTAL, WALLACE_SP1, label=r'sp 1 $k$=%.1f $L$%%=%.0f $h$=%.1f' %
         (K_SP1, SP1_LAI_PERCENT * 100, HEIGHT_SP1), marker='o', color='k')
plt.plot(LAI_TOTAL, WALLACE_SP2, label=r'sp 2 $k$=%.1f $L$%%=%.0f $h$=%.1f' %
         (K_SP2, SP2_LAI_PERCENT * 100, HEIGHT_SP2), marker='o', color='k',
         markerfacecolor='white')
plt.text(0.35, 0.7, 'A', bbox={'facecolor': 'white', 'alpha': 0, 'pad': 10},
         fontsize=18)
plt.ylabel('Light interception', fontsize=18, labelpad=8)
plt.xlim(0, 7)
plt.ylim(0, 1.15)
plt.legend(loc='upper left', prop={'size': 16}, frameon=False)
# Graph 2.2: lai:50/50, k:0.4/0.6, SP_HEIGHT:0.5/1
plt.subplot(3, 3, 2).tick_params(axis='both', which='major', labelsize=16)
SP1_LAI_PERCENT = 0.5
SP2_LAI_PERCENT = 0.5
MIN_LAI = 0.01
MAX_LAI = 7
LAI_SPECIES1 = np.linspace(MIN_LAI * SP1_LAI_PERCENT, MAX_LAI *
                           SP1_LAI_PERCENT, num=10)
LAI_SPECIES2 = np.linspace(MIN_LAI * SP2_LAI_PERCENT, MAX_LAI *
                           SP2_LAI_PERCENT, num=10)
LAI_TOTAL = LAI_SPECIES1 + LAI_SPECIES2
ARRAY_SIZE = len(LAI_SPECIES1)
K_SP1 = 0.4
K_SP2 = 0.6
HEIGHT_SP1 = 0.5
HEIGHT_SP2 = 1
K_SPECIES1 = np.ones(ARRAY_SIZE) * K_SP1
K_SPECIES2 = np.ones(ARRAY_SIZE) * K_SP2
HEIGHT_SPECIES1 = np.ones(ARRAY_SIZE) * HEIGHT_SP1
HEIGHT_SPECIES2 = np.ones(ARRAY_SIZE) * HEIGHT_SP2
WALLACE_SP1 = np.zeros(ARRAY_SIZE)
WALLACE_SP2 = np.zeros(ARRAY_SIZE)
for i in range(ARRAY_SIZE):
    WALLACE_SP1[i] = rad_intercpt_cycles([[K_SPECIES1[i], LAI_SPECIES1[i],
                                            HEIGHT_SPECIES1[i]],
                                           [K_SPECIES2[i], LAI_SPECIES2[i],
                                            HEIGHT_SPECIES2[i]]])[0]
    WALLACE_SP2[i] = rad_intercpt_cycles([[K_SPECIES1[i], LAI_SPECIES1[i],
                                            HEIGHT_SPECIES1[i]],
                                           [K_SPECIES2[i], LAI_SPECIES2[i],
                                            HEIGHT_SPECIES2[i]]])[1]
plt.plot(LAI_TOTAL, WALLACE_SP1, label=r'sp 1 $k$=%.1f $L$%%=%.0f $h$=%.1f' %
         (K_SP1, SP1_LAI_PERCENT * 100, HEIGHT_SP1), marker='o', color='k')
plt.plot(LAI_TOTAL, WALLACE_SP2, label=r'sp 2 $k$=%.1f $L$%%=%.0f $h$=%.1f' %
         (K_SP2, SP2_LAI_PERCENT*100, HEIGHT_SP2), marker='o', color='k',
         markerfacecolor='white')
plt.text(0.35, 0.7, 'B', bbox={'facecolor': 'white', 'alpha': 0, 'pad': 10},
         fontsize=18)
# plt.ylabel('Light interception')
plt.xlim(0, 7)
plt.ylim(0, 1.15)
plt.legend(loc='upper left', prop={'size': 16}, frameon=False)
# Graph 2.3: lai:50/50, k:0.4/0.6, SP_HEIGHT:1/0.5
plt.subplot(3, 3, 3).tick_params(axis='both', which='major', labelsize=16)
SP1_LAI_PERCENT = 0.5
SP2_LAI_PERCENT = 0.5
MIN_LAI = 0.01
MAX_LAI = 7
LAI_SPECIES1 = np.linspace(MIN_LAI * SP1_LAI_PERCENT, MAX_LAI *
                           SP1_LAI_PERCENT, num=10)
LAI_SPECIES2 = np.linspace(MIN_LAI * SP2_LAI_PERCENT, MAX_LAI *
                           SP2_LAI_PERCENT, num=10)
LAI_TOTAL = LAI_SPECIES1 + LAI_SPECIES2
ARRAY_SIZE = len(LAI_SPECIES1)
K_SP1 = 0.4
K_SP2 = 0.6
HEIGHT_SP1 = 1
HEIGHT_SP2 = 0.5
K_SPECIES1 = np.ones(ARRAY_SIZE) * K_SP1
K_SPECIES2 = np.ones(ARRAY_SIZE) * K_SP2
HEIGHT_SPECIES1 = np.ones(ARRAY_SIZE) * HEIGHT_SP1
HEIGHT_SPECIES2 = np.ones(ARRAY_SIZE) * HEIGHT_SP2
WALLACE_SP1 = np.zeros(ARRAY_SIZE)
WALLACE_SP2 = np.zeros(ARRAY_SIZE)
for i in range(ARRAY_SIZE):
    WALLACE_SP1[i] = rad_intercpt_cycles([[K_SPECIES1[i], LAI_SPECIES1[i],
                                            HEIGHT_SPECIES1[i]],
                                           [K_SPECIES2[i], LAI_SPECIES2[i],
                                            HEIGHT_SPECIES2[i]]])[0]
    WALLACE_SP2[i] = rad_intercpt_cycles([[K_SPECIES1[i], LAI_SPECIES1[i],
                                            HEIGHT_SPECIES1[i]],
                                           [K_SPECIES2[i], LAI_SPECIES2[i],
                                            HEIGHT_SPECIES2[i]]])[1]
plt.plot(LAI_TOTAL, WALLACE_SP1, label=r'sp 1 $k$=%.1f $L$%%=%.0f $h$=%.1f' %
         (K_SP1, SP1_LAI_PERCENT * 100, HEIGHT_SP1), marker='o', color='k')
plt.plot(LAI_TOTAL, WALLACE_SP2, label=r'sp 2 $k$=%.1f $L$%%=%.0f $h$=%.1f' %
         (K_SP2, SP2_LAI_PERCENT*100, HEIGHT_SP2), marker='o', color='k',
         markerfacecolor='white')
plt.text(0.35, 0.7, 'C', bbox={'facecolor': 'white', 'alpha': 0, 'pad': 10},
         fontsize=18)
plt.xlim(0, 7)
plt.ylim(0, 1.15)
plt.legend(loc='upper left', prop={'size': 16}, frameon=False)
# Graph 2.4: lai:80/20, k:0.4/0.6, SP_HEIGHT:0.5/1
plt.subplot(3, 3, 4).tick_params(axis='both', which='major', labelsize=16)
SP1_LAI_PERCENT = 0.8
SP2_LAI_PERCENT = 0.2
MIN_LAI = 0.01
MAX_LAI = 7
LAI_SPECIES1 = np.linspace(MIN_LAI * SP1_LAI_PERCENT, MAX_LAI *
                           SP1_LAI_PERCENT, num=10)
LAI_SPECIES2 = np.linspace(MIN_LAI * SP2_LAI_PERCENT, MAX_LAI *
                           SP2_LAI_PERCENT, num=10)
LAI_TOTAL = LAI_SPECIES1 + LAI_SPECIES2
ARRAY_SIZE = len(LAI_SPECIES1)
K_SP1 = 0.4
K_SP2 = 0.6
HEIGHT_SP1 = 0.5
HEIGHT_SP2 = 1
K_SPECIES1 = np.ones(ARRAY_SIZE) * K_SP1
K_SPECIES2 = np.ones(ARRAY_SIZE) * K_SP2
HEIGHT_SPECIES1 = np.ones(ARRAY_SIZE) * HEIGHT_SP1
HEIGHT_SPECIES2 = np.ones(ARRAY_SIZE) * HEIGHT_SP2
WALLACE_SP1 = np.zeros(ARRAY_SIZE)
WALLACE_SP2 = np.zeros(ARRAY_SIZE)
for i in range(ARRAY_SIZE):
    WALLACE_SP1[i] = rad_intercpt_cycles([[K_SPECIES1[i], LAI_SPECIES1[i],
                                            HEIGHT_SPECIES1[i]],
                                           [K_SPECIES2[i], LAI_SPECIES2[i],
                                            HEIGHT_SPECIES2[i]]])[0]
    WALLACE_SP2[i] = rad_intercpt_cycles([[K_SPECIES1[i], LAI_SPECIES1[i],
                                            HEIGHT_SPECIES1[i]],
                                           [K_SPECIES2[i], LAI_SPECIES2[i],
                                            HEIGHT_SPECIES2[i]]])[1]
plt.plot(LAI_TOTAL, WALLACE_SP1, label=r'sp 1 $k$=%.1f $L$%%=%.0f $h$=%.1f' %
         (K_SP1, SP1_LAI_PERCENT * 100, HEIGHT_SP1), marker='o', color='k')
plt.plot(LAI_TOTAL, WALLACE_SP2, label=r'sp 2 $k$=%.1f $L$%%=%.0f $h$=%.1f' %
         (K_SP2, SP2_LAI_PERCENT*100, HEIGHT_SP2), marker='o', color='k',
         markerfacecolor='white')
plt.xlabel('Total leaf area index ' + r'(m$^2$ m$^{-2}$)', fontsize=18,
           labelpad=8)
plt.ylabel('Light interception', fontsize=18, labelpad=8)
plt.text(0.35, 0.7, 'D', bbox={'facecolor': 'white', 'alpha': 0, 'pad': 10},
         fontsize=18)
plt.xlim(0, 7)
plt.ylim(0, 1.15)
plt.legend(loc='upper left', prop={'size': 16}, frameon=False)
# Graph 2.5: lai:20/80, k:0.4/0.6, SP_HEIGHT:1/0.5
plt.subplot(3, 3, 5).tick_params(axis='both', which='major', labelsize=16)
SP1_LAI_PERCENT = 0.2
SP2_LAI_PERCENT = 0.8
MIN_LAI = 0.01
MAX_LAI = 7
LAI_SPECIES1 = np.linspace(MIN_LAI * SP1_LAI_PERCENT, MAX_LAI *
                           SP1_LAI_PERCENT, num=10)
LAI_SPECIES2 = np.linspace(MIN_LAI * SP2_LAI_PERCENT, MAX_LAI *
                           SP2_LAI_PERCENT, num=10)
LAI_TOTAL = LAI_SPECIES1 + LAI_SPECIES2
ARRAY_SIZE = len(LAI_SPECIES1)
K_SP1 = 0.4
K_SP2 = 0.6
HEIGHT_SP1 = 1
HEIGHT_SP2 = 0.5
K_SPECIES1 = np.ones(ARRAY_SIZE) * K_SP1
K_SPECIES2 = np.ones(ARRAY_SIZE) * K_SP2
HEIGHT_SPECIES1 = np.ones(ARRAY_SIZE) * HEIGHT_SP1
HEIGHT_SPECIES2 = np.ones(ARRAY_SIZE) * HEIGHT_SP2
WALLACE_SP1 = np.zeros(ARRAY_SIZE)
WALLACE_SP2 = np.zeros(ARRAY_SIZE)

for i in range(ARRAY_SIZE):
    WALLACE_SP1[i] = rad_intercpt_cycles([[K_SPECIES1[i], LAI_SPECIES1[i],
                                            HEIGHT_SPECIES1[i]],
                                           [K_SPECIES2[i], LAI_SPECIES2[i],
                                            HEIGHT_SPECIES2[i]]])[0]
    WALLACE_SP2[i] = rad_intercpt_cycles([[K_SPECIES1[i], LAI_SPECIES1[i],
                                            HEIGHT_SPECIES1[i]],
                                           [K_SPECIES2[i], LAI_SPECIES2[i],
                                            HEIGHT_SPECIES2[i]]])[1]
plt.plot(LAI_TOTAL, WALLACE_SP1, label=r'sp 1 $k$=%.1f $L$%%=%.0f $h$=%.1f' %
         (K_SP1, SP1_LAI_PERCENT * 100, HEIGHT_SP1), marker='o', color='k')
plt.plot(LAI_TOTAL, WALLACE_SP2, label=r'sp 2 $k$=%.1f $L$%%=%.0f $h$=%.1f' %
         (K_SP2, SP2_LAI_PERCENT * 100, HEIGHT_SP2), marker='o', color='k',
         markerfacecolor='white')

plt.xlabel('Total leaf area index ' + r'(m$^2$ m$^{-2}$)', fontsize=18,
           labelpad=8)
plt.text(0.35, 0.7, 'E', bbox={'facecolor': 'white', 'alpha': 0, 'pad': 10},
         fontsize=18)
plt.xlim(0, 7)
plt.ylim(0, 1.15)
plt.legend(loc='upper left', prop={'size': 16}, frameon=False)
# Graph 2.6: lai:20/80, k:0.4/0.6, SP_HEIGHT:0.5/1
plt.subplot(3, 3, 6).tick_params(axis='both', which='major', labelsize=16)
SP1_LAI_PERCENT = 0.2
SP2_LAI_PERCENT = 0.8
MIN_LAI = 0.01
MAX_LAI = 7
LAI_SPECIES1 = np.linspace(MIN_LAI * SP1_LAI_PERCENT, MAX_LAI *
                           SP1_LAI_PERCENT, num=10)
LAI_SPECIES2 = np.linspace(MIN_LAI * SP2_LAI_PERCENT, MAX_LAI *
                           SP2_LAI_PERCENT, num=10)
LAI_TOTAL = LAI_SPECIES1 + LAI_SPECIES2
ARRAY_SIZE = len(LAI_SPECIES1)
K_SP1 = 0.4
K_SP2 = 0.6
HEIGHT_SP1 = 0.5
HEIGHT_SP2 = 1
K_SPECIES1 = np.ones(ARRAY_SIZE) * K_SP1
K_SPECIES2 = np.ones(ARRAY_SIZE) * K_SP2
HEIGHT_SPECIES1 = np.ones(ARRAY_SIZE) * HEIGHT_SP1
HEIGHT_SPECIES2 = np.ones(ARRAY_SIZE) * HEIGHT_SP2
WALLACE_SP1 = np.zeros(ARRAY_SIZE)
WALLACE_SP2 = np.zeros(ARRAY_SIZE)

for i in range(ARRAY_SIZE):
    WALLACE_SP1[i] = rad_intercpt_cycles([[K_SPECIES1[i], LAI_SPECIES1[i],
                                            HEIGHT_SPECIES1[i]],
                                           [K_SPECIES2[i], LAI_SPECIES2[i],
                                            HEIGHT_SPECIES2[i]]])[0]
    WALLACE_SP2[i] = rad_intercpt_cycles([[K_SPECIES1[i], LAI_SPECIES1[i],
                                            HEIGHT_SPECIES1[i]],
                                           [K_SPECIES2[i], LAI_SPECIES2[i],
                                            HEIGHT_SPECIES2[i]]])[1]
plt.plot(LAI_TOTAL, WALLACE_SP1, label=r'sp 1 $k$=%.1f $L$%%=%.0f $h$=%.1f' %
         (K_SP1, SP1_LAI_PERCENT*100, HEIGHT_SP1), marker='o', color='k')
plt.plot(LAI_TOTAL, WALLACE_SP2, label=r'sp 2 $k$=%.1f $L$%%=%.0f $h$=%.1f' %
         (K_SP2, SP2_LAI_PERCENT*100, HEIGHT_SP2), marker='o', color='k',
         markerfacecolor='white')

plt.xlabel('Total leaf area index ' + r'(m$^2$ m$^{-2}$)', fontsize=18,
           labelpad=8)
plt.text(0.35, 0.7, 'F', bbox={'facecolor': 'white', 'alpha': 0, 'pad': 10},
         fontsize=18)
plt.xlim(0, 7)
plt.ylim(0, 1.15)
plt.legend(loc='upper left', prop={'size': 16}, frameon=False)
# Axis removal controls
plt.setp(plt.subplot(3, 3, 1).get_xticklabels(), visible=False)
plt.setp(plt.subplot(3, 3, 2).get_yticklabels(), visible=False)
plt.setp(plt.subplot(3, 3, 3).get_yticklabels(), visible=False)
plt.setp(plt.subplot(3, 3, 3).get_xticklabels(), visible=False)
plt.setp(plt.subplot(3, 3, 5).get_yticklabels(), visible=False)
plt.setp(plt.subplot(3, 3, 2).get_xticklabels(), visible=False)
plt.setp(plt.subplot(3, 3, 2).get_yticklabels(), visible=False)
plt.setp(plt.subplot(3, 3, 6).get_yticklabels(), visible=False)
plt.subplots_adjust(wspace=0.07, hspace=0.1)
plt.savefig('Figure3.svg')
# Figure 3 Cycles and Wallace comparison
plt.figure(3)
plt.subplot(1, 1, 1).tick_params(axis='both', which='major', labelsize=16)
SP1_LAI_PERCENT = 0.5
SP2_LAI_PERCENT = 0.5
MIN_LAI = 0.01
MAX_LAI = 7
LAI_SPECIES1 = np.linspace(MIN_LAI * SP1_LAI_PERCENT, MAX_LAI *
                           SP1_LAI_PERCENT, num=10)
LAI_SPECIES2 = np.linspace(MIN_LAI * SP2_LAI_PERCENT, MAX_LAI *
                           SP2_LAI_PERCENT, num=10)
LAI_TOTAL = LAI_SPECIES1 + LAI_SPECIES2
ARRAY_SIZE = len(LAI_SPECIES1)
K_SP1 = 0.4
K_SP2 = 0.6
HEIGHT_SP1 = 0.5
HEIGHT_SP2 = 1
K_SPECIES1 = np.ones(ARRAY_SIZE) * K_SP1
K_SPECIES2 = np.ones(ARRAY_SIZE) * K_SP2
HEIGHT_SPECIES1 = np.ones(ARRAY_SIZE) * HEIGHT_SP1
HEIGHT_SPECIES2 = np.ones(ARRAY_SIZE) * HEIGHT_SP2
WALLACE_SP1 = np.zeros(ARRAY_SIZE)
WALLACE_SP2 = np.zeros(ARRAY_SIZE)
CYCLES_SP1 = np.zeros(ARRAY_SIZE)
CYCLES_SP2 = np.zeros(ARRAY_SIZE)
for i in range(ARRAY_SIZE):
    WALLACE_SP1[i] = rad_intercpt_wallace([[K_SPECIES1[i], LAI_SPECIES1[i],
                                            HEIGHT_SPECIES1[i]],
                                           [K_SPECIES2[i], LAI_SPECIES2[i],
                                            HEIGHT_SPECIES2[i]]])[0]
    CYCLES_SP1[i] = rad_intercpt_cycles([[K_SPECIES1[i], LAI_SPECIES1[i],
                                          HEIGHT_SPECIES1[i]],
                                         [K_SPECIES2[i], LAI_SPECIES2[i],
                                          HEIGHT_SPECIES2[i]]])[0]
    WALLACE_SP2[i] = rad_intercpt_wallace([[K_SPECIES1[i], LAI_SPECIES1[i],
                                            HEIGHT_SPECIES1[i]],
                                           [K_SPECIES2[i], LAI_SPECIES2[i],
                                            HEIGHT_SPECIES2[i]]])[1]
    CYCLES_SP2[i] = rad_intercpt_cycles([[K_SPECIES1[i], LAI_SPECIES1[i],
                                          HEIGHT_SPECIES1[i]],
                                         [K_SPECIES2[i], LAI_SPECIES2[i],
                                          HEIGHT_SPECIES2[i]]])[1]
plt.plot(LAI_TOTAL, WALLACE_SP1,
         label=r'Wallace SP1 $k$=%.1f $L$%%=%.0f $h$=%.1f' %
         (K_SP1, SP1_LAI_PERCENT*100, HEIGHT_SP1), marker='o', color='k',
         markerfacecolor='white')
plt.plot(LAI_TOTAL, CYCLES_SP1,
         label=r'Cycles SP1 $k$=%.1f $L$%%=%.0f $h$=%.1f' %
         (K_SP1, SP1_LAI_PERCENT*100, HEIGHT_SP1), marker='o', color='k')
plt.plot(LAI_TOTAL, WALLACE_SP2,
         label=r'Wallace SP2 $k$=%.1f $L$%%=%.0f $h$=%.1f' %
         (K_SP2, SP2_LAI_PERCENT*100, HEIGHT_SP2), marker='v', color='k',
         markerfacecolor='white')
plt.plot(LAI_TOTAL, CYCLES_SP2,
         label=r'Cycles SP2 $k$=%.1f $L$%%=%.0f $h$=%.1f' %
         (K_SP2, SP2_LAI_PERCENT*100, HEIGHT_SP2), marker='v', color='k')
plt.ylabel('Light interception', fontsize=18, labelpad=8)
plt.xlabel('Total leaf area index ' + r'(m$^2$ m$^{-2}$)', fontsize=18,
           labelpad=8)
plt.xlim(0, 7)
plt.ylim(0, 1)
plt.legend(loc='upper left', prop={'size': 14}, frameon=False)
plt.savefig('Figure4.svg')
# Figure 4 Cycles and APSIM comparison
fig4 = plt.figure(4)
SP1_LAI_PERCENT = 0.33
SP2_LAI_PERCENT = 0.33
SP3_LAI_PERCENT = 0.33
K_SP1 = 0.6
K_SP2 = 0.6
K_SP3 = 0.6
HEIGHT_SP1 = 1
HEIGHT_SP2 = 2
HEIGHT_SP3 = 4
MIN_LAI = 0.01
MAX_LAI = 7
LAI_SPECIES1 = np.linspace(MIN_LAI * SP1_LAI_PERCENT, MAX_LAI *
                           SP1_LAI_PERCENT, num=10)
LAI_SPECIES2 = np.linspace(MIN_LAI * SP2_LAI_PERCENT, MAX_LAI *
                           SP2_LAI_PERCENT, num=10)
LAI_SPECIES3 = np.linspace(MIN_LAI * SP3_LAI_PERCENT, MAX_LAI *
                           SP2_LAI_PERCENT, num=10)
LAI_TOTAL = LAI_SPECIES1 + LAI_SPECIES2 + LAI_SPECIES3
ARRAY_SIZE = len(LAI_SPECIES1)
K_SPECIES1 = np.ones(ARRAY_SIZE) * K_SP1
K_SPECIES2 = np.ones(ARRAY_SIZE) * K_SP2
K_SPECIES3 = np.ones(ARRAY_SIZE) * K_SP3
HEIGHT_SPECIES1 = np.ones(ARRAY_SIZE) * HEIGHT_SP1
HEIGHT_SPECIES2 = np.ones(ARRAY_SIZE) * HEIGHT_SP2
H_SPECIES3 = np.ones(ARRAY_SIZE) * HEIGHT_SP3
APSIM_SP1 = np.zeros(ARRAY_SIZE)
APSIM_SP2 = np.zeros(ARRAY_SIZE)
APSIM_SP3 = np.zeros(ARRAY_SIZE)
CYCLES_SP1 = np.zeros(ARRAY_SIZE)
CYCLES_SP2 = np.zeros(ARRAY_SIZE)
CYCLES_SP3 = np.zeros(ARRAY_SIZE)
for i in range(ARRAY_SIZE):
    APSIM_SP1[i] = rad_intercpt_apsim([[K_SPECIES1[i], LAI_SPECIES1[i]],
                                       [K_SPECIES2[i], LAI_SPECIES2[i]],
                                       [K_SPECIES3[i], LAI_SPECIES3[i]]])[0]
    APSIM_SP2[i] = rad_intercpt_apsim([[K_SPECIES1[i], LAI_SPECIES1[i]],
                                       [K_SPECIES2[i], LAI_SPECIES2[i]],
                                       [K_SPECIES3[i], LAI_SPECIES3[i]]])[1]
    APSIM_SP3[i] = rad_intercpt_apsim([[K_SPECIES1[i], LAI_SPECIES1[i]],
                                       [K_SPECIES2[i], LAI_SPECIES2[i]],
                                       [K_SPECIES3[i], LAI_SPECIES3[i]]])[2]
    CYCLES_SP1[i] = rad_intercpt_cycles([[K_SPECIES1[i], LAI_SPECIES1[i],
                                          HEIGHT_SPECIES1[i]],
                                         [K_SPECIES2[i], LAI_SPECIES2[i],
                                          HEIGHT_SPECIES2[i]],
                                         [K_SPECIES3[i], LAI_SPECIES3[i],
                                          H_SPECIES3[i]]])[0]
    CYCLES_SP2[i] = rad_intercpt_cycles([[K_SPECIES1[i], LAI_SPECIES1[i],
                                          HEIGHT_SPECIES1[i]],
                                         [K_SPECIES2[i], LAI_SPECIES2[i],
                                          HEIGHT_SPECIES2[i]],
                                         [K_SPECIES3[i], LAI_SPECIES3[i],
                                          H_SPECIES3[i]]])[1]
    CYCLES_SP3[i] = rad_intercpt_cycles([[K_SPECIES1[i], LAI_SPECIES1[i],
                                          HEIGHT_SPECIES1[i]],
                                         [K_SPECIES2[i], LAI_SPECIES2[i],
                                          HEIGHT_SPECIES2[i]],
                                         [K_SPECIES3[i], LAI_SPECIES3[i],
                                          H_SPECIES3[i]]])[2]

axes1 = fig4.add_axes([0.1, 0.1, 0.8, 0.8])
axes2 = fig4.add_axes([0.55, 0.55, 0.3, 0.3])

axes1.plot(LAI_TOTAL, APSIM_SP1, label='APSIM (3 species)', marker='^',
         color='k', markerfacecolor='white')
axes1.plot(LAI_TOTAL, CYCLES_SP1, label=r'Cycles sp 1 $h$=%.0f' % (HEIGHT_SP1),
         marker='o', color='k', markerfacecolor='white')
axes1.plot(LAI_TOTAL, CYCLES_SP2, label=r'Cycles sp 2 $h$=%.0f' % (HEIGHT_SP2),
         marker='o', color='k', markerfacecolor='gray')
axes1.plot(LAI_TOTAL, CYCLES_SP3, label=r'Cycles sp 3 $h$=%.0f' % (HEIGHT_SP3),
         marker='o', color='k')
axes1.set_ylabel('Light interception', fontsize=18, labelpad=8)
axes1.set_xlabel('Total leaf area index ' + r'(m$^2$ m$^{-2}$)', fontsize=18,
                 labelpad=8)
axes1.set_xlim([0, 7])
axes1.set_ylim([0, 1])
axes1.legend(loc='upper left', prop={'size': 16}, frameon=False)
axes1.xaxis.set_tick_params(labelsize=16)
axes1.yaxis.set_tick_params(labelsize=16)
# Figure 4 Error between Cycles and APSIM comparison
axes2.plot(LAI_TOTAL, APSIM_SP1 - APSIM_SP1, label=r'APSIM (3 species)',
         marker='^', color='k', markerfacecolor='white')
axes2.plot(LAI_TOTAL, CYCLES_SP1 - APSIM_SP1, label=r'Cycles sp 1 $h$=%.0f' %
         (HEIGHT_SP1), marker='o', color='k', markerfacecolor='white')
axes2.plot(LAI_TOTAL, CYCLES_SP2 - APSIM_SP1, label=r'Cycles sp 2 $h$=%.0f' %
         (HEIGHT_SP2), marker='o', color='k', markerfacecolor='gray')
axes2.plot(LAI_TOTAL, CYCLES_SP3 - APSIM_SP1, label=r'Cycles sp 3 $h$=%.0f' %
         (HEIGHT_SP3), marker='o', color='k')
axes2.set_ylabel('Difference', fontsize=18, labelpad=8)
axes2.set_yticks([-0.2, -0.1, 0.0, 0.1, 0.2])
axes2.yaxis.set_tick_params(labelsize=16)
axes2.xaxis.set_tick_params(labelsize=16)
plt.savefig('Figure5.svg')


# Barilot vs Cycles
fig5 = plt.figure(5, figsize=(7, 9))
axes1 = fig5.add_axes([0.1, 0.1, 0.8, 0.8])
axes2 = fig5.add_axes([0.62, 0.13, 0.24, 0.20])
fname = 'barillot_data.csv'

data = np.loadtxt(fname, dtype='float', delimiter=',', skiprows=1)

therm_time = data[:, 0]
pea_height = data[:, 1]
wheat_height = data[:, 2]
pea_light_intercpt = data[:, 3]
wheat_light_intercpt = data[:, 4]
pea_lai = data[:, 5]
wheat_lai = data[:, 6]

pea_sim_li = np.zeros(len(therm_time))
wheat_sim_li = np.zeros(len(therm_time))
length = range(len(therm_time))
kp_final = 0.540909090909 # values obtained through optimization
kw_final = 0.510606060606 
for i in length:
    pea_sim_li[i], wheat_sim_li[i] = rad_intercpt_cycles(
        ([kp_final, pea_lai[i], pea_height[i]],
         [kw_final, wheat_lai[i], wheat_height[i]]))

axes1.plot(therm_time, pea_sim_li + wheat_sim_li, label='Mixture Cycles',
    color='k', dashes=(5,5), linewidth = 2)
axes1.plot(therm_time, pea_light_intercpt + wheat_light_intercpt,
    label='Mixture Barillot',color='k', marker='s', markerfacecolor='white',
    markersize = 5, linewidth = 0)
axes1.plot(therm_time, pea_sim_li, label='Pea Cycles', color='k',
    dashes=[5,3,1,3], linewidth = 2)
axes1.plot(therm_time, pea_light_intercpt, label='Pea Barillot', color='k',
    marker='o', markerfacecolor='white', markersize = 4, linewidth = 0)
axes1.plot(therm_time, wheat_sim_li, label='Wheat Cycles', color='k',
    dashes=[1,3], linewidth = 2)
axes1.plot(therm_time, wheat_light_intercpt, label='Wheat Barillot',color='k',
    marker='^', markerfacecolor='k', markersize = 4, linewidth = 0)

axes1.set_xlim(0, 2000)
axes1.set_ylim(0, 1)
axes1.xaxis.set_tick_params(labelsize=16)
axes1.yaxis.set_tick_params(labelsize=16)
axes1.set_xlabel("Thermal time (C-day)", fontsize=18)
axes1.set_ylabel("Light interception", fontsize=18)
#axes1.subplots_adjust(hspace=0.1)
axes1.legend(loc='upper left', prop={'size':14}, frameon=False)

total_diff = (pea_sim_li + wheat_sim_li) - (pea_light_intercpt + wheat_light_intercpt)
pea_diff = abs(pea_sim_li - pea_light_intercpt)
wheat_diff = abs(wheat_sim_li - wheat_light_intercpt)
pea_ave_abs_bias = pea_diff.mean()
wheat_ave_abs_bias = wheat_diff.mean()

axes2.plot(therm_time, pea_diff, label='Pea', color='k', marker='8', markerfacecolor='white',
    markersize = 3, linewidth = 0)
axes2.plot(therm_time, wheat_diff, ':',label='Wheat', color='k', marker='^',
    markersize = 3, linewidth = 0)
axes2.legend(loc='upper left', prop={'size':11}, frameon=False)
axes2.set_yticks([0.0, 0.05, 0.1, 0.15])
axes2.set_xticks([0, 1000, 2000])
axes2.set_ylabel('Absolute difference', fontsize=15, labelpad=8)
axes2.text(-30, 0.16, 'Mean pea bias = %.3f'%pea_ave_abs_bias, fontsize=11)
axes2.text(-30, 0.18, 'Mean wheat bias = %.3f'%wheat_ave_abs_bias, fontsize=11)

plt.savefig('Figure6.svg')

plt.show()
