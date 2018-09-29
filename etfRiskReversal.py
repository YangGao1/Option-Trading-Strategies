#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Risk reversal Volatility Trading Strategy
###################
###### 50ETF ######
###################

from __future__ import division
import numpy as np
import pandas as pd
import threading as tt
import traceback as tb
import time as t
from WindPy import *
from datetime import *

w.start()
w.isconnected()


class ETFRiskReversal(object):
    def __init__(self, CallCode, PutCode, Position, mean_period, para_a, para_b):
        self.CallCode = CallCode.upper()
        self.PutCode = PutCode.upper()
        self.position = Position
        self.mean_period = mean_period
        self.para_a = para_a
        self.para_b = para_b

    def CalcuMeanStd(self):
        strPeriod = "-20D"
        today = date.today()
        yesterday = "-1D"
        callIVX = pd.DataFrame(w.wsd(self.CallCode, "us_impliedvol", strPeriod, yesterday, "TradingCalender=DCE").Data).dropna()
        putIVX = pd.DataFrame(w.wsd(self.PutCode, "us_impliedvol", strPeriod, yesterday, "TradingCalender=DCE").Data).dropna()
        try:
            diffIVX = np.array(callIVX)- np.array(putIVX)
            meanDiffIVX = np.mean(diffIVX[0][:-1])
            stdDiffIVX = np.std(diffIVX[0][:-1])
            diffIVXnew=diffIVX[0][-1]
        except:
            pass
        return diffIVXnew, meanDiffIVX, stdDiffIVX

    def longPosition(self):
        string = "NOTICE! Buy " + self.PutCode + ",  sell " + self.CallCode + ",  buy Future"
        print(string)

    def shortPosition(self):
        string = "NOTICE! Buy " + self.CallCode + ",  sell " + self.PutCode + ",  sell Future"
        print(string)

    def BollingerBand(self):
        """DROP OUT"""
        today = date.today()
        yesterday = str(today - timedelta(days=1))
        callIVX = pd.DataFrame(w.wsd(self.CallCode, "us_impliedvol", "TD-20D", yesterday, "TradingCalender=DCE").Data).dropna()
        putIVX = pd.DataFrame(w.wsd(self.PutCode, "us_impliedvol", "TD-20D", yesterday, "TradingCalender=DCE").Data).dropna()
        diffIVX = np.array(callIVX) - np.array(putIVX)
        MA = np.mean(diffIVX)
        MB = np.mean(diffIVX[0:-1])
        STD = np.std(diffIVX)
        UP = MB + 2 * STD
        DOWN = MB - 2 * STD
        return diffIVX, MA, MB, UP, DOWN

    def GammaScalp(self):
        pass

    def Hedge(self):
        [callDelta],[Gamma],[Vega],[callTheta],[callRho] = w.wsq(self.CallCode, "rt_delta,rt_gamma,rt_vega,rt_theta,rt_rho").Data
        [putDelta],[putTheta],[putRho] = w.wsq(self.PutCode, "rt_delta,rt_theta,rt_rho").Data
        print "CallDelta: ", callDelta
        print "PutDelta: ", putDelta
        print "Gamma: ", Gamma
        print "Vega: ", Vega
        print "CallTheta: ", callTheta
        print "PutTheta: ", putTheta
        print "CallRho: ", callRho
        print "PutRho: ", putRho

    def Monitor(self):
        """Wind数据准备"""

        # rate = w.wsq("CGB1Y.WI", "rt_latest").Data[0][0] / 100.0
        # # rate = 0.031412
        # currentCallPrice = w.wsq(myCallCode, "rt_latest").Data[0][0]
        # currentPutPrice = w.wsq(myPutCode, "rt_latest").Data[0][0]
        # currentFuturePrice = w.wsq(self.futureCode, "rt_latest").Data[0][0]
        # callVO = VanillaOption(spot=currentFuturePrice, strike=self.Strike, maturity=4.0/12, rate=rate, vol=0.12, optionType='Call')
        # putVO = VanillaOption(spot=currentFuturePrice, strike=self.Strike, maturity=4.0/12, rate=rate, vol=0.12, optionType='Put')
        # myCallIVX = callVO.impVol(currentPrice=currentCallPrice, modelType='mc')
        # myPutIVX = putVO.impVol(currentPrice=currentPutPrice, modelType='mc')
        myCallIVX = w.wsq(self.CallCode, "rt_imp_volatility").Data[0][0]  # the real time ivx of wind
        myPutIVX = w.wsq(self.PutCode, "rt_imp_volatility").Data[0][0]

        print 'ETFRiskReversal', self.CallCode, self.PutCode,datetime.now()
        print "Call Implied Volatility: ", myCallIVX
        print "Put Implied Volatility: ", myPutIVX
        print "Diff of IVX:", myCallIVX - myPutIVX

        # if self.Bollinger:
        #     diffIVX, MA, MB, UP, DOWN = self.BollingerBand()
        #     indicator = self.Cover(myCallIVX - myPutIVX, MA)
        #     if indicator == 1:
        #         return
        #     if myCallIVX - myPutIVX > UP:
        #         self.longPosition()
        #         self.Hedge()

        #     elif myCallIVX - myPutIVX < DOWN:
        #         self.shortPosition()
        #         self.Hedge()

        #     print "UP: ", UP
        #     print "DOWN: ", DOWN

        # else:

        diff_ivx, mean_diff_ivx, std_diff_ivx = self.CalcuMeanStd()
        
        # OPEN POSITION
        a = abs(float(self.para_a))
        b = min(float(self.para_b), 1.0/self.para_b)

        if self.position == 'flat':
            if diff_ivx > mean_diff_ivx + a * std_diff_ivx:
                self.longPosition()
                self.Hedge()
                #self.position = 'buy'
            elif diff_ivx < mean_diff_ivx - a * std_diff_ivx:
                self.shortPosition()
                self.Hedge()
                #self.position = 'short'

        # close a position
        elif mean_diff_ivx - b * std_diff_ivx < diff_ivx < mean_diff_ivx + b * std_diff_ivx:
            if self.position == 'buy':
                print('平仓！')
                self.shortPosition()
                self.Hedge()
                #self.position = 'flat'
            elif self.position == 'short':
                print('平仓！')
                self.longPosition()
                self.Hedge()
                #self.position = 'flat'

        # print "Mean of diffIVX: ", mean_diff_ivx
        # print "Standard Deviation of diffIVX: ", std_diff_ivx
        #
        print " "


if __name__ == '__main__':
    '''策略参数准备'''
    myCallCode = "10000871.SH" # 1706 CALL 2.35
    myPutCode  = "10000876.SH" # 1706 PUT 2.35
    my_mean_period = 20
    my_para_a = 1      # open parameter: 1.5 ~ 3.0
    my_para_b = 0.3    # close parameter: 0 ~ 1.0

    myPosition = 'flat'  # flat long-short buy-sell
    # Bollinger Band: mean_period = 20 & para_a = 2.0

    '''监控开始'''
    RR = ETFRiskReversal(myCallCode, myPutCode, myPosition, my_mean_period, my_para_a, my_para_b)
    timeInterval = 1


    def delayrun():
        print 'Begin...'


    timer = tt.Timer(timeInterval, delayrun)
    timer.start()
    while True:
        t.sleep(5)
        RR.Monitor()
