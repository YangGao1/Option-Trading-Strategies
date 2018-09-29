#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Risk reversal Volatility Trading Strategy
#################
###### 白糖 ######
#################

import numpy as np
import pandas as pd
import threading as tt
import traceback as tb
import time as t
from OptionHelper import VanillaOption
from WindPy import *
from datetime import *

w.start()
w.isconnected()


class SugarRiskReversal(object):
    def __init__(self, CallCode, PutCode, Position, Period=30, aStd=3, Bollinger=False):
        self.CallCode = CallCode.upper()
        self.PutCode = PutCode.upper()
        self.position = Position
        self.Period = Period
        self.aStd = aStd
        self.Bollinger = Bollinger
        # self.futureCode = CallCode[0:5]+CallCode[-4:]
        # self.Strike = float(CallCode[8:12])

    def CalcuMeanStd(self):
        strPeriod = "ED-" + str(self.Period) + "D"
        today = date.today()
        yesterday = str(today - timedelta(days=1))
        callIVX = pd.DataFrame(
            w.wsd(self.CallCode, "us_impliedvol", strPeriod, yesterday, "TradingCalender=DCE").Data).dropna()
        putIVX = pd.DataFrame(
            w.wsd(self.PutCode, "us_impliedvol", strPeriod, yesterday, "TradingCalender=DCE").Data).dropna()
        diffIVX = np.array(callIVX) - np.array(putIVX)
        meanDiffIVX = np.mean(diffIVX)
        stdDiffIVX = np.std(diffIVX)
        return diffIVX, meanDiffIVX, stdDiffIVX

    def longPosition(self):
        string = "NOTICE! Buy " + self.PutCode + ",  sell " + self.CallCode + ",  buy Future"
        print(string)

    def shortPosition(self):
        string = "NOTICE! Buy " + self.CallCode + ",  sell " + self.PutCode + ",  sell Future"
        print(string)

    def BollingerBand(self):
        today = date.today()
        yesterday = str(today - timedelta(days=1))
        try:
            callIVX = pd.DataFrame(w.wsd(self.CallCode, "us_impliedvol", "ED-20D", yesterday, "TradingCalender=DCE").Data).dropna()
            putIVX = pd.DataFrame(w.wsd(self.PutCode, "us_impliedvol", "ED-20D", yesterday, "TradingCalender=DCE").Data).dropna()
            diffIVX = np.array(callIVX) - np.array(putIVX)
            MA = np.mean(diffIVX)
            MB = np.mean(diffIVX[0:-1])
            STD = np.std(diffIVX)
            UP = MB + 3 * STD
            DOWN = MB - 3 * STD
            return diffIVX, MA, MB, UP, DOWN
        except:
            pass

    def GammaScalp(self):
        pass

    def Cover(self, diffIVX, mean):
        if self.Position == 0:
            return 0
        elif self.Position == 1:
            if diffIVX == mean:
                string = "Buy call,  sell put,  and sell Future"
                print("Please COVER!" + string)
                return 1
        elif self.Position == -1:
            if diffIVX == mean:
                string = "Buy put,  sell call,  and buy Future"
                print("Please COVER!" + string)
                return 1
        else:
            print("position wrong!")
            return 1

    def Hedge(self):
        [callDelta],[callGamma],[callVega],[callTheta],[callRho] = w.wsq(self.CallCode,
                                                                    "rt_delta,rt_gamma,rt_vega,rt_theta,rt_rho").Data
        [putDelta],[putGamma],[putVega],[putTheta],[putRho] = w.wsq(self.PutCode,
                                                                "rt_delta,rt_gamma,rt_vega,rt_theta,rt_rho").Data
        print "CallDelta: ", callDelta
        print "CallGamma: ", callGamma
        print "CallVega: ", callVega
        print "CallTheta: ", callTheta
        print "CallRho: ", callRho
        print "PutDelta: ", putDelta
        print "PutGamma: ", putGamma
        print "PutVega: ", putVega
        print "PutTheta: ", putTheta
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

        print "Sugar RiskReversal:",self.CallCode, self.PutCode,datetime.now()
        print "Call Implied Volatility: ", myCallIVX
        print "Put Implied Volatility: ", myPutIVX
        print "Diff of IVX:", myCallIVX - myPutIVX

        diffIVX, MA, MB, UP, DOWN = self.BollingerBand()

        # open a position
        if self.position == 0:
            if myCallIVX - myPutIVX > UP:
                self.longPosition()
                self.Hedge()
                #self.position == 1
            elif myCallIVX - myPutIVX < DOWN:
                self.shortPosition()
                self.Hedge()
                #self.position == -1

        # close a position
        elif self.Position == 1:
            if diffIVX == mean:
                print("Please COVER!")
                self.shortPosition()
                self.Hedge()
                #self.position == 0

        elif self.Position == -1:
            if diffIVX == mean:
                print("Please COVER!")
                self.longPosition()
                self.Hedge()
                #self.position == 0
        else:
            print("position wrong!")

        print " "

if __name__ == '__main__':
    '''策略参数准备'''
    myCallCode = "SR801C6800.CZC"
    myPutCode = "SR801P6800.CZC"
    myPeriod = 30
    myBollinger = False
    myaStd = 3  # (1.5, 3)
    myPosition = 0  # -1:short 0:empty 1：long

    '''监控开始'''
    RR = SugarRiskReversal(myCallCode, myPutCode, myPosition, myPeriod, myaStd, myBollinger)
    timeInterval = 1


    def delayrun():
        print 'Begin...'


    timer = tt.Timer(timeInterval, delayrun)
    timer.start()
    while True:
        t.sleep(5)
        RR.Monitor()
