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
warnings.filterwarnings('ignore')
w.start()
w.isconnected()

today1 = str(filter(str.isdigit, str(date.today())))
w_etf_data = pd.DataFrame(w.wset('SectorConstituent', u'date=' + today1 + ';sector=华夏上证50ETF期权').Data)
w_etf_data = w_etf_data.T

def term_option(option_month3):
    m1 = option_month3
    m_list = {"1": (2, 3, 6), "2": (3, 6, 9), "3": (4, 6, 9), "4": (5, 6, 9), "5": (6, 9, 12), "6": (7, 9, 12),
              "7": (8, 9, 12), "8": (9, 12, 3), "9": (10, 12, 3), "10": (11, 12, 3), "11": (12, 3, 6), "12": (1, 3, 6)}
    (m2, m3, m4) = m_list.get(str(m1))
    option_call1, option_call2, option_call3, option_call4 = "50ETF购" + str(m1) + "月" + str('{:.2f}'.format(price3)), "50ETF购" + str(m2) + "月" + str('{:.2f}'.format(price3)), "50ETF购" + str(m3) + "月" + str('{:.2f}'.format(price3)), "50ETF购" + str(m4) + "月" + str('{:.2f}'.format(price3))
    myCode1, myCode2, myCode3, myCode4 = w_etf_data[w_etf_data[2] == option_call1][1].values[0], w_etf_data[w_etf_data[2] == option_call2][1].values[0], w_etf_data[w_etf_data[2] == option_call3][1].values[0], w_etf_data[w_etf_data[2] == option_call4][1].values[0]
    return myCode1, myCode2, myCode3, myCode4


def main(option_year1, option_month1,price1,option_year2, option_month2,price2, option_month3,price3):
# soybeanmeal
    ##### BuySellVol #####
    Code1 = "M" + str(option_year1)[-2:] + "0" + str(option_month1) + "-C-" + str(price1)+ ".DCE"
    HVPeriod1 = 30
    TotalTime1 = 365  # total period of HV
    Type1 = 2  # 1  2
    StdPara1 = 5.0 / 6  # (2/3, 1.5)
    CoverPara1 = 2.0 / 3  #
    Position_soyBSV = 0  #
    SoyBeanmealBSV = SoybeanmealBuySellVol(Code1, Position_soyBSV, HVPeriod1, TotalTime1, Type1, StdPara1, CoverPara1)

    #### Risk Reversal #####
    CallCode1 = "M" + str(option_year1)[-2:] + "0" + str(option_month1) + "-C-" + str(price1)+ ".DCE"
    PutCode1 = "M" + str(option_year1)[-2:] + "0" + str(option_month1) + "-P-" + str(price1)+ ".DCE"
    Period1 = 30
    Bollinger1 = False
    aStd1 = 3  # (1.5, 3)
    Position_soyRR = 0  # -1:short 0:empty 1：long
    SoyBeanmealRR = SoybeanmealRiskReversal(CallCode1, PutCode1, Position_soyRR, Period1, aStd1, Bollinger1)

    ##### skew #####
    at_call_Code1 = "M" + str(option_year1)[-2:] + "0" + str(option_month1) + "-C-" + str(price1)+ ".DCE"
    out_call_Code1 = "M" + str(option_year1)[-2:] + "0" + str(option_month1) + "-C-" + str(price1+50)+ ".DCE"
    out2_call_Code1 = "M" + str(option_year1)[-2:] + "0" + str(option_month1) + "-C-" + str(price1+100)+ ".DCE"
    HS = hisskew1()
    #per11, per12, per13, per14= HS.calcuskew()
    per11, per12, per13, per14=1.0144358771171262, 1.0012391007209027, 0.99615900654962253, 0.98272494892270823
    position_soySKEW = 'flat'  # flat buy-sell
    BSV_at_call1 = Soybeanmealskew(at_call_Code1, out_call_Code1, position_soySKEW,per11, per12, per13, per14)

#sugar
    ##### BuySellVol #####
    Code2 = "SR" + str(option_year2)[-1:] + "0" + str(option_month2) + "C" + str(price2) + ".CZC"
    HVPeriod2 = 30
    TotalTime2 = 365  # total period of HV
    Type2 = 2  # 1  2
    StdPara2 = 5.0 / 6  # (2/3, 1.5)
    CoverPara2 = 2.0 / 3  #
    Position_sugarBSV = 0  #
    SugarBSV = SugarBuySellVol(Code2, Position_sugarBSV, HVPeriod2, TotalTime2, Type2, StdPara2, CoverPara2)

    #### Risk Reversal #####
    CallCode2 = "SR" + str(option_year2)[-1:] + "0" + str(option_month2) + "C" + str(price2) + ".CZC"
    PutCode2 = "SR" + str(option_year2)[-1:] + "0" + str(option_month2) + "P" + str(price2) + ".CZC"
    Period2 = 30
    Bollinger2 = False
    aStd2 = 3  # (1.5, 3)
    Position_sugarRR = 0  # -1:short 0:empty 1：long
    SugarRR = SugarRiskReversal(CallCode2, PutCode2, Position_sugarRR, Period2, aStd2, Bollinger2)

    ##### skew #####
    at_call_Code2 = "SR" + str(option_year2)[-1:] + "0" + str(option_month2) + "C" + str(price2) + ".CZC"
    out_call_Code2 = "SR" + str(option_year2)[-1:] + "0" + str(option_month2) + "C" + str(price2 + 100) + ".CZC"
    HS = hisskew2()
    #per21, per22, per23, per24 = HS.calcuskew()
    per21, per22, per23, per24 =1.0242826607030691, 1.0021983077587877, 0.99407156245866335, 0.97084377269530364
    position_sugarSKEW = 'flat'  # flat buy-sell
    BSV_at_call2 = Sugarskew(at_call_Code2, out_call_Code2, position_sugarSKEW,per21, per22, per23, per24)

#50etf
    option_at_call3 = "50ETF购" + str(option_month3) + "月" + str('{:.2f}'.format(price3))
    option_at_put3 = "50ETF沽" + str(option_month3) + "月" + str('{:.2f}'.format(price3))
    try:
        at_call_Code3 = w_etf_data[w_etf_data[2] == option_at_call3][1].values[0]
        at_put_Code3 = w_etf_data[w_etf_data[2] == option_at_put3][1].values[0]
    except:
        pass

    ##### BuySellVol #####
    threshold_type3 = 2  # 1  2
    open_a3 = 1.35
    open_b3 = 2
    close_a3 = 1
    close_b3 = 0.0001
    position_etfBSV = 'flat'  # flat buy short
    option_type3 = 'call+put'  # call put call+put
    para_list3 = [open_a3, open_b3, close_a3, close_b3]
    ETFBSV = ETFBuySellVol(at_call_Code3, at_put_Code3, position_etfBSV, threshold_type3, para_list3, option_type3)

    #### Risk Reversal #####
    my_mean_period = 20
    my_para_a = 1  # open parameter: 1.5 ~ 3.0
    my_para_b = 0.3  # close parameter: 0 ~ 1.0
    position_etfRR = 'flat'  # flat buy short

    # Bollinger Band: mean_period = 20 & para_a = 2.0
    ETFRR = ETFRiskReversal(at_call_Code3, at_put_Code3, position_etfRR, my_mean_period, my_para_a, my_para_b)

    ##### Term Structure #####
    my_term_period = 1     # 期限结构计算的回顾样本数量, trading day
    my_mean_period = 20  # 均值计算的回顾样本数量, trading day
    my_num_type = 2  # num类型: 1, 2, 3
    my_num = 2  # 1.5-2.5  1-2 basis point  4%-8% current vol
    my_cl = 0.5  # close parameter
    my_para_list = [my_mean_period, my_num_type, my_num, my_cl]
    myPosition = 'flat'  # flat buy short
    myCode1, myCode2, myCode3, myCode4 = term_option(option_month3)
    ETFTS = ETFTermStructure(myCode1, myCode2, myCode3, myCode4, my_para_list, myPosition)

    ##### ETFskew #####
    option_at_call3="50ETF购"+str(option_month3)+"月"+str('{:.2f}'.format(price3))
    option_at_put3="50ETF沽"+str(option_month3)+"月"+str('{:.2f}'.format(price3))
    option_out_call3="50ETF购"+str(option_month3)+"月"+str('{:.2f}'.format(price3+0.05))
    option_out_put3="50ETF沽"+str(option_month3)+"月"+str('{:.2f}'.format(price3-0.05))
    at_call_Code3 = w_etf_data[w_etf_data[2] == option_at_call3][1].values[0]
    at_put_Code3 = w_etf_data[w_etf_data[2] == option_at_put3][1].values[0]
    out_call_Code3 = w_etf_data[w_etf_data[2] == option_out_call3][1].values[0]
    out_put_Code3 = w_etf_data[w_etf_data[2] == option_out_put3][1].values[0]
    #per1, per2, per3, per4 = hisskew().calcuskew()
    per1, per2, per3, per4 =1.3299239120086517, 1.0986293232658269, 1.0640195706382001, 1.0060487445266135
    position_etfSKEW = 'flat'  # flat buy short
    BSV_at_call3 = ETFoptionskew(at_call_Code3, out_call_Code3, position_etfSKEW,per1, per2, per3, per4)
    '''监控开始'''
    timeInterval = 1
    timer = tt.Timer(timeInterval, delayrun)
    timer.start()
    while True:
        t.sleep(10)  # frequency: 2 min
        print "==============================="
        print "==== SoyBeanmeal ===="
        SoyBeanmealBSV.Monitor()
        SoyBeanmealRR.Monitor()
        BSV_at_call1.Monitor()
        print "==============================="
        print "==== Sugar ===="
        SugarBSV.Monitor()
        SugarRR.Monitor()
        BSV_at_call2.Monitor()
        print "==============================="
        print "==== 50ETF ===="
        ETFBSV.Monitor()
        ETFRR.Monitor()
        ETFTS.Monitor()
        BSV_at_call3.Monitor()

def delayrun():
    print 'Begin...'
if __name__ == '__main__':
    date = datetime.today()
    OPC1 = optionchoose1(0, date)
    option_year1, option_month1 = OPC1.option_name()
    m1 = w.wsq("M" + str(option_year1)[-2:] + "0" + str(option_month1) + ".DCE", "rt_last")
    m_price1 = np.array(m1.Data[0])[0]
    OPC1 = optionchoose1(m_price1, date)
    option_year1, option_month1 = OPC1.option_name()
    price1 = OPC1.mround()
    OPC2 = optionchoose2(0, date)
    option_year2, option_month2 = OPC2.option_name()
    m2 = w.wsq("SR" + str(option_year2)[-1:] + "0" + str(option_month2) + ".CZC", "rt_last")
    m_price2 = np.array(m2.Data[0])[0]
    OPC2 = optionchoose2(m_price2, date)
    price2 = OPC2.mround()
    option_year2, option_month2 = OPC2.option_name()
    date = datetime.today()
    etf = w.wsq("510050.SH", "rt_last")
    etf_price = np.array(etf.Data[0])[0]
    OPC3 = optionchoose3(etf_price, date)
    option_year3, option_month3 = OPC3.option_name()
    price3 = OPC3.mround()
    main(option_year1, option_month1, price1, option_year2, option_month2, price2, option_month3, price3)