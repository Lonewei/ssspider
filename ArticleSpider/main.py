# _*_ coding: utf-8 _*_
from scrapy.cmdline import execute

__author__ = 'onewei'
__date__ = '2017/7/12 3:23'

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
execute(["scrapy", "crawl", "jobbole"])
