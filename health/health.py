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

weight = 105
height = 185
age = 49
body_fat_percentage = 15
waist = 108
neck = 47
hip = 0

AGE = 49
# tanaka equation
MAXIMUM_HEART_RATE = 208 - (0.7 * AGE)

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
    return 495 / ( 1.0324 - 0.19077 * log10( waist - neck ) + 0.15456 * log10( height ) ) - 450


def lean_body_mass():
    return weight * (100 - us_navy_body_fat_calc()) / 100


def lean_body_mass_boer_formula_estimate():
    """
    Lean Body Mass Boer Formula:
    (For when you don't know your body fat %)
        Men:    LBM = 0.407 * weight [kg] + 0.267 * height [cm] - 19.2
        Women:  LBM = 0.252 * weight [kg] + 0.473 * height [cm] - 48.3
    """
    return 0.407 * weight + 0.267 * height - 19.2


def mifflin_st_jeor():
    """
    Mifflin-St Jeor Equation:
        Men:    BMR = 10 * W + 6.25 * H - 5 * A + 5
        Women:  BMR = 10 * W + 6.25 * H - 5 * A - 161
    """
    return 10 * weight + 6.25 * height - 5 * age + 5


def revised_harris_benedict():
    """
    Revised Harris-Benedict Equation:
        Men:    BMR = 13.397 * W + 4.799 * H - 5.677 * A + 88.362
        Women:  BMR = 9.247 * W + 3.098 * H - 4.330 * A + 447.593
    """
    return 13.397 * weight + 4.799 * height - 5.677 * age + 88.362


def katch_mcardle(lbm):
    """
    Katch-McArdle Equation:
        First calculate LBM with lean_body_mass_boer_formula_estimate()
        BMR = 370 + (21.6 * LBM)
    """
    return 370 + (21.6 * lbm)


def body():
    lbm_est = lean_body_mass_boer_formula_estimate()
    lbm_boer = lean_body_mass()
    print(f'lbm_est: {lbm_est}\nlbm_boer: {lbm_boer}')
    bfp = us_navy_body_fat_calc()
    print(f'body fat: {bfp}\n')
    msj = mifflin_st_jeor()
    rhb = revised_harris_benedict()
    kma = katch_mcardle(lbm_boer)

    print(f'msj: {msj}\nrhb: {rhb}\nkma: {kma}\n')


def performance(resting_heart_rate):
    print(f'Resting heart rate: {resting_heart_rate}')
    print(f'Maximum heart rate: {MAXIMUM_HEART_RATE}')
    for zone in ZONE_DICT.keys():
        karvonen(zone, resting_heart_rate)


if __name__ == "__main__":

    try:
        resting_heart_rate = int(sys.argv[1])
    except IndexError:
        resting_heart_rate = 48

    body()
    performance(resting_heart_rate)
