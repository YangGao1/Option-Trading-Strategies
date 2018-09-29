#coding=utf-8
import numpy as np
import pandas as pd
import threading as tt
import traceback as tb
import time as t
from WindPy import *
from datetime import *
import sys

from soybeanmealBuySellVol import SoybeanmealBuySellVol
from soybeanmealRiskReversal import SoybeanmealRiskReversal
from soybeanmealskew import Soybeanmealskew
from soybeanmealskew import optionchoose as optionchoose1
from soybeanmealskew import hisskew1

from sugarBuySellVol import SugarBuySellVol
from sugarRiskReversal import SugarRiskReversal
from sugarskew import Sugarskew
from sugarskew import optionchoose2
from sugarskew import hisskew2

from etfBuySellVol import ETFBuySellVol
from etfRiskReversal import ETFRiskReversal
from etfTermStructure import ETFTermStructure
from etfskew import ETFoptionskew
from etfskew import optionchoose3
from etfskew import hisskew

import warnings

a=29/7
print(a)


