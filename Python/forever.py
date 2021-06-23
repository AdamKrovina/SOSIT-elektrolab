# -*- coding: utf-8 -*-
"""
Created on Tue Dec  8 19:04:09 2020

@author: Adam Krovina
"""

#!/usr/bin/python
from subprocess import Popen
import sys

filename = sys.argv[1]
while True:
    print("\nStarting " + filename)
    p = Popen("python " + filename, shell=True)
    p.wait()