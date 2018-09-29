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


w.start()
w.isconnected()

# per1,per2,per3,per4=1.16227245905,1.00754341006,0.986996744487,0.943550679017

class hisskew1(object):
    def calcuskew(self):
        end = datetime.today()
        begin = datetime(2017,3,31)
        #begin=end-timedelta(10)
        day2 = []
        for i in range((end - begin).days + 1):
            day = begin + timedelta(days=i)
            day2.append(day)
        hisSKEW = []
        for date in day2:
            close = 0
            OPC = optionchoose(close, date)
            option_year, option_month = OPC.option_name()
            closePrice = pd.DataFrame(w.wsd("M" + str(option_year)[-2:] + "0" + str(option_month) + ".DCE", "close", date, date,"TradingCalender=DCE").Data[0]).dropna()
            close = np.array(closePrice)
            if close == [[u'CWSDService: No data.']]:
                continue
            OPC = optionchoose(close, date)
            price = OPC.mround()
            at_call_Code = "M" + str(option_year)[-2:] + "0" + str(option_month) + "-C-" + str('{:.0f}'.format(price)) + '.DCE'
            out_call_Code = "M" + str(option_year)[-2:] + "0" + str(option_month) + "-C-" + str('{:.0f}'.format(price + 50)) + '.DCE'
            his_atIVX = pd.DataFrame(w.wsd(at_call_Code, "us_impliedvol", date, date, "TradingCalender=DCE").Data).dropna()
            his_outIVX = pd.DataFrame(w.wsd(out_call_Code, "us_impliedvol", date, date, "TradingCalender=DCE").Data).dropna()
            try:
                his_skew = his_outIVX / his_atIVX
                his_skew = his_skew.values[0][0]
            except:
                continue
            hisSKEW.append(his_skew)
        per11, per12, per13, per14 = np.percentile(hisSKEW, 90), np.percentile(hisSKEW, 60), np.percentile(hisSKEW,40), np.percentile(hisSKEW, 10)
        print("soybeanmealskew percentile")
        print([per11, per12, per13, per14])
        return per11, per12, per13, per14


class Soybeanmealskew(object):
    def __init__(self, atCode, outCode, position,per11, per12, per13, per14):
        self.atCode = atCode
        self.outCode = outCode
        self.position = position
        self.Underlying = 'M1801.DCE'
        self.per11 = per11
        self.per12 = per12
        self.per13 = per13
        self.per14 = per14

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
        print("SoyBeanmeal SKEW",self.atCode,self.outCode,datetime.now())
        try:
            atIVX = w.wsq(self.atCode, "rt_imp_volatility").Data[0][0]  # the real time ivx of wind
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
        if skewnow>self.per11 and self.position == 'flat':
            print('NOTICE! buy one'+str(self.atCode)+'，short two '+str(self.outCode))
        elif skewnow<self.per14 and self.position == 'flat':
            print('NOTICE! short one'+str(self.atCode)+'，buy two '+str(self.outCode))

        # close a position
        if skewnow<self.per12 and self.position == 'buy':
            print('COVER OPTIONS! short one'+str(self.atCode)+'，buy two'+str(self.outCode))
        elif skewnow>self.per13 and self.position == 'short':
            print('COVER OPTIONS! buy one'+str(self.atCode)+'，short two '+str(self.outCode))


class optionchoose(object):
    def __init__(self, a, date):
        self.a = a
        self.date = date

    def mround(self):
        b=int(self.a/50)*50
        if self.a-b<=25:
           price=b
        else:
           price=b+50
        return price

    def endday(self):
        firstday = datetime(self.date.year, self.date.month, 1)
        if firstday.isocalendar()[2]==6 :
            endday = 7
        elif firstday.isocalendar()[2]==7:
            endday = 6
        else:
            endday= 8
        return endday

    def option_name(self):
        option_year = self.date.year
        option_month = self.date.month
        option_day = self.date.day
        if option_month in [1, 2, 3]:
            option_month = 5
        elif option_month in [5, 6, 7]:
            option_month = 9
        elif option_month in [9, 10, 11]:
            option_month = 1
            option_year=option_year+1
        else:
            option_day = self.date.day
            if option_day < self.endday():
                if option_month == 4:
                    option_month = 5
                elif option_month == 8:
                    option_month = 9
                elif option_month == 12:
                    option_month = 1
                    option_year = option_year + 1
            else:
                if option_month == 4:
                    option_month = 9
                elif option_month == 8:
                    option_month = 1
                    option_year = option_year + 1
                elif option_month == 12:
                    option_month = 5
                    option_year = option_year + 1
        return option_year, option_month

w_wset_data=pd.DataFrame(w.wset('SectorConstituent',u'date=20171016;sector=豆粕期权').Data)
w_wset_data=w_wset_data.T

if __name__ == '__main__':
    etf = w.wsq("M1801.DCE", "rt_last")
    a = np.array(etf.Data[0])[0]
    OPC = optionchoose(m_price, date)
    price = OPC.mround()
    option_at_call = "豆粕期权M1801-C-" + str('{:.0f}'.format(mround(a)))
    option_at_put = "豆粕期权M1801-P-" + str('{:.0f}'.format(mround(a)))
    option_out_call = "豆粕期权M1801-C-" + str('{:.0f}'.format(mround(a) + 50))
    option_out_put = "豆粕期权M1801-P-" + str('{:.0f}'.format(mround(a) - 50))
    option_out2_call = "豆粕期权M1801-C-" + str('{:.0f}'.format(mround(a) + 100))
    option_out2_put = "豆粕期权M1801-C-" + str('{:.0f}'.format(mround(a) - 100))


    position = 'flat'  # flat long-short buy-sell
    '''监控开始'''
    timeInterval = 1
    def delayrun():
        print('Soybeanmeal Skew Begin...')

    timer = tt.Timer(timeInterval, delayrun)
    timer.start()
    while True:
        t.sleep(60)  # frequency: 5 seconds

        atCode = w_wset_data[w_wset_data[2] == option_at_call][1].values[0]
        outCode = w_wset_data[w_wset_data[2] == option_out_call][1].values[0]
        BSV_at_call = Soybeanmealoptionskew(atCode, outCode, position)
        BSV_at_call.Monitor()
