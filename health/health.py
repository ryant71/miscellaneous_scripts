#!/usr/bin/env python3

"""
Source(s):
    - https://www.omnicalculator.com/health
    - https://github.com/pyrob2142/FastingWidget#real-time-calories-estimation

Mifflin-St Jeor Equation:
Revised Harris-Benedict Equation:
Katch-McArdle Formula:

W Weight in kilograms (kg)
H Height in centimenters (cm)
A Age in years
F Body fat in percent (%)


Training zones using Karvonen heart rate formula

standard calculation
MAXIMUM_HEART_RATE = 220 - AGE

tanaka equation
MAXIMUM_HEART_RATE = 208 - (0.7 * AGE)
"""

import sys
from math import log10

HEIGHT = 185
AGE = 51
WAIST = 108
NECK = 47
HIP = 0

# tanaka equation
MAXIMUM_HEART_RATE = 208 - (0.7 * AGE)

# as reported by garmin watch
RESTING_HEART_RATE = 49

# putting this here, but this will be calculated in karvonen function
HEART_RATE_RESERVE = MAXIMUM_HEART_RATE - RESTING_HEART_RATE


ZONE_DICT = {
    'Zone 0': (0.4, 0.5, 'Easy'),
    'Zone 1': (0.5, 0.6, 'Warm-up, recovery'),
    'Zone 2': (0.6, 0.7, 'Moderate,  85/15% fat/carb, light run 30 minutes, normal conversation'),
    'Zone 3': (0.7, 0.8, 'Aerobic,   50/50% fat/carb, plateau=bad'),
    'Zone 4': (0.8, 0.9, 'Anaerobic, 15/85% fat/carb feel burn, lactic acid, heavy weights, 30-45 mins'),
    'Zone 5': (0.9, 1.0, 'Crazy red line, 45-60 seconds, interval'),
}


def float_to_percent(lower, upper):
    return f'{int(100*lower)}-{int(100*upper)}%'


def karvonen(zone, resting_heart_rate):
    """
    Karvonen equation for calculating heart-rate zones
    """
    lower, upper, text = ZONE_DICT[zone]
    percent_range = float_to_percent(lower, upper)
    lower = int(((MAXIMUM_HEART_RATE - resting_heart_rate) * lower) + resting_heart_rate)
    upper = int(((MAXIMUM_HEART_RATE - resting_heart_rate) * upper) + resting_heart_rate)
    print(f'{zone} | {percent_range:<8} {lower:>4} - {upper} | ({text})')


def us_navy_body_fat_calc():
    """
    US Navy Body Fat Calculator:
        Men: BF = 495 / ( 1.0324 - 0.19077 * log10( waist - neck ) + 0.15456 * log10( height ) ) - 450
        Women: BF = 495 / ( 1.29579 - 0.35004 * log10( waist + hip - neck ) + 0.22100 * log10( height ) ) - 450
    """
    return 495 / (1.0324 - 0.19077 * log10(WAIST - NECK) + 0.15456 * log10(HEIGHT)) - 450


def lean_body_mass(weight):
    return weight * (100 - us_navy_body_fat_calc()) / 100


def boer_formula_lean_body_mass_estimate(weight):
    """
    Lean Body Mass Boer Formula:
    (For when you don't know your body fat %)
        Men:    LBM = 0.407 * weight [kg] + 0.267 * height [cm] - 19.2
        Women:  LBM = 0.252 * weight [kg] + 0.473 * height [cm] - 48.3
    """
    return 0.407 * weight + 0.267 * HEIGHT - 19.2


def mifflin_st_jeor_lean_basal_metabolic_rate(weight):
    """
    The Mifflin-St. Jeor calculator (or equation) calculates your
    basal metabolic rate (BMR), and its results are based on an
    estimated average. Basal metabolic rate is the amount of energy expended
    per day at rest (how many calories you would burn on bed rest).

    Mifflin-St Jeor Equation:
        Men:    BMR = 10 * W + 6.25 * H - 5 * A + 5
        Women:  BMR = 10 * W + 6.25 * H - 5 * A - 161
    """
    return 10 * weight + 6.25 * HEIGHT - 5 * AGE + 5


def revised_harris_benedict_lean_basal_metabolic_rate(weight):
    """
    Basal metabolic rate (BMR), and its results are based on an
    estimated average. Basal metabolic rate is the amount of energy expended
    per day at rest (how many calories you would burn on bed rest).


    Revised Harris-Benedict Equation:
        Men:    BMR = 13.397 * W + 4.799 * H - 5.677 * A + 88.362
        Women:  BMR = 9.247 * W + 3.098 * H - 4.330 * A + 447.593
    """
    return 13.397 * weight + 4.799 * HEIGHT - 5.677 * AGE + 88.362


def katch_mcardle_lean_basal_metabolic_rate(lbm):
    """
    Basal metabolic rate (BMR), and its results are based on an
    estimated average. Basal metabolic rate is the amount of energy expended
    per day at rest (how many calories you would burn on bed rest).

    Katch-McArdle Equation:
        First calculate LBM with boer_formula_lean_body_mass_estimate()
        BMR = 370 + (21.6 * LBM)
    """
    return 370 + (21.6 * lbm)


def body(weight):
    lbm_boer = boer_formula_lean_body_mass_estimate(weight)
    lbm_est = lean_body_mass(weight)
    bfp = us_navy_body_fat_calc()
    print('\nBody Weight:')
    print(f'USN body fat estimation: {bfp}')
    print(f'Lean Body Mass Estimate (Standard Method): {lbm_est}')
    print(f'Lean Body Mass Estimate (Boer Method): {lbm_boer}')
    msj = mifflin_st_jeor_lean_basal_metabolic_rate(weight)
    rhb = revised_harris_benedict_lean_basal_metabolic_rate(weight)
    kma = katch_mcardle_lean_basal_metabolic_rate(lbm_boer)
    print('\nDaily Basal Metabolic Rate Estimates:')
    print(f'Mifflin St Jeor: {int(msj)}')
    print(f'Revised Harris Benedict: {int(rhb)}')
    print(f'Katch McArdle: {int(kma)}')


def performance(resting_heart_rate):
    print('\nPerformance:')
    print(f'Resting heart rate: {resting_heart_rate}')
    print(f'Maximum heart rate: {MAXIMUM_HEART_RATE}')
    for zone in ZONE_DICT.keys():
        karvonen(zone, resting_heart_rate)


if __name__ == "__main__":

    try:
        weight = int(sys.argv[1])
        resting_heart_rate = int(sys.argv[2])
    except IndexError:
        print(f'Usage: {sys.argv[0]} <weight> <resting-heart-rate>')
        sys.exit(1)

    body(weight)
    performance(resting_heart_rate)
