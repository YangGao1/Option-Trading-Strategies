#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Term Structure
###################
###### 50ETF ######
###################

import numpy as np
import pandas as pd
import threading as tt
import traceback as tb
import time as t
from WindPy import *
from datetime import *
w.start()
w.isconnected()


class ETFTermStructure(object):
    def __init__(self, Code0, Code1, Code2, Code3, paraList, position):
        self.Code0 = Code0.upper()
        self.Code1 = Code1.upper()
        self.Code3 = Code2.upper()
        self.Code6 = Code3.upper()
        [self.mean_period, self.num_type, self.num, self.cl] = paraList

        # self.TSPeriod = TSPeriod
        # self.RangeType = int(RangeType)
        # self.RangePara = float(RangePara)

        self.position = position
        self.Underlying0 = '510050.SH'
        self.Underlying1 = '510050.SH'
        self.Underlying3 = '510050.SH'
        self.Underlying6 = '510050.SH'

    def CalcuTermStruct(self):
        today = date.today()
        yesterday = "-1D"
        strPeriod = "-20D"
        IVX1 = pd.DataFrame(w.wsd(self.Code1, "us_impliedvol", strPeriod, yesterday, "TradingCalender=DCE").Data[0]).dropna()
        IVX3 = pd.DataFrame(w.wsd(self.Code3, "us_impliedvol", strPeriod, yesterday, "TradingCalender=DCE").Data[0]).dropna()
        IVX6 = pd.DataFrame(w.wsd(self.Code6, "us_impliedvol", strPeriod, yesterday, "TradingCalender=DCE").Data[0]).dropna()

        IVX = (pd.DataFrame([IVX1[0], IVX3[0], IVX6[0]], index=list('136'))).T

        meanIVX = IVX.mean()
        stdIVX = IVX.std()
        return list(meanIVX), list(stdIVX)

    def CalcuHV(self, Code, HVPeriod):
        today = date.today()
        yesterday = today - timedelta(days=1)
        strPeriod = "TD-"+str(HVPeriod)+"D"
        closePrice = pd.DataFrame(w.wsd(Code, "close", strPeriod, yesterday, "TradingCalender=DCE").Data[0]).dropna()
        preClosePrice = pd.DataFrame(w.wsd(Code, "pre_close", strPeriod, yesterday, "TradingCalender=DCE").Data[0]).dropna()
        dailyReturn = closePrice / preClosePrice    # 计算每日价格变动百分比
        logReturn = np.log(dailyReturn).dropna()    # 取对数
        HV = np.std(logReturn) * np.sqrt(252.0)
        return HV

    def buyButterfly(self):
        string = "NOTICE! Buy 1 "+self.Code1+" and 1 "+self.Code6+", and sell 2 "+self.Code3
        print(string)

    def sellButterfly(self):
        string = "NOTICE! Sell 1 "+self.Code1+" and 1 "+self.Code6+", and buy 2 "+self.Code3
        print(string)

    def Expire(self):
        today = date.today()
        tommorrow = today + timedelta(days=1)
        expire = str(w.wsd(self.Code0, "exe_enddate", "ED0TD", today, "TradingCalender=DCE").Data[0][0])

        if self.position == 'flat':
            return False
        elif expire == tommorrow:
            string = "Option of this month will expire tommorrow!"
            print("Please COVER!"+string)
            return True
        else:
            return False

    def Hedge(self):
        [Delta1],[Gamma1],[Vega1],[Theta1],[Rho1] = w.wsq(self.Code1,
                                                              "rt_delta,rt_gamma,rt_vega,rt_theta,rt_rho").Data
        [Delta2],[Gamma2],[Vega2],[Theta2],[Rho2] = w.wsq(self.Code3,
                                                              "rt_delta,rt_gamma,rt_vega,rt_theta,rt_rho").Data
        [Delta3],[Gamma3],[Vega3],[Theta3],[Rho3] = w.wsq(self.Code6,
                                                              "rt_delta,rt_gamma,rt_vega,rt_theta,rt_rho").Data
        [Delta],[Gamma],[Vega],[Theta],[Rho] = [Delta1+Delta3-2*Delta2],[Gamma1+Gamma3-2*Gamma2],[Vega1+Vega3-2*Vega2],\
                                               [Theta1+Theta3-2*Theta2],[Rho1+Rho3-2*Rho2]
        print "Delta1: ", Delta1
        print "Gamma1: ", Gamma1
        print "Vega1: ", Vega1
        print "Theta1: ", Theta1
        print "Rho1: ", Rho1
        print "Delta2: ", Delta2
        print "Gamma2: ", Gamma2
        print "Vega2: ", Vega2
        print "Theta2: ", Theta2
        print "Rho2: ", Rho2
        print "Delta3: ", Delta3
        print "Gamma3: ", Gamma3
        print "Vega3: ", Vega3
        print "Theta3: ", Theta3
        print "Rho3: ", Rho3

        print "Delta: ", Delta
        print "Gamma: ", Gamma
        print "Vega: ", Vega
        print "Theta: ", Theta
        print "Rho: ", Rho

    def Monitor(self):
        print 'ETFTermStructure',self.Code0, self.Code1, self.Code3, self.Code6,datetime.now()
        meanIVX, stdIVX = self.CalcuTermStruct()
        mean_ivx16 = (meanIVX[0] + meanIVX[2]) / 2.0
        ivx3 = meanIVX[1]
        if self.Expire():
            return
        if self.num_type == 1:    # 1.5-2.5*std
            _num = abs(self.num) * (stdIVX[0] + stdIVX[2]) / 2.0
        elif self.num_type == 2:  # 1-2 basis point
            _num = abs(self.num) * 0.01
        elif self.num_type == 3:  # 4%-8% of current vol
            _num = abs(self.num) / 100.0 * self.CalcuHV(self.Underlying3, 20)
        else:
            raise ValueError('error num_type')     

        # print "Your selected num:", float(_num)

        # open a position
        if self.position == 'flat':
            if ivx3 > mean_ivx16 + _num:
                self.buyButterfly()
                # self.Hedge()
                #self.position = 'buy'
            elif ivx3 < mean_ivx16 - _num:
                self.sellButterfly()
                # self.Hedge()
                #self.position = 'short'

        # close a position
        elif mean_ivx16 + self.cl * _num >= ivx3 and self.position == 'buy':
            self.sellButterfly()
            # self.Hedge()
            #self.position = 'flat'
        elif ivx3 >= mean_ivx16 - self.cl * _num and self.position == 'short':
            self.buyButterfly()
            # self.Hedge()
            #self.position = 'flat'

        # print "Implied Volatility 2: ", meanIVX[1]
        # print "Implied Volatility 1: ", meanIVX[0]
        # print "Implied Volatility 3: ", meanIVX[2]

        print " "


if __name__ == '__main__':
    myCode0 = "10000871.SH"  # 1705 Call 2.35
    myCode1 = "10000798.SH"  # 1706 Call 2.35
    myCode2 = "10000845.SH"  # 1709 Call 2.35
    myCode3 = "10000889.SH"  # 1712 Call 2.35
    # my_term_period = 1     # 期限结构计算的回顾样本数量, trading day
    my_mean_period = 20     # 均值计算的回顾样本数量, trading day
    my_num_type = 2        # num类型: 1, 2, 3
    my_num = 2             # 1.5-2.5  1-2 basis point  4%-8% current vol
    my_cl = 0.5             # close parameter
    my_para_list = [my_mean_period, my_num_type, my_num, my_cl]
    # myTSPeriod = 20
    # myRangeType = 2  # 1, 2, 3
    # myRangePara = 0.05  # 1.5-2.5  1-2 basis point  4%-8% current vol
    myposition = 'flat'  # flat long-short buy-sell

    '''监控开始'''
    TS = ETFTermStructure(myCode0, myCode1, myCode2, myCode3, my_para_list, myposition)
    timeInterval = 1

    def delayrun():
        print 'Begin...'
    timer = tt.Timer(timeInterval, delayrun)
    timer.start()
    while True:
        t.sleep(5)
        TS.Monitor()
