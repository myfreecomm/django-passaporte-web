# -*- coding: utf-8 -*-
"""
Source: https://github.com/brosner/django-timezones
Original file: https://github.com/brosner/django-timezones/blob/3ce983c23b50ee5277c6ba6c5b7af9952a281cd7/timezones/zones.py
"""
from datetime import datetime

import pytz

ALL_TIMEZONE_CHOICES = tuple(zip(pytz.all_timezones, pytz.all_timezones))
COMMON_TIMEZONE_CHOICES = tuple(zip(pytz.common_timezones, pytz.common_timezones))
PRETTY_TIMEZONE_CHOICES = []

for tz in pytz.common_timezones:
    now = datetime.now(pytz.timezone(tz))
    ofs = now.strftime("%z")
    PRETTY_TIMEZONE_CHOICES.append((int(ofs), tz, "(GMT%s) %s" % (ofs, tz)))
PRETTY_TIMEZONE_CHOICES.sort()
for i in xrange(len(PRETTY_TIMEZONE_CHOICES)):
    PRETTY_TIMEZONE_CHOICES[i] = PRETTY_TIMEZONE_CHOICES[i][1:]
