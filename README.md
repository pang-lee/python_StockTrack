### This is the test of using python to fetch stock price and data
### Tools:

#### pip install yfinance and twstock


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
