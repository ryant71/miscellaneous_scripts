#!/usr/bin/env python

"""
Training zones using Karvonen heart rate formula

standard calculation
MAXIMUM_HEART_RATE = 220 - AGE

tanaka equation
MAXIMUM_HEART_RATE = 208 - (0.7 * AGE)
"""

import sys

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


def main(resting_heart_rate):
    print(f'Resting heart rate: {resting_heart_rate}')
    print(f'Maximum heart rate: {MAXIMUM_HEART_RATE}')
    for zone in ZONE_DICT.keys():
        karvonen(zone, resting_heart_rate)


if __name__ == "__main__":

    try:
        resting_heart_rate = int(sys.argv[1])
    except IndexError:
        resting_heart_rate = 48

    main(resting_heart_rate)
