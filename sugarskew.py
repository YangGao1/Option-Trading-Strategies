# -*- coding: utf-8 -*-
"""

@version: 0.0.1
"""
from __future__ import print_function, division
import numpy as np
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
from datetime import *
from WindPy import w
import pandas as pd
import threading as tt
import traceback as tb
import time as t
import calendar
w.start()
w.isconnected()

# per1,per2,per3,per4=1.16227245905,1.00754341006,0.986996744487,0.943550679017
class hisskew2(object):
    def calcuskew(self):
        end = datetime.today()
        begin = datetime(2017,4,19)
        #begin=end-timedelta(10)
        day2 = []
        for i in range((end - begin).days + 1):
            day = begin + timedelta(days=i)
            day2.append(day)
        hisSKEW = []
        for date in day2:
            close = 0
            OPC2 = optionchoose2(close, date)
            option_year, option_month = OPC2.option_name()
            closePrice = pd.DataFrame(w.wsd("SR" + str(option_year)[-1:] + "0" + str(option_month) + ".CZC", "close", date, date,"TradingCalender=DCE").Data[0]).dropna()
            close = np.array(closePrice)
            if close == [[u'CWSDService: No data.']]:
                continue
            OPC2 = optionchoose2(close, date)
            price = OPC2.mround()
            at_call_Code = "SR" + str(option_year)[-1:] + "0" + str(option_month) + "C" + str('{:.0f}'.format(price)) + '.CZC'
            out_call_Code = "SR" + str(option_year)[-1:] + "0" + str(option_month) + "C" + str('{:.0f}'.format(price + 100)) + '.CZC'
            his_atIVX = pd.DataFrame(w.wsd(at_call_Code, "us_impliedvol", date, date, "TradingCalender=DCE").Data).dropna()
            his_outIVX = pd.DataFrame(w.wsd(out_call_Code, "us_impliedvol", date, date, "TradingCalender=DCE").Data).dropna()
            try:
                his_skew = his_outIVX / his_atIVX
                his_skew = his_skew.values[0][0]
            except:
                continue
            hisSKEW.append(his_skew)
        per21, per22, per23, per24 = np.percentile(hisSKEW, 90), np.percentile(hisSKEW, 60), np.percentile(hisSKEW,40), np.percentile(hisSKEW, 10)
        print("sugarskew percentile")
        print([per21, per22, per23, per24])
        return per21,per22,per23,per24


class Sugarskew(object):
    def __init__(self, atCode, outCode, position,per21,per22,per23,per24):
        self.atCode = atCode
        self.outCode = outCode
        self.position = position
        self.Underlying = "SR801.CZC"
        self.per21 = per21
        self.per22 = per22
        self.per23 = per23
        self.per24 = per24

    def Expire(self):
        today = date.today()
        tommorrow = today + timedelta(days=1)
        expire = w.wsd(self.atCode, "exe_enddate", "ED0TD", today, "TradingCalender=DCE").Data[0][0]
        if self.position == 'flat':
            return False
        elif expire == tommorrow:
            string = "Option will expire tommorrow!"
            print(string +"Please COVER "+str(self.atCode)+'and'+str(self.outCode))
            return True
        else:
            return False

    def Monitor(self):
        print("Sugar SKEW",self.atCode,self.outCode,datetime.now())
        try:
            atIVX = w.wsq(self.atCode, "rt_imp_volatility").Data[0][0]
        # the real time ivx of wind
            outIVX = w.wsq(self.outCode, "rt_imp_volatility").Data[0][0]   # the real time ivx of wind
        except IndexError:
            pass
        if atIVX !=0:
            skewnow=outIVX/atIVX
        else:
            return
        if self.Expire():
            return

        print ("skew: ", skewnow)

        # open a position
        if skewnow>self.per21 and self.position == 'flat':
            print('NOTICE! buy one'+str(self.atCode)+'，short two '+str(self.outCode))
        elif skewnow<self.per24 and self.position == 'flat':
            print('NOTICE! short one'+str(self.atCode)+'，buy two '+str(self.outCode))

        # close a position
        if skewnow<self.per22 and self.position == 'buy':
            print('COVER OPTIONS! short one'+str(self.atCode)+'，buy two'+str(self.outCode))
        elif skewnow>self.per23 and self.position == 'short':
            print('COVER OPTIONS! buy one'+str(self.atCode)+'，short two '+str(self.outCode))

class optionchoose2(object):
    def __init__(self, a, date):
        self.a = a
        self.date = date

    def mround(self):
        b=int(self.a/100)*100
        if self.a-b<=50:
           price=b
        else:
           price=b+100
        return price

    def endday(self):
        monthRange = calendar.monthrange(self.date.year, self.date.month)[1]
        lastday = datetime(self.date.year, self.date.month, monthRange)
        if lastday.isocalendar()[2] == 5:
            endday = monthRange - 4
        if lastday.isocalendar()[2] == 6:
            endday = monthRange - 5
        else:
            endday = monthRange - 6

    def option_name(self):
        option_year = self.date.year
        option_month = self.date.month
        if option_month==12:
            option_month = 5
            option_year = option_year + 1
        if option_month in [1,2]:
            option_month = 5
        elif option_month in [4,5,6]:
            option_month = 9
        elif option_month in [8,9,10]:
            option_month = 1
            option_year=option_year+1
        else:
            option_day=self.date.day
            if option_day< self.endday():
                if option_month == 3:
                    option_month = 5
                if option_month == 7:
                    option_month = 9
                if option_month == 11:
                    option_month = 1
                    option_year = option_year + 1
            else:
                if option_month == 3:
                    option_month = 9
                if option_month == 7:
                    option_month = 1
                    option_year = option_year + 1
                if option_month == 11:
                    option_month = 5
                    option_year = option_year + 1
        return option_year, option_month

w_wset_data=pd.DataFrame(w.wset('SectorConstituent',u'date=20171009;sector=白糖期权').Data)
w_wset_data=w_wset_data.T

if __name__ == '__main__':
    etf = w.wsq("SR801.CZC", "rt_last")
    a = np.array(etf.Data[0])[0]
    OPC2 = optionchoose2(a, date)
    price = OPC2.mround()
    option_at_call = "" + str(format(price))
    option_at_put = "" + str(format(price))
    option_out_call = "" + str(format(price + 100))
    option_out_put = "" + str(format(price - 100))
    option_out2_call = "" + str(format(price + 200))
    option_out2_put = "" + str(format(price - 200))


    position = 'flat'  # flat long-short buy-sell
    '''监控开始'''
    timeInterval = 1
    def delayrun():
        print('SugarSkew Begin...')

    timer = tt.Timer(timeInterval, delayrun)
    timer.start()
    while True:
        t.sleep(60)  # frequency: 5 seconds
        atCode = w_wset_data[w_wset_data[2] == option_at_call][1].values[0]
        outCode = w_wset_data[w_wset_data[2] == option_out_call][1].values[0]
        BSV_at_call = Sugarskew(atCode, outCode, position)
        BSV_at_call.Monitor()

