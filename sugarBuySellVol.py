#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Buy/Sell Volatility
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


class SugarBuySellVol(object):
    def __init__(self, Code, Position, HVPeriod, TotalTime, Type, StdPara, CoverPara):
        self.Code = Code
        self.position = Position
        self.HVPeriod = HVPeriod
        self.TotalTime = TotalTime
        self.Type = Type
        self.StdPara = float(StdPara)
        self.CoverPara = float(CoverPara)
        self.Underlying = "SR801.CZC"


    def CalcuVol(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        # startDay = "2017-04-19"
        strPeriod = "ED-"+str(self.TotalTime)+"D"
        # t = w.wsd(self.Code, "close", strPeriod, yesterday, "TradingCalender=DCE").Data
        try:
            closePrice = pd.DataFrame(w.wsd(self.Underlying, "close", strPeriod, yesterday, "TradingCalender=DCE").Data[0]).dropna()
            preClosePrice = pd.DataFrame(w.wsd(self.Underlying, "pre_close",strPeriod, yesterday, "TradingCalender=DCE").Data[0]).dropna()
            dailyReturn = closePrice/preClosePrice
            logReturn = np.log(dailyReturn.dropna())
            HV = (pd.rolling_std(logReturn, window=self.HVPeriod) * np.sqrt(252.0)).dropna()
            meanHV = HV[0].mean()
            stdHV = HV[0].std()
        except TypeError:
            pass
        return meanHV, stdHV

    def buyStraddle(self):
        string = "NOTICE! Buy "+self.Code+", and buy corresponding opposite option with same strike price!"
        print(string)

    def sellStraddle(self):
        string = "NOTICE! Sell "+self.Code+", and sell corresponding opposite option with same strike price!"
        print(string)

    def Protection(self):
        pass

    def Cover():
        pass

    def Expire(self):
        today = date.today()
        tommorrow = today + timedelta(days=1)
        expire = w.wsd(self.Code, "exe_enddate", "ED0TD", today, "TradingCalender=DCE").Data[0][0]
        if self.position == 0:
            return False
        elif expire == tommorrow:
            string = "Option will expire tommorrow!"
            print(string +"Please COVER "+str(self.atCode)+'and'+str(self.outCode))
            return True
        else:
            return False

    def Hedge(self):
        [Delta],[Gamma],[Vega],[Theta],[Rho] = w.wsq(self.Code,"rt_delta,rt_gamma,rt_vega,rt_theta,rt_rho").Data
        print "Delta: ", Delta
        print "Gamma: ", Gamma
        print "Vega: ", Vega
        print "Theta: ", Theta
        print "Rho: ", Rho

    def Monitor(self):
        # currentPrice = w.wsq(self.Code, "rt_latest").Data[0][0]
        # callVO = VanillaOption(spot=2789.0, strike=2800.0, maturity=4.0 / 12, rate=rate, vol=0.12, optionType='Call')
        IVX = w.wsq(self.Code, "rt_imp_volatility").Data[0][0]  # the real time ivx of wind
        try:
            meanHV, stdHV = self.CalcuVol()
        except UnboundLocalError:
            return

        print "Sugar BuySellVol:",self.Code,datetime.now()
        print "Implied Volatility: ", IVX
        print "Realized Volatility:", meanHV

        if self.Expire():
            return

        if self.Type == 2:
            # open a position
            if IVX > meanHV + self.StdPara * stdHV and self.position == 0:
                self.sellStraddle()
                self.Hedge()
                #self.position == -1

            elif IVX < meanHV - self.StdPara * stdHV and self.position == 0:
                self.buyStraddle()
                self.Hedge()
                #self.position == 1

            # close a position
            if self.position == 1:
                if IVX >= meanHV - self.CoverPara * std and IVX <= meanHV + self.CoverPara * std:
                    print("Please COVER!", self.Code)
                    self.sellStraddle()
                    #self.position == 0
            elif self.position == -1:
                if IVX >= meanHV - self.CoverPara * std and IVX <= meanHV + self.CoverPara * std:
                    print("Please COVER!", self.Code)
                    self.buyStraddle()
                    #self.position == 0
            #print ("Hist Volatility: ", hv)
            #print ("Standard of HV: ", hvstd)
        print " "


if __name__ == '__main__':
    myCode = "SR801C6800.CZC"
    myHVPeriod = 30
    myTotalTime = 365    # total period of HV
    myType = 1  # 1  2 
    myStdPara = 5.0/6   # (2/3, 1.5)
    myCoverPara = 2.0/3  #
    myPosition = 0  # -1:short 0:empty 1：long

    '''监控开始'''
    BSV = SugarBuySellVol(myCode, myPosition, myHVPeriod, myTotalTime, myType, myStdPara, myCoverPara)
    timeInterval = 1

    def delayrun():
        print 'Begin...'
    timer = tt.Timer(timeInterval, delayrun)
    timer.start()
    while True:
        t.sleep(5)   # frequency: 5 seconds
        BSV.Monitor()