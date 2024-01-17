import datetime
import pandas as pd
from bs4 import BeautifulSoup
import requests
import json
import time
from io import StringIO
import random
import chardet
###############################################################################
#                           股票機器人                        #
###############################################################################
'''
選股條件：

（１）評估價值是否被低估？（股票價格不會太貴）
１．本益比＜１５倍
２．股價淨值比 < 1％
３．總報酬率 = 盈餘成長率 + 收益率(殖利率) 
４．總報酬率本益比 = 總報酬率/本益比
５．總報酬率本益比買賣標準:
（一）高於1.2(高於1.6更好)—股價被低估-->買進 
（二）0.8-1.2—股價合理 --> 不買不賣 
（三）低於0.8—股價被高估 --> 賣出

（２）確定本業利益是成長的，且為本業賺的（不是靠業外收益賺的，獲利不持久）
１．近五年營收累計年增率　＞　０％
２．近五年毛利率穩定向上　＞　０％
３．近五年營業利益益率　＞　０％
４．近五年稅前淨利率　＞０％
５．近五年稅後淨利正成長　＞０％
６．本業收益（營業利益率／稅前淨利率）　＞６０％
7. 近五年股東權益報酬率(ROE)長年維持15%或以上

（３）確定配息不是虛假的．（營運現金流有賺錢，才可以配股息）
１．近一年（２０１７）營運現金流　＞０
２．近一季（２０１８Ｑ３）營運現金流　＞０
３. 近五年現金股利正成長 (公司有維持賺錢但現金股利變少 => 財報有問題)

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
class basicStock:
    def __init__(self):
        self.init_date()
        self.StockInfoUrl = 'https://www.twse.com.tw/exchangeReport/BWIBBU_d?date=' + self.date.strftime('%Y%m%d') + '&selectType=ALL&response=json&_=' + str(time.time())
        self.FinancialUrl = 'https://mops.twse.com.tw/server-java/t164sb01?step=1&SYEAR='
        self.AvgUrl = 'http://www.twse.com.tw/exchangeReport/STOCK_DAY_AVG?response=json&date='
        self.InvestorUrl = 'https://mops.twse.com.tw/mops/web/stapap1'
        self.InvestorSellSold = 'https://www.twse.com.tw/rwd/zh/fund/T86?&selectType=ALL&response=csv&date='
        self.choosen = []
        self.filter_all_stock()
        
    def init_date(self):
        if datetime.date.today().weekday() == 6:
            self.date = datetime.datetime.today() - datetime.timedelta(days = 2)
        elif datetime.date.today().weekday() == 0:
            self.date = datetime.datetime.today() - datetime.timedelta(days = 3)
        else:
            self.date = datetime.datetime.today() - datetime.timedelta(days = 1)
        return print('獲取日期:', self.date)
    
    def modify_number_with_parentheses(self, num):
        if type(num) == float:
            return num
        elif num[-1] == ')':
            return float(num.strip('()').replace(",", ""))
        else:
            return float(num.replace(",", ""))
    
    def get_avg_price(self, stock):
        avgprice = []
        
        #要睡覺一下，不然會被ben掉
        time.sleep(random.randint(0,10))
        json_data = json.loads(str(self.crawl(self.AvgUrl + self.date.strftime("%Y%m%d") + '&stockNo=' + stock)))
        for i in range(len(json_data['data'])-1):
            avgprice.append(float(json_data['data'][i][1]))
            
        #如果不夠20日，就爬上個月的價格    
        if len(avgprice) < 19:
            #要睡覺一下，不然會被ben掉
            time.sleep(random.randint(0,10))
            json_last_data = json.loads(str(self.crawl(self.AvgUrl + (self.date  - datetime.timedelta(days=31)).strftime("%Y%m%d") + '&stockNo=' + stock)))
            for i in range(len(json_last_data['data'])-1,1,-1):
                avgprice.append(float(json_last_data['data'][i][1])) 
                
        return avgprice
    
    def get_season_data(self, stock):
        season_data = []
        
        for season in range(4,0,-1):
            if not season_data:
                season_data = self.crawl_balance_sheet(stock = stock, season = season)
            if len(season_data) > 0:
                break
        
        if not season_data:
            for last_year_season in range(4, 0, -1):
                if not season_data:
                    season_data = self.crawl_balance_sheet(stock = stock, year = datetime.date.today().year - 1, season = last_year_season)
                if len(season_data) > 0:
                    break
            
        if not season_data:
            return print('日期或資料有錯誤抓不到財報')

        return season_data
    
    def crawl(self, url = '', headers = {}, data = {}, resType = 'json'):
        if bool(headers) == False and resType == 'json':
            list_req = requests.get(url)
            list_req.encoding = chardet.detect(list_req.content)['encoding']
            return BeautifulSoup(list_req.text, "html.parser")
        elif resType == 'csv':
            return requests.get(url)
        else:
            list_req = requests.post(url, data = data, headers = headers)
            list_req.encoding = chardet.detect(list_req.content)['encoding']
            return BeautifulSoup(list_req.text, "html.parser")
        
    def crawl_twse_basic_info(self):
        url = self.StockInfoUrl
        print('某日股票url', url)
        return self.crawl(url)

    def crawl_balance_sheet(self, year = datetime.date.today().year, stock = '', season = ''):
        # url = self.FinancialUrl + str(year) + '&REPORT_ID=C&CO_ID=' + str(stock) + '&SSEASON=' + str(season)
        # time.sleep(random.randint(0,10))
        
        # if not self.crawl(url).findAll("table"):
        #     print('找不到' + str(year) + '年第' + str(season) + '季的股票' + str(stock) + '財報')
        #     return []
        
        
        
        #### 現金流量表(第3張表) 四季都相同四個欄位
        #### 綜合損益表(第2張表) 一四季為四個欄位, 二三季為六個欄位(需要依照日期合併計算)
        #### 資產負債表(第1張表) 一二三季為五個欄位(需要依照日期比較), 第四季為四個欄位
        #### 第一季須調整表格: 第1張表 (1. 比較日期的第1和3欄位(與去年同期比較))
        #### 第二季須調整表格: 第1,2張表 (1. 比較日期的第1和3欄位(與去年同期比較), 2. 獲取日期的第3,4欄位)
        #### 第三季須調整表格: 第1,2張表 (1. 比較日期的第1和3欄位(與去年同期比較), 2. 獲取日期的第3,4欄位)
        
        url = 'https://mops.twse.com.tw/server-java/t164sb01?step=1&SYEAR=2023&REPORT_ID=C&CO_ID=1102&SSEASON=3'
        
        print('某年某季財報', url)
        self.table_data = self.crawl(url).findAll("table")
        
        print('self table data', self.table_data)
        
        modify_data = []
        
        #只有獲取資產負債表, 綜合損益表, 現金流量表
        for i in range(0, 3):
            data = pd.DataFrame({
                pd.read_html(str(self.table_data))[0].columns[0][1]: pd.read_html(str(self.table_data))[i].iloc[:, 0],
                pd.read_html(str(self.table_data))[0].columns[1][1]: pd.read_html(str(self.table_data))[i].iloc[:, 1],
                pd.read_html(str(self.table_data))[0].columns[2][1]: pd.read_html(str(self.table_data))[i].iloc[:, 2],
                pd.read_html(str(self.table_data))[0].columns[3][1]: pd.read_html(str(self.table_data))[i].iloc[:, 3]
            })

            modify_data.append(data)

        return modify_data
    
    def crawl_basic_stock_info(self):
        getjson = json.loads(self.crawl_twse_basic_info().text)
        return pd.DataFrame(getjson['data'], columns=["證券代號","證券名稱","殖利率(%)","股利年度","本益比","股價淨值比","財報年/季"])
    
    def crawl_yahoo_current_price(self, stock):
        url = 'https://tw.stock.yahoo.com/q/q?s=' + stock
        print("即時股價", url)
        return float(self.crawl(url).select('ul li.price-detail-item span')[1].text)
    
    def compare_PE_PB_ratio(self):
        stockdf = self.crawl_basic_stock_info()
        PB = pd.to_numeric(stockdf['股價淨值比'], errors='coerce') < 1.0 # 找到股價淨值比小於1的股票
        PE = pd.to_numeric(stockdf['本益比'], errors='coerce') < 15 # 找到本益比小於15的股票
        print('候選股票:', stockdf[(PB & PE)])
        return stockdf[(PB & PE)] if stockdf[(PB & PE)].empty != None else print('No match basic stock found') # 綜合以上兩者，選出兩者皆符合的股票
    
    def compare_last_year_income_sum(self, getdata):
        #營收要比去年高 (其中getdata[1][getdata[1].columns[1]]是表格的第二欄會計項目其他類推)
        
        print('營收要比去年高', getdata[1][['營業收入合計' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist())
        
        return self.modify_number_with_parentheses(getdata[1][['營業收入合計' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][2]) > self.modify_number_with_parentheses(getdata[1][['營業收入合計' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][3])
    
    def compare_positive_profit(self, getdata):
        #毛利跟營收要是正的
        return self.modify_number_with_parentheses(getdata[1][['營業收入合計' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][2])  > 0 and self.modify_number_with_parentheses(getdata[1][['營業毛利（毛損）淨額' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][2]) > 0
    
    def compare_positive_operating_profit(self, getdata):
        #營業利益是正的
        return self.modify_number_with_parentheses(getdata[1][['營業利益（損失）' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][2]) > 0
    
    def compare_positive_tax_profit(self, getdata):
        #稅前稅後淨利是正的
        return self.modify_number_with_parentheses(getdata[1][['繼續營業單位稅前淨利（淨損）' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][2]) > 0 and self.modify_number_with_parentheses(getdata[1][['繼續營業單位本期淨利（淨損）' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][2]) > 0  #float(getdata[1][['繼續營業單位本期淨利（淨損）' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][2][1:-1].replace(",", "")) > 0 [1,-1]或者strip('()')可以將字串去頭去尾去掉括弧
    
    def compare_operating_profit(self, getdata):
        #本業收益（營業利益率／稅前淨利率）　＞ ６０％
        return (self.modify_number_with_parentheses(getdata[1][['營業利益（損失）' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][2]) / self.modify_number_with_parentheses(getdata[1][['營業收入合計' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][2])) / (self.modify_number_with_parentheses(getdata[1][['繼續營業單位稅前淨利（淨損）' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][2]) / self.modify_number_with_parentheses(getdata[1][['營業收入合計' in x for x in getdata[1][getdata[1].columns[1]]]].values.tolist()[0][2])) > 0.6
    
    def compare_operating_cashflow(self, getdata):
        #營運現金是正的>0
        return self.modify_number_with_parentheses(getdata[2][['本期現金及約當現金增加（減少）數' in x for x in getdata[2][getdata[2].columns[1]]]].values.tolist()[0][2]) > 0 and self.modify_number_with_parentheses(getdata[2][['本期現金及約當現金增加（減少）數' in x for x in getdata[2][getdata[2].columns[1]]]].values.tolist()[0][3]) > 0 # .values.tolist()[0][3]) > 0  [1:-1].replace(",", "")
    
    def compare_avg_price(self, stock):
        #檢查價格超過MA10、MA20
        avg20 = sum(self.get_avg_price(stock)[:20])/20
        avg10 = sum(self.get_avg_price(stock)[:10])/10
        current_price = self.crawl_yahoo_current_price(stock)
        
        if avg20 < current_price and avg10 < current_price:
            return avg20 < avg10
        
        return print('均線不達標準')
    
    def compare_institutional_investor(self, stock):
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
        
        stockbroad = self.crawl(url = self.InvestorUrl, headers = headers, data = data).find_all('td',{'style':'text-align:right !important;'})
    
                                                
        socie = pd.DataFrame()
        for element in self.table_data:
            if '當期權益變動表' in element.get_text():
                socie = pd.read_html(str(element), header =0)
                                            
        #將權益變動表的欄位名稱改成第二欄位的數字, 方式是df.column = [A,B]
        for i in range(0, len(socie[0].columns.values)):
            socie[0].columns = socie[0].iloc[:1,:].values[0]
    
        return float(stockbroad[-2:-1][0].text.replace(' ','').replace(',','')) / float(socie[0].iloc[-1,:].values[2]) > 0.1
    
    def compare_investor_sell_sold(self, stock):
        #檢查三大法人買賣狀況
        countstock = 0
        sumstock = 0
        
        for i in range(5,0,-1):
            date = datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(days=i),'%Y%m%d')
            print('三大法人買賣', 'https://www.twse.com.tw/rwd/zh/fund/T86?date='+ date +'&selectType=ALL&response=json')
            r = self.crawl(url = self.InvestorSellSold + date, resType='csv')
            
            if r.text != '\r\n': #有可能會沒有爬到東西，有可能是六日
                countstock += 1
                get = pd.read_csv(StringIO(r.text), header=1).dropna(how='all', axis=1).dropna(how='any') 
                get = get[get['證券代號'] == stock] # 找到我們要搜尋的股票
                if len(get) >0:
                    get['三大法人買賣超股數'] = get['三大法人買賣超股數'].str.replace(',','').astype(float)
                    if get['三大法人買賣超股數'].values[0] >0:
                        sumstock += 1
        
        if countstock == sumstock:
            return self.choosen.append(stock)

    def filter_all_stock(self):
                
        list = [1102,1104]
        
        for stock in range(0, len(list)):
            getdata = self.get_season_data(list[stock])
            print(getdata)
        
        
        
        # for stock in self.compare_PE_PB_ratio()['證券代號'].values:
        #     getdata = self.get_season_data(stock)

        #     #getdata是一個陣列，裡面有三個dataframe(對應網站資產負債, 綜合損益...), 分別用getdata[n]來獲得「表」, 用getdata[n][x]來獲得「欄位」包含(代號, 會計項目, 今年日期, 去年日期)
        #     if len(getdata) > 0 :
        #         if(self.compare_last_year_income_sum(getdata)):
        #             print('已確定:營收要比去年高')                    
        #             if(self.compare_positive_profit(getdata)):
        #                 print('已確定:毛利跟營收要是正的')
        #                 if(self.compare_positive_operating_profit(getdata)):
        #                     print('已確定:營業利益是正的')
        #                     if(self.compare_positive_tax_profit(getdata)):
        #                         print('已確定:稅前稅後淨利是正的')
        #                         if(self.compare_operating_profit(getdata)):
        #                             print('已確定:本業收益（營業利益率／稅前淨利率）　＞ ６０％')
        #                             if(self.compare_operating_cashflow(getdata)):
        #                                 print('已確定:營運現金是正的>0')
        #                                 if(self.compare_avg_price(stock)):
        #                                     print('已確定:檢查價格低於MA10、MA20')
        #                                     if(self.compare_institutional_investor(stock)):
        #                                         print('已確定:檢查三大法人買賣狀況')
        #                                         self.compare_investor_sell_sold(stock)
        #                                         print('單一股票:' + stock + '符合所有標準')
        #     else:
        #         print(stock + '爬蟲失敗')
        #     #要睡覺一下，不然會被ben掉
        #     time.sleep(random.randint(5,30))

        print('符合全部標準的可選擇股票', self.choosen)                     
                        

basicStock()