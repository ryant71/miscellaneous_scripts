#!/usr/bin/env python3

import sys
import pytz
from datetime import datetime, timedelta

# List of timezones you want to display
timezones = [
    ("Etc/UTC", 'north'),
    ("Europe/London", 'north'),
    ("Europe/Berlin", 'north'),
    ("Africa/Johannesburg", 'south'),
    ("America/Santiago", 'south'),
    ("America/Denver", 'north'),
    ("America/Los_Angeles", 'north'),
    ("Australia/Brisbane", 'south'),
    ("Australia/Melbourne", 'south'),
    ("Pacific/Auckland", 'south'),
]


def next_change_value(current_offset, next_transition_datetime, hemisphere):
    mid = datetime(next_transition_datetime.year, 7, 2, 0, 0, 0)

    if hemisphere == 'south':
        if current_offset >= 0:
            if next_transition_datetime > mid:  # -> summer
                return 1
            if next_transition_datetime < mid:  # -> winter
                return -1
        else:
            if next_transition_datetime > mid:  # -> summer
                return 1
            if next_transition_datetime < mid:  # -> winter
                return -1
    if hemisphere == 'north':
        if current_offset >= 0:
            if next_transition_datetime > mid:  # -> summer
                return -1
            if next_transition_datetime < mid:  # -> winter
                return 1
        else:
            if next_transition_datetime > mid:  # -> summer
                return -1
            if next_transition_datetime < mid:  # -> winter
                return 1


def get_time_in_timezones(timezones, override_date=None):
    current_time = override_date if override_date else datetime.now()
    print(f"{current_time}")
    print(f"{'Timezone':14}{'Time  (Day)':13}{'Offset':>6}{'DST':>5}{'Next Change':>14}{'':>4}")
    for timezone in timezones:

        tz_name = timezone[0]

        hemisphere = timezone[1]

        tz = pytz.timezone(tz_name)

        # Get time in given TZ
        localized_time = current_time.astimezone(tz)

        # Get TZ offset
        current_offset = tz.utcoffset(current_time).total_seconds() / 60 / 60 or 0

        # Check if DST is in effect at the current time
        is_dst = tz.dst(current_time) != timedelta(0)

        # Calculate the DST offset
        dst_offset = tz.dst(current_time).seconds / 60 / 60 if is_dst else 0

        try:
            next_transition_datetime = [t_time for t_time in tz._utc_transition_times if t_time > current_time][0]
            next_transition = next_transition_datetime.strftime('%Y.%m.%d')
        except (AttributeError, IndexError):
            next_transition = ""

        if next_transition:
            next_offset = int(current_offset) + next_change_value(current_offset, next_transition_datetime, hemisphere)
        else:
            next_offset = ""

        current_offset = int(current_offset) if current_offset else ""
        dst_offset = int(dst_offset) if dst_offset else ""

        # print(f"{tz_name.split('/')[1]:14}{dst_offset:4}{north:6}{south:6}{next_offset:5}")
        print(f"{tz_name.split('/')[1]:14}{localized_time.strftime('%H:%M (%a)'):13}{current_offset:>6}{dst_offset:>5}{next_transition:>14}{next_offset:>4}")


if __name__ == "__main__":
    try:
        od = datetime.strptime(sys.argv[1], "%Y.%m.%d")
        now = datetime.now()
        override_date = datetime(od.year, od.month, od.day, now.hour, now.minute, now.second, now.microsecond)
    except IndexError:
        override_date = None

    get_time_in_timezones(timezones, override_date)
