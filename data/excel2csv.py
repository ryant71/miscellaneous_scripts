#!/usr/bin/env python

import sys
import csv
from openpyxl import load_workbook

# default to first worksheet
wb = load_workbook(filename = sys.argv[1])
ws = wb.worksheets[0]

for row in ws.rows:
    print(','.join([str(item.value) for item in row]))


