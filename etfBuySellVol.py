#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Buy/Sell Volatility
###################
###### 50ETF ######
###################

from __future__ import print_function, division
import numpy as np
import pandas as pd
import threading as tt
import traceback as tb
import time as t
from WindPy import *
from datetime import *
w.start()
w.isconnected()


class ETFBuySellVol(object):
    def __init__(self, callCode, putCode, position, Type, para_list, optionType):
        self.callCode = callCode
        self.putCode = putCode
        self.position = position
        self.Type = Type
        self.paraList = para_list
        self.Underlying = '510050.SH'
        self.optionType = optionType

        [self.open_a, self.open_b, self.close_a, self.close_b] = self.paraList

    def CalcuVol(self):
        today = date.today()
        yesterday = "-1D"
        # startDay = "2017-03-31"
        strPeriod = "-252D"
        # t = w.wsd(self.callCode, "close", strPeriod, yesterday, "TradingCalender=DCE").Data
        try:
            closePrice = pd.DataFrame(w.wsd(self.Underlying, "close", strPeriod, yesterday, "TradingCalender=DCE").Data[0]).dropna()
            preClosePrice = pd.DataFrame(w.wsd(self.Underlying, "pre_close", strPeriod, yesterday, "TradingCalender=DCE").Data[0]).dropna()
            dailyReturn = closePrice/preClosePrice
            logReturn = np.log(dailyReturn.dropna())
        #logReturn = pd.DataFrame(np.log(dailyReturn.dropna()))
            HV = (pd.rolling_std(logReturn, window=20) * np.sqrt(252.0)).dropna()
        #HV =  logReturn.rolling(window=20,center=False).std()* np.sqrt(252.0)).dropna()
            meanHV = HV[0].mean()
            stdHV = HV[0].std()
            return meanHV, stdHV
        except TypeError:
            pass

    def buyStraddle(self):
        string = "NOTICE! Buy "+self.callCode+", and "+self.putCode
        print(string)

    def sellStraddle(self):
        string = "NOTICE! Sell "+self.callCode+", and "+self.putCode
        print(string)

    def Protection(self):
        pass

    def Expire(self):
        today = date.today()
        tommorrow = today + timedelta(days=1)
        expire = w.wsd(self.callCode, "exe_enddate", "ED0TD", today, "TradingCalender=DCE").Data[0][0]
        # expire = "2017-05-08"
        if self.position == 'flat':
            return False
        elif expire == tommorrow:
            string = "Option will expire tommorrow! "
            print("ETFBuySellVol！Please COVER!"+string, callCode , putCode)
            return True
        else:
            return False

    def Hedge(self):
        [callDelta],[Gamma],[Vega],[callTheta],[callRho] = w.wsq(self.callCode,"rt_delta,rt_gamma,rt_vega,rt_theta,rt_rho").Data
        [putDelta],[putTheta],[putRho] = w.wsq(self.putCode,"rt_delta,rt_theta,rt_rho").Data
        print("callDelta: ", callDelta)
        print("putDelta", putDelta)
        print("Gamma: ", Gamma)
        print("Vega: ", Vega)
        print("callTheta: ", callTheta)
        print("putTheta: ", putTheta)
        print("callRho: ", callRho)
        print("putRho", putRho)

    def Monitor(self):
        # currentPrice = w.wsq(self.callCode, "rt_latest").Data[0][0]
        # callVO = VanillaOption(spot=2789.0, strike=2800.0, maturity=4.0 / 12, rate=rate, vol=0.12, optionType='Call')
        # s = w.wsq(self.callCode, "rt_imp_volatility")
        callIVX = w.wsq(self.callCode, "rt_imp_volatility").Data[0][0]   # the real time ivx of wind
        putIVX = w.wsq(self.putCode, "rt_imp_volatility").Data[0][0]   # the real time ivx of wind
        if self.optionType == 'call':
            ivx = float(callIVX)
        elif self.optionType == 'put':
            ivx = float(putIVX)
        elif self.optionType =='call+put':
            ivx = (float(callIVX) + float(putIVX)) / 2.0
        else:
            raise ValueError('error: optionType')

        hv, hvstd = self.CalcuVol()
        if self.Expire():
            return

        print('ETFBuySellVol', self.callCode, self.putCode, datetime.now())
        print ("Implied Volatility: ", ivx)
        print("Realized Volatility:", hv)

        if self.Type == 1:
            _open_a = max(float(self.open_a), 1.0 / self.open_a)
            _close_a = max(float(self.close_a), 1.0 / self.close_a)

            # open position
            if ivx > _open_a * hv and self.position == 'flat':
                self.sellStraddle()
                #self.position = 'short'
                self.Hedge()
            elif ivx < 1.0 / _open_a * hv and self.position == 'flat':
                self.buyStraddle()
                #self.position = 'buy'
                self.Hedge()

            # close a position
            if (1.0 / _close_a) * hv < ivx < _close_a * hv:
                if self.position == 'buy':
                    print('ETFBuySellVol平仓！',callCode , putCode)
                    self.sellStraddle()
                    #self.position = 'flat'
                    self.Hedge()
                elif self.position == 'short':
                    print('ETFBuySellVol平仓！',callCode , putCode)
                    self.buyStraddle()
                    #self.position = 'flat'
                    self.Hedge()


        if self.Type == 2:
            _open_b = abs(float(self.open_b))
            _close_b = abs(float(self.close_b))

            # open a position
            if ivx > hv + _open_b * hvstd and self.position == 'flat':
                self.sellStraddle()
                self.Hedge()
                #self.position = 'short'
            elif ivx < hv - _open_b * hvstd and self.position == 'flat':
                self.buyStraddle()
                self.Hedge()
                #self.position = 'buy'

            # close a position
            if hv - _close_b * hvstd < ivx < hv + _close_b * hvstd:
                if self.position == 'buy':
                    print('ETFBuySellVol平仓！',callCode , putCode)
                    self.sellStraddle()
                    self.Hedge()
                    #self.position = 'flat'
                elif self.position == 'short':
                    print('ETFBuySellVol平仓！', callCode , putCode)
                    self.buyStraddle()
                    self.Hedge()
                    #self.position = 'flat'

            #print ("Hist Volatility: ", hv)
            #print ("Standard of HV: ", hvstd)

        print (" ")


if __name__ == '__main__':
    myCallCode = '10000871.SH'  # 1705 CALL 2.35
    myPutCode = '10000876.SH'
    threshold_type = 1  # 1  2
    open_a = 1.35
    open_b = 2
    close_a = 1
    close_b = 0.0001
    myPosition = 'flat'  # flat long-short buy-sell 
    option_type = 'call+put'   # call put call+put

    para_list = [open_a, open_b, close_a, close_b]

    '''监控开始'''
    BSV = ETFBuySellVol(myCallCode, myPutCode, myPosition, threshold_type, para_list, option_type)
    timeInterval = 1

    def delayrun():
        print ('ETF Buy and Sell Vol Begin...')
    timer = tt.Timer(timeInterval, delayrun)
    timer.start()
    while True:
        t.sleep(5)   # frequency: 5 seconds
        BSV.Monitor()
