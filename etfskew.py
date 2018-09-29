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
import threading
import traceback as tb
import time
w.start()
w.isconnected()
# per1,per2,per3,per4=1.16227245905,1.00754341006,0.986996744487,0.943550679017

class hisskew():
    def calcuskew(self):
        end = datetime.today()
        begin = datetime(2015,2,11)
        #begin = end - timedelta(10)
        day2 = []
        for i in range((end - begin).days + 1):
            day = begin + timedelta(days=i)
            day2.append(day)
        hisSKEW = []
        for date in day2:
            closePrice = pd.DataFrame(w.wsd("510050.SH", "close", date, date, "TradingCalender=DCE").Data[0]).dropna()
            close = np.array(closePrice)
            if close == [[u'CWSDService: No data.']]:
                continue
            OPC3 = optionchoose3(close, date)
            option_year, option_month = OPC3.option_name()
            price = OPC3.mround()
            option_at_call = "50ETF购" + str(option_year) + "年" + str(option_month) + "月" + str('{:.2f}'.format(price))
            option_out_call = "50ETF购" + str(option_year) + "年" + str(option_month) + "月" + str('{:.2f}'.format(price + 0.05))
            w_etf_data = pd.DataFrame(w.wset('SectorConstituent', u'date=' + str(date) + ';sector=华夏上证50ETF期权').Data)
            w_etf_data = w_etf_data.T
            try:
                at_call_Code = w_etf_data[w_etf_data[2] == option_at_call][1].values[0]
                out_call_Code = w_etf_data[w_etf_data[2] == option_out_call][1].values[0]
            except IndexError:
                try:
                    option_at_call = "50ETF购" + str(option_month) + "月" + str('{:.2f}'.format(price))
                    at_call_Code = w_etf_data[w_etf_data[2] == option_at_call][1].values[0]
                    option_out_call = "50ETF购" + str(option_month) + "月" + str('{:.2f}'.format(price + 0.05))
                    out_call_Code = w_etf_data[w_etf_data[2] == option_out_call][1].values[0]
                except IndexError:
                    continue
            his_atIVX = pd.DataFrame(w.wsd(at_call_Code, "us_impliedvol", date, date, "TradingCalender=DCE").Data).dropna()
            his_outIVX = pd.DataFrame(w.wsd(out_call_Code, "us_impliedvol", date, date, "TradingCalender=DCE").Data).dropna()
            try:
                his_skew = his_outIVX / his_atIVX
                his_skew = his_skew.values[0][0]
            except:
                continue
            hisSKEW.append(his_skew)
        per1,per2,per3,per4=np.percentile(hisSKEW,90),np.percentile(hisSKEW,60),np.percentile(hisSKEW,40),np.percentile(hisSKEW,10)
        print("etfskew percentile")
        print([per1,per2,per3,per4])
        return per1,per2,per3,per4

class ETFoptionskew(object):
    def __init__(self, atCode, outCode, position,per1,per2,per3,per4):
        self.atCode = atCode
        self.outCode = outCode
        self.position = position
        self.Underlying = '510050.SH'
        self.per1=per1
        self.per2=per2
        self.per3=per3
        self.per4=per4

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
        print ("ETFskew",self.atCode,self.outCode,datetime.now())
        try:
            atIVX = w.wsq(self.atCode, "rt_imp_volatility").Data[0][0]   # the real time ivx of wind
            outIVX = w.wsq(self.outCode, "rt_imp_volatility").Data[0][0]   # the real time ivx of wind
        except IndexError:
            pass
        if atIVX !=0:
            skewnow=outIVX/atIVX
        else:
            return
        if self.Expire():
            return


        # open a position
        if skewnow>self.per1 and self.position == 'flat':
            print('NOTICE! buy one'+str(self.atCode)+'，short two '+str(self.outCode))
            #self.position = 'buy'
        elif skewnow<self.per4 and self.position == 'flat':
            print('NOTICE! short one'+str(self.atCode)+'，buy two '+str(self.outCode))
            #self.position = 'short'

        # close a position
        if skewnow<self.per2 and self.position == 'buy':
            print('COVER OPTIONS! short one'+str(self.atCode)+'，buy two'+str(self.outCode))
            #self.position = 'flat'
        elif skewnow>self.per3 and self.position == 'short':
            print('COVER OPTIONS! buy one'+str(self.atCode)+'，short two '+str(self.outCode))
            #self.position = 'flat'

class optionchoose3(object):
    def __init__(self, a, date):
        self.a = a
        self.date = date

    def mround(self):
        b=float(int(self.a*10))/10+0.05
        if (self.a-b<0 and abs(self.a-b)<0.025) or (self.a-b>0 and abs(self.a-b)<0.025):
            price=b
        elif (self.a-b)<0 and abs(self.a-b)>0.025:
            price=b-0.05
        else:
        	price=b+0.05
        return price

    def weekdb(self):
    	firstday = datetime(self.date.year,self.date.month,1)
    	num = self.date.day-1+firstday.isocalendar()[2]-3
    	if firstday.isocalendar()[2]>3:
    		n=num/7
    	else:
    		n=num/7+1
    	return n

    def option_name(self):
        if self.weekdb()<4:
            option_month=self.date.month
            option_year=self.date.year
        else:
            if self.date.month<12:
                option_month=self.date.month+1
                option_year=self.date.year
            else:
                option_month=1
                option_year=self.date.year+1
        return option_year,option_month



w_wset_data=pd.DataFrame(w.wset('SectorConstituent',u'date=20170901;sector=华夏上证50ETF期权').Data)
w_wset_data=w_wset_data.T

if __name__ == '__main__':
    etf = w.wsq("510050.SH", "rt_last")
    a = np.array(etf.Data[0])[0]
    date = datetime.today()
    OPC = optionchoose3(etf_price, date)
    option_year, option_month = OPC.option_name()
    price = OPC.mround()
    option_at_call="50ETF购"+str(option_month)+"月"+str('{:.2f}'.format(mround(a)))
    option_at_put="50ETF沽"+str(option_month)+"月"+str('{:.2f}'.format(mround(a)))
    option_out_call="50ETF购"+str(option_month)+"月"+str('{:.2f}'.format(mround(a)+0.05))
    option_out_put="50ETF沽"+str(option_month)+"月"+str('{:.2f}'.format(mround(a)-0.05))
    option_out2_call="50ETF购"+str(option_month)+"月"+str('{:.2f}'.format(mround(a)+0.1))
    option_out2_put="50ETF沽"+str(option_month)+"月"+str('{:.2f}'.format(mround(a)-0.1))
    position = 'flat'  # flat long-short buy-sell
    '''监控开始'''
    timeInterval = 1
    def delayrun():
        print('ETF Skew Begin...')

    def bsv_option(option_at_call, option_at_put, option_out_call, option_out_put, option_out2_call, option_out2_put):
        atCode = w_wset_data[w_wset_data[2] == option_at_call][1].values[0]
        outCode = w_wset_data[w_wset_data[2] == option_out_call][1].values[0]
        BSV_at_call = ETFoptionskew(atCode, outCode, position)
        BSV_at_call.Monitor()

        atCode = w_wset_data[w_wset_data[2] == option_out_call][1].values[0]
        outCode = w_wset_data[w_wset_data[2] == option_out2_call][1].values[0]
        BSV_out_call = ETFoptionskew(atCode, outCode, position)
        BSV_out_call.Monitor()

        atCode = w_wset_data[w_wset_data[2] == option_at_put][1].values[0]
        outCode = w_wset_data[w_wset_data[2] == option_out_put][1].values[0]
        BSV_at_put = ETFoptionskew(atCode, outCode, position)
        BSV_at_put.Monitor()

        atCode = w_wset_data[w_wset_data[2] == option_out_put][1].values[0]
        outCode = w_wset_data[w_wset_data[2] == option_out2_put][1].values[0]
        BSV_out_put = ETFoptionskew(atCode, outCode, position)
        BSV_out_put.Monitor()
        return

    t = threading.Timer(timeInterval, delayrun)
    t.start()
    while True:
        time.sleep(5)  # frequency: 5 seconds
        bsv_option(option_at_call, option_at_put, option_out_call, option_out_put, option_out2_call, option_out2_put)





