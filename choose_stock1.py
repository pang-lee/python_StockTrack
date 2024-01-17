#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 16 13:09:54 2019

@author: cheating
"""

import datetime
import pandas as pd
from bs4 import BeautifulSoup
import requests
import json
import time
from io import StringIO
import random
###############################################################################
#                           股票機器人   選股範例                             #
###############################################################################
'''
選股條件：

（１）評估價值是否被低估？（股票價格不會太貴）
１．本益比　＜１５倍
２．現金殖利率 　＞５％

（２）確定本業利益是成長的，且為本業賺的（不是靠業外收益賺的，獲利不持久）
１．營收累計年增率　＞　０％
２．毛利率　＞　０％
３．營業益益率　＞　０％
４．稅前淨利率　＞０％
５．稅後淨利率　＞０％
６．本業收益（營業利益率／稅前淨利率）　＞６０％

（３）確定配息不是虛假的．（營運現金流有賺錢，才可以配股息）
１．近一年（２０１７）營運現金流　＞０
２．近一季（２０１８Ｑ３）營運現金流　＞０

以上確定選出來的股票是低本益比＋高殖利率，未避免條件過於嚴格，所以先由寬至嚴，若標準太低，導致選出來的股票較多，可以把條件設嚴格．

二．技術面（這是確定底部打好，且已經向上，不摸底）
１．股價　＞　均線ＭＡ１０
２．股價　＞　均線ＭＡ２０
３．均線ＭＡ１０　與　均線ＭＡ２０　呈現黃金交叉

三．籌碼面
１．董監持股　＞　１０％以上
２．法人持續買超天數　＞　２天

董監持股高，對於公司有信心
三大法人持續買超二天以上，至少短時間看好
'''

### goodinfo爬蟲獲取歷年ROE
import requests
url = "https://goodinfo.tw/StockInfo/StockBzPerformance.asp?STOCK_ID=2330"
res = requests.get(url)
res.encoding = "utf-8"
res.text



# #### 指定時間轉成timestamp
date = datetime.datetime(2020, 7, 15)


#----------------- （１）評估價值是否被低估？（股票價格不會太貴） -------------
########## 去公開資訊觀測站，把本益比、股價淨值比爬下來 ##########
# url = 'http://www.twse.com.tw/exchangeReport/BWIBBU_d?response=json&date=&selectType=&_=' + str(time.time())

url  = 'http://www.twse.com.tw/exchangeReport/BWIBBU_d?date=' + date.strftime('%Y%m%d') + '&selectType=ALL&response=json&_=' + str(time.time())
list_req = requests.get(url)
soup = BeautifulSoup(list_req.content, "html.parser")
getjson=json.loads(soup.text)

# 因為是表格式，用dataframe處理會比較方便
stockdf = pd.DataFrame(getjson['data'],columns=["證券代號","證券名稱","殖利率(%)","股利年度","本益比","股價淨值比","財報年/季"])
PBR = pd.to_numeric(stockdf['股價淨值比'], errors='coerce') < 0.5 # 找到股價淨值比小於0.7的股票
EPS = pd.to_numeric(stockdf['本益比'], errors='coerce') < 15 # 找到本益比小於15的股票
candidate = stockdf[(PBR & EPS)] # 綜合以上兩者，選出兩者皆符合的股票

print('某日股票url', date, url)
print(candidate)


#------------------------------ 基本面財報檢查 --------------------------------

### 現在時間處裡 ###
# now = datetime.datetime.now() #現在的時間
# year = now.strftime("%Y") #抓今年
# lastmonth = now - datetime.timedelta(days=31) #一個月前的時間

now = datetime.datetime(2020, 7, 15) #現在的時間
year = 2020
lastmonth = date - datetime.timedelta(days=31) #一個月前的時間

candidate2 = []
for stock in candidate['證券代號'].values:
    for season in range(4, 0, -1):
        ### 先與網站請求抓到每天的報價資料 ###
        url = 'https://mops.twse.com.tw/server-java/t164sb01?step=1&CO_ID=' + stock + '&SYEAR=' + str(year) + '&SSEASON=' + str(season) + '&REPORT_ID=C'
        
        #要睡覺一下，不然會被ben掉
        time.sleep(random.randint(0,10))
        print('某年某季財報', url)
        
        fin_req = requests.get(url)
        fin_req.encoding = 'big5'
        soup = BeautifulSoup(fin_req.text, "html.parser")
        soup_data = soup.findAll("table") #裡面所有文字內容

        getdata = []
        
        #只有獲取資產負債表, 綜合損益表, 現金流量表
        for i in range(0, 3):
            data = pd.DataFrame({
                pd.read_html(str(soup_data))[0].columns[0][1]: pd.read_html(str(soup_data))[i].iloc[:, 0],
                pd.read_html(str(soup_data))[0].columns[1][1]: pd.read_html(str(soup_data))[i].iloc[:, 1],
                pd.read_html(str(soup_data))[0].columns[2][1]: pd.read_html(str(soup_data))[i].iloc[:, 2],
                pd.read_html(str(soup_data))[0].columns[3][1]: pd.read_html(str(soup_data))[i].iloc[:, 3]
                })
            
            getdata.append(data)
        
        if len(getdata) > 1: # 檢查'查無資料'
            break
            
    ### 檢查'查無資料'
    if len(getdata) == 1:
        url = 'https://mops.twse.com.tw/server-java/t164sb01?step=1&CO_ID=' + stock + '&SYEAR=' + str(int(year)-1) + '&SSEASON=4&REPORT_ID=C'
        #要睡覺一下，不然會被ben掉
        time.sleep(random.randint(0,10))
        getdata=pd.read_html(url, encoding='big5-hkscs',header=0)
    
    ### 檢查'查無資料'
    if len(getdata) == 1: 
        url = 'https://mops.twse.com.tw/server-java/t164sb01?step=1&CO_ID=' + stock + '&SYEAR=' + str(int(year)-1) + '&SSEASON=3&REPORT_ID=C' 
        #要睡覺一下，不然會被ben掉
        time.sleep(random.randint(0,10))
        getdata=pd.read_html(url, encoding='big5-hkscs',header=0)
    
    
    #------------------------------先顯示目前價格----------------------------------
    # 要抓取的網址
    url = 'https://tw.stock.yahoo.com/q/q?s=' + stock
    print("即時股價", url)
    #請求網站
    list_req = requests.get(url)
    #將整個網站的程式碼爬下來
    soup = BeautifulSoup(list_req.content, "html.parser")
    #找到b這個標籤
    get_stock_price = soup.select('ul li.price-detail-item span')[1].text #裡面所有文字內容

    #getdata是一個陣列，裡面有三個dataframe(對應網站資產負債, 綜合損益...), 分別用getdata[n]來獲得「表」, 用getdata[n][x]來獲得「欄位」包含(代號, 會計項目, 今年日期, 去年日期)
    if len(getdata) > 0 :
        
        #營收要比去年高 (其中getdata[1][getdata[1].columns[1]]是表格的第二欄會計項目其他類推)
        if float(getdata[1][['營業收入合計' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][2]) > float(getdata[1][['營業收入合計' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][3]):
            #毛利跟營收要是正的
            if float(getdata[1][['營業收入合計' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][2])  > 0 and float(getdata[1][['營業毛利（毛損）淨額' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][2]) > 0:
                #營業利益是正的
                if float(getdata[1][['營業利益（損失）' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][2]) > 0:
                    #稅前稅後淨利是正的
                    if float(getdata[1][['繼續營業單位稅前淨利（淨損）' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][2]) > 0 and float(getdata[1][['繼續營業單位本期淨利（淨損）' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][2][1:-1].replace(",", "")) > 0: #[1,-1]或者strip('()')可以將字串去頭去尾去掉括弧
                        #本業收益（營業利益率／稅前淨利率）　＞ ６０％
                        if (float(getdata[1][['營業利益（損失）' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][2]) / float(getdata[1][['營業收入合計' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][2])) / (float(getdata[1][['繼續營業單位稅前淨利（淨損）' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][2]) / float(getdata[1][['營業收入合計' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][2])) > 0.6:
                            #營運現金是正的>0
                            if float(getdata[2][['本期現金及約當現金增加（減少）數' in x for x in getdata[2][getdata[2].columns[1]]]].values.tolist()[0][2]) > 0 and float(getdata[2][['本期現金及約當現金增加（減少）數' in x for x in getdata[2][getdata[2].columns[1]]]].values.tolist()[0][3]) > 0:
                                #檢查價格超過MA10、MA20
                                avgprice = []
                                url = 'http://www.twse.com.tw/exchangeReport/STOCK_DAY_AVG?response=json&date=' + now.strftime("%Y%m%d") + '&stockNo=' + stock
                                
                                #要睡覺一下，不然會被ben掉
                                time.sleep(random.randint(0,10))
                               
                                list_req = requests.get(url) #請求網站
                                soup = BeautifulSoup(list_req.content, "html.parser") #將整個網站的程式碼爬下來
                                jsonsoup = json.loads(str(soup))
                                
                                for i in range(len(jsonsoup['data'])-1):
                                    avgprice.append(float(jsonsoup['data'][i][1]))

                                #如果不夠20日，就爬上個月的價格    
                                if len(avgprice) < 19:
                                    url = 'http://www.twse.com.tw/exchangeReport/STOCK_DAY_AVG?response=json&date=' + lastmonth.strftime("%Y%m%d") + '&stockNo=' + stock
                                    
                                    print('不夠20天上個月的價格url', url)
                                    #要睡覺一下，不然會被ben掉
                                    time.sleep(random.randint(0,10))
                                    
                                    list_req = requests.get(url) #請求網站
                                    soup = BeautifulSoup(list_req.content, "html.parser") #將整個網站的程式碼爬下來
                                    jsonsoup = json.loads(str(soup))
                                    for i in range(len(jsonsoup['data'])-1,1,-1):
                                        avgprice.append(float(jsonsoup['data'][i][1])) 
                                
                                #計算出平均並且進行判斷
                                avg20 = sum(avgprice[:20])/20
                                
                                if avg20 < float(get_stock_price):
                                    avg10 = sum(avgprice[:10])/10
                                    if avg10 < float(get_stock_price):
                                        #黃金交叉
                                        if avg20 < avg10:
                                            #檢查董監事持股比例
                                            data = {
                                                'step': '1',
                                                'firstin': '1',
                                                'off': '1',
                                                'queryName': 'co_id',
                                                'inpuType': 'co_id',
                                                'TYPEK': 'all',
                                                'isnew': 'true',
                                                'co_id': stock
                                            }
                                    
                                            headers = {
                                                'Host': 'mops.twse.com.tw',
                                                'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'         
                                            }
                                            
                                            url = 'https://mops.twse.com.tw/mops/web/stapap1'
                                            list_req = requests.post(url, data=data ,headers=headers)
                                            soup = BeautifulSoup(list_req.content, "html.parser")
                                            stockbroad = soup.find_all('td',{'style':'text-align:right !important;'})
                                            
                                            socie = pd.DataFrame()
                                            for element in soup_data:
                                                if '當期權益變動表' in element.get_text():
                                                    socie = pd.read_html(str(element),header =0)
                                            
                                            #將權益變動表的欄位名稱改成第二欄位的數字, 方式是df.column = [A,B]
                                            for i in range(0, len(socie[0].columns.values)):
                                                socie[0].columns = socie[0].iloc[:1,:].values[0]
                                            
                                            if float(stockbroad[-2:-1][0].text.replace(' ','').replace(',','')) / float(socie[0].iloc[-1,:].values[2]) > 0.1:
                                                #檢查三大法人買賣狀況
                                                countstock = 0
                                                sumstock = 0
                                                
                                                for i in range(5,0,-1):
                                                    date = datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(days=i),'%Y%m%d')
                                                    r = requests.get('https://www.twse.com.tw/rwd/zh/fund/T86?date='+ date +'&selectType=ALL&response=csv')
                                                    print('三大法人買賣', 'https://www.twse.com.tw/rwd/zh/fund/T86?date='+ date +'&selectType=ALL&response=json')
                                                    
                                                    if r.text != '\r\n': #有可能會沒有爬到東西，有可能是六日
                                                        countstock += 1
                                                        get = pd.read_csv(StringIO(r.text), header=1).dropna(how='all', axis=1).dropna(how='any') 
                                                        get = get[get['證券代號'] == stock] # 找到我們要搜尋的股票
                                                        if len(get) >0:
                                                            get['三大法人買賣超股數'] = get['三大法人買賣超股數'].str.replace(',','').astype(float)
                                                            if get['三大法人買賣超股數'].values[0] >0:
                                                                sumstock += 1
                                                
                                                if countstock == sumstock:
                                                    candidate2.append(stock)
    else:
        print(stock + '爬蟲失敗')
    #要睡覺一下，不然會被ben掉
    time.sleep(random.randint(5,30))

print('the result of candidate', candidate2)
                            
                            
                    


    

        



