# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 15:02:09 2017
一月交易一次版本
@author: LENOVO
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
import datetime

import sys
import importlib
importlib.reload(sys)
reload(sys)
sys.setdefaultencoding('utf8')
from time import time
start = time()
db_file_path = 'E:/skew/skew/mydatabase5.db'    # SQLite数据库名称，路径为当前目录
conn = sqlite3.connect(db_file_path)

lastdate='SELECT * FROM "ETF_option_lasttradingdate"'
lastdate=pd.read_sql(lastdate,conn)

lastdate=pd.read_excel("E:/skew/skew/50etf8_28.xlsx","ETF_option_lasttradingdate")
etf_close=pd.read_excel("E:/skew/skew/50etf8_28.xlsx","close")
etf_imvol=pd.read_excel("E:/skew/skew/50etf8_28.xlsx","imvol")
etf_option_name=pd.read_excel("E:/skew/skew/50etf8_28.xlsx","option_name")

fee = 5.0
slippage = 5.0
capital = 20000.0
size=1
option_value=0
remain_money=capital
total_money = [remain_money]
trade_option = pd.DataFrame()

(up_buy,up_sell,down_sell,down_buy)=(90,60,40,10) #上下界
option_type = "out"# at/out，at为平值期权和虚值1期权，out为虚值1与虚值2期权
_type="call" #call/out
befexp="T" #是否在到期日前d天内不交易
d=7

#boundary


def skew_ivx(date,at_name,out_name):
    if at_name in etf_imvol.columns and out_name in etf_imvol.columns:
        at_imvol = etf_imvol[etf_imvol.Date==date][at_name].values[0].tolist() 
        out_imvol = etf_imvol[etf_imvol.Date==date][out_name].values[0].tolist()
        if at_imvol !=0:
            skeww = out_imvol/at_imvol
        else:
            skeww="False"
    else:
        skeww="False"
    return skeww

def add_open(num,at_name,out_name):
    "正在开仓中的合约"
    global trade_option,size
    if trade_option.empty:
        t = pd.Series([at_name,out_name,num], index=["at","out","size"])
        trade_option = trade_option.append(t, ignore_index=True)
    else:        
        if at_name not in trade_option['at'].values:
            t = pd.Series([at_name,out_name,num], index=["at","out","size"])
            trade_option = trade_option.append(t, ignore_index=True)
    return trade_option

def Calendar_Spread(posit,date,at_name,out_name):#资金处理
    global size,trade_option
    at_close = etf_close[etf_close.Date==date][at_name].values[0].tolist() 
    out_close = etf_close[etf_close.Date==date][out_name].values[0].tolist()     
    if posit=="buy": #买平值卖虚值
        num=size
        add_open(num,at_name,out_name)
        print str(date) + 'buy: '+str(at_name)+' and sell'+str(out_name)
        money_chg=-10000.0*num*at_close+20000.0*num*out_close
    elif posit=="sell":#买虚值卖平值
        num=-size
        add_open(num,at_name,out_name)
        print str(date) + 'sell: '+str(at_name)+' and buy'+str(out_name)
        money_chg=-10000.0*num*at_close+20000.0*num*out_close 
    elif posit=="close buy":
        num=trade_option[trade_option['at'] ==at_name]['size'].values[0].tolist()      
        trade_option=trade_option[trade_option['at']!=at_name]      
        print str(date) + 'close buy: '+str(at_name)+' and sell'+str(out_name)
        money_chg=10000.0*num*at_close-20000.0*num*out_close
    elif posit=="close sell":
        num=trade_option[trade_option['at'] ==at_name]['size'].values[0].tolist() 
        trade_option=trade_option[trade_option['at']!=at_name]   
        print str(date) + 'close sell: '+str(at_name)+' and buy'+str(out_name)
        money_chg=10000.0*num*at_close-20000.0*num*out_close

    return money_chg - 3 * size * fee - 3 * size * slippage / 2.0
  
if option_type == "out" and _type=="call":
    a_name,o_name='out_call','out2_call'
elif option_type == "out" and _type=="put":
    a_name,o_name='out_put','out2_put'
elif option_type == "at" and _type=="call":
    a_name,o_name='at_call','out_call'
elif option_type == "at" and _type=="put":
    a_name,o_name='at_put','out_put'
else:
    print "_type error" 

def handle_ivx(date,_type,per1,per2,per3,per4): #下单信号； type=call/put
    global remain_money,a_name,o_name
    
    at_name=etf_option_name[etf_option_name.date==date][a_name].values[0]
    out_name=etf_option_name[etf_option_name.date==date][o_name].values[0]

 # open position       
    skew=skew_ivx(date,at_name,out_name)
    if at_name not in lastdate.symbol.values and _type=="call":
        at_name=at_name[:-4]+str(float(at_name[-4:])+0.05)+"0"
    elif at_name not in lastdate.symbol.values and _type=="put":
        at_name=at_name[:-4]+str(float(at_name[-4:])-0.05)+"0"
    expireday=lastdate[lastdate.symbol==at_name]['lasttradingdate'].values[0]
    if befexp=="T" and (expireday-datetime.datetime.strptime(date,'%Y-%m-%d')).days<d:
        change=0
    else:        
	    if trade_option.empty and skew!="False":
	        if skew > per1:
	            posit ="buy"  # buy atm option,sell otm option
	            change=Calendar_Spread(posit,date,at_name,out_name)
	        elif skew < per4:
	            posit ="sell" # sell atm option,buy otm option
	            change=Calendar_Spread(posit,date,at_name,out_name)
	        else:
	            change=0
	    else:
	        change=0

# close position
    option_value=0 #持仓价值
    if trade_option.empty == False:        
        for at_name in trade_option['at']:
            out_name=trade_option[trade_option['at']==at_name]["out"].values[0]
            skew=skew_ivx(date,at_name,out_name)
            num=trade_option[trade_option['at']==at_name]["size"].values.tolist()[0]
            at_close = etf_close[etf_close.Date==date][at_name].values[0].tolist()  
            out_close = etf_close[etf_close.Date==date][out_name].values[0].tolist()   
            if num>0 and ((skew!="False" and skew < per2)  or expire(at_name,date)=="T"):
                posit ="close buy"
                change=Calendar_Spread(posit,date,at_name,out_name)
            elif num<0 and((skew!="False" and skew > per3)   or expire(at_name,date)=="T"):
                posit ="close sell"
                change=Calendar_Spread(posit,date,at_name,out_name)
            else:
                option_value=option_value+10000.0*num*at_close-20000.0*num*out_close
                change=0
    else:
        change=0
        
    remain_money += change
    total_money.append(remain_money + option_value)

def expire(at_name,date):
    if date in lastdate.lasttradingdate.values and (at_name in lastdate[lastdate.lasttradingdate==date]['symbol'].values):
        expireTF="T"
    else:
        expireTF="F"
    return expireTF

a=[]
for date in etf_option_name.date.values: #date为datetime
    date=pd.to_datetime(str(date)).strftime('%Y-%m-%d')
    at_name=etf_option_name[etf_option_name.date==date][a_name].values[0]
    out_name=etf_option_name[etf_option_name.date==date][o_name].values[0]   
    if at_name in etf_imvol.columns and out_name in etf_imvol.columns:
        at_imvol = etf_imvol[etf_imvol.Date==date][at_name].values[0].tolist() 
        out_imvol = etf_imvol[etf_imvol.Date==date][out_name].values[0].tolist()
        if at_imvol !=0:
            skeww = out_imvol/at_imvol
            a.append(skeww)
a=[x for x in a if np.isnan(x) == False]
(per1,per2,per3,per4)=(np.percentile(a,up_buy),np.percentile(a,up_sell),np.percentile(a,down_sell),np.percentile(a,down_buy))

 
day=[]  
for date in etf_option_name.date.values: #date为datetime
    date=pd.to_datetime(str(date)).strftime('%Y-%m-%d') #date为字符串  
    handle_ivx(date,_type,per1,per2,per3,per4)
    date = datetime.datetime.strptime(date, "%Y-%m-%d")
    day.append(date)
    

    
DAY_MAX=len(total_money)  
    
def cacul_performance():
    """
    Calculate annualized return, Sharpe ratio, maximal drawdown, return volatility and sortino ratio
    :return: annualized return, Sharpe ratio, maximal drawdown, return volatility and sortino ratio
    """
    rtn = total_money[-1] / capital - 1
    
    annual_rtn = np.power(rtn + 1, 252.0 / DAY_MAX) - 1  # 复利
    annual_rtn = rtn * 252 / DAY_MAX  # 单利
    
    annual_lst = [(total_money[k + 1] - total_money[k]) / total_money[k] for k in range(DAY_MAX - 1)]
    annual_vol = np.array(annual_lst).std() * np.sqrt(252.0)
    
    rf = 0.04
    semi_down_list = [annual_lst[k] < rf for k in range(DAY_MAX - 1)]
    semi_down_vol = np.array(semi_down_list).std()
    sharpe_ratio = (annual_rtn - rf) / annual_vol
    sortino_ratio = (annual_rtn - rf) / semi_down_vol
    
    max_drawdown_ratio = 0
    for e, i in enumerate(total_money):
        for f, j in enumerate(total_money):
            if f > e and float(j - i) / i < max_drawdown_ratio:
                max_drawdown_ratio = float(j - i) / i

    return annual_rtn, max_drawdown_ratio, annual_vol, sharpe_ratio, sortino_ratio

backtest_return = total_money[-1] / capital - 1
annulized, max_drawdown, rtn_vol, sharpe, sortino = cacul_performance()
#
print "boundary %d %d %d %d" % (up_buy,up_sell,down_sell,down_buy)
print "option_type",option_type,"type", _type
print befexp,"before expire %d don't trade " % (d)
## 回测绩效与绘图
print 'Return: %.2f%%' % (backtest_return * 100.0)
print 'Annualized Return: %.2f%%' % (annulized * 100.0)
print 'Maximal Drawdown: %.2f%%' % (max_drawdown * 100.0)
print 'Annualized Vol: %.2f%%' % (100.0 * rtn_vol)
print 'Sharpe Ratio: %.4f' % sharpe
print 'Sortino Ratio: %.4f' % sortino
#
#sns.set_style('white')
plt.figure(figsize=(8, 5))
plt.plot(day, total_money[1:])
plt.xlabel('Date')
plt.ylabel('Money')
plt.title('Money Curve')
plt.grid(True)
plt.show()



end = time()
print 'total time is %.6f seconds'%(end-start)
