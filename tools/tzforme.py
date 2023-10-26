#!/usr/bin/env python3

import pytz
from datetime import datetime, timedelta

# List of timezones you want to display
timezones = [
    "Etc/UTC",
    "Europe/London",
    "Europe/Berlin",
    "Africa/Johannesburg",
    "America/Denver",
    "America/Los_Angeles",
    "Pacific/Auckland"
]


def get_time_in_timezones(timezones):
    current_time = datetime.now()

    print(f"{'Timezone':14}{'Time  (Day)':13}{'Offset':>6}{'DST':>5}{'Next Change':>13}")
    for tz_name in timezones:
        tz = pytz.timezone(tz_name)
        # Get time in given TZ
        localized_time = current_time.astimezone(tz)

        # Get TZ offset
        current_offset = tz.utcoffset(current_time).total_seconds() / 60 / 60 or ""

        # Check if DST is in effect at the current time
        is_dst = tz.dst(current_time) != timedelta(0)

        # Calculate the DST offset
        dst_offset = tz.dst(current_time).seconds / 60 / 60 if is_dst else ""

        if dst_offset:
            next_transition = [t_time for t_time in tz._utc_transition_times if t_time > current_time][0].strftime('%Y.%m.%d')
        else:
            next_transition = ""

        print(f"{tz_name.split('/')[1]:14}{localized_time.strftime('%H:%M (%a)'):13}{current_offset:>6}{dst_offset:>5}{next_transition:>13}")


if __name__ == "__main__":
    get_time_in_timezones(timezones)
