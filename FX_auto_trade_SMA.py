"""
SMAAutotrading-system-version_1.0.3
以下のパケージのインストールが必要です
・oandapyV20 # オアンだパッケージのインストール
注意
・動かす前にすべてのポジションをクローズしてから動かす事

"""
from oandapyV20 import API
import oandapyV20.endpoints.instruments as instruments
import pandas as pd
import numpy as np
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.positions as positions

accountID="" #Oandaの個人ID
access_token=""#Oandaの個人token
api=API(access_token=access_token)

import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import pytz
import time
np.set_printoptions(threshold=np.inf)

import requests #LINE

url = "" #line notify のURL
Laccess_token = ""#LINEaccesstoken
headers = {'Authorization': 'Bearer ' + Laccess_token}

def LINEmessage(conv):#LINEメッセージ送信関数
  payload = {'message': conv}
  r = requests.post(url, headers=headers, params=payload,)

def PLvalue():#損失値返却関数
  trading_data=api.request(trades.OpenTrades(accountID=accountID))
  return float(trading_data["trades"][0]["unrealizedPL"])

Losscutlevel=-5.0
def LossCut(trading_data): #損切関数
  if trading_data:
    trading_data=api.request(trades.OpenTrades(accountID=accountID)) #現在のロスを知るために一度データの取得
    if float(trading_data["trades"][0]["unrealizedPL"]) < Losscutlevel: #損切
      r=trades.TradeClose(accountID=accountID,tradeID=trading_data["trades"][0]["id"],data=datab) #最も新しく取引したトレードを売却 trading_data["lastTransactionID"]っていうのは最新取引ID
      api.request(r)
      global initialize,position,profit #トレード変数のグローバル変数化
      print("損切")
      initialize=0 #初回の処理に入る
      position=0
      profit+=float(trading_data["trades"][0]["unrealizedPL"])
      LINEmessage("損切しました."+"profit:"+str(profit)+"JPY"+"onlyprofit"+str(trading_data["trades"][0]["unrealizedPL"]))
      trading_data={} #データの初期化,関数化しているためグローバル化が必要
      return trading_data
    return trading_data
  return trading_data

def get_mdata(num):
  params={"count":num,"granularity":"M1"}
  r=instruments.InstrumentsCandles(instrument="USD_JPY",params=params)
  api.request(r)
  Z=r.response #r.responseはdict型で返す.
  #"candle":{いろいろな詳細データこの中のデータを使う}'granularity': 'M5','instrument': 'USD_JPY'
  data=[]
  for raw in r.response["candles"]:
    data.append([raw["time"],raw["volume"],raw["mid"]["o"],raw["mid"]["h"]
                ,raw["mid"]["l"],raw["mid"]["c"]])

  df=pd.DataFrame(data)
  df.columns=["time","volume","open","high","low","close"] #カラム名の変更
  df=df.set_index("time") #indexをtimeに変更
  df.index=pd.to_datetime(df.index) #indexの型をtimedateに変更
  df["close"]=df["close"].astype(float) #ここでfloatにキャスト。これをしないとmeanとかが使えない
  return df

def SMA(df): #ゴールデンクロス、デットクロスを入れたデータフレームを返す関数
  # 単純移動平均を計算
  sma1=2 #ここを調整
  sma2=5

  def sma_1(): #文字列変換sma1
    return 'sma_'+str(sma1)

  def sma_2(): #文字列変換sma2
    return 'sma_'+str(sma2)

  #df = df[['time', 'close' ]]
  df[sma_1()] = np.round(df['close'].rolling(window=sma1).mean(), 2)
  df[sma_2()] = np.round(df['close'].rolling(window=sma2).mean(), 2)
  df[0:18]

  df['diff'] = df[sma_1()] - df[sma_2()] #短期移動線ー長期移動線=diff

  # ゴールデンクロスを検出
  asign = np.sign(df['diff']) #sign:マイナスであればー１、＋であれば１に変換する関数
  sz = asign == 0 #sz:asign=0のところはTrue、他はすべてFalse
  while sz.any(): #差分diffが０になることも考えられるので、そのときはwhileの処理をする.sz.any()いずれかの要素がtrue→true
      asign[sz] = np.roll(asign, 1)[sz]#np.roll()[配列]配列を要素方向に１っこずらしている
      sz = asign == 0

  signchange_g = ((np.roll(asign, 1) - asign) == -2).astype(int) #-2の時にゴールデンクロス
  df['Gcross'] = signchange_g

  
  #デットクロスの検知
  asign = np.sign(df['diff'])
  sz = asign == 0
  while sz.any():
      asign[sz] = np.roll(asign, 1)[sz]
      sz = asign == 0
  
  signchange_d = ((np.roll(asign, 1) - asign) == 2).astype(int)
  df['Dcross'] = signchange_d
  """
  # デッドクロスの出現箇所を「-1」としてデータフレームへコピー
  df['dead'] = df['cross']
  df['dead'][df['dead'] == 1] = -1
  """
  return df,sma_1(),sma_2()

data1={
    "order":{
        "instrument":"USD_JPY",
        "units":"+1000",
        "type":"MARKET",
        "positionFill":"DEFAULT"
    }
}

data2={
    "order":{
        "instrument":"USD_JPY",
        "units":"-1000",
        "type":"MARKET",
        "positionFill":"DEFAULT"
    }
}
datab={
    "units":"1000"
}

df=get_mdata(5000)
df,sma1,sma2=SMA(df) #sma1=sma_(Short_value),sma2=sma_(Long_value)の文字列を取得
print(int(df["Gcross"].tail(1)))
print(df["Dcross"])

#以下繰り返し処理
startminute =datetime.now().minute
starthour=datetime.now().hour
startday=datetime.now().day

nowminute =datetime.now().minute
nowhour=datetime.now().hour
nowday=datetime.now().day

initialize=0
position =0
profit=0
only_profit=0
trading_data={}

while(1): #分を起点としてnow-startの差分で回す時間を決める
  Mdata = get_mdata(100) #500件読み込み
  df,sma1,sma2=SMA(Mdata) #sma1=sma_(Short_value),sma2=sma_(Long_value)の文字列を取得
  now_Gcross_point=int(df["Gcross"].tail(1))
  now_Dcross_point=int(df["Dcross"].tail(1))

  if now_Gcross_point==1 and position==0 and initialize==0:
    c=orders.OrderCreate(accountID,data=data1)
    api.request(c)
    trading_data=api.request(trades.OpenTrades(accountID=accountID))
    #ticket=oanda.create_order(account_id=account_id,instrument="USD_JPY",units=5000,side="buy",type ="market")
    #成り行き注文で買い注文
    position=1
    initialize=1 #子のループにはもう入れないようにする
    print("買い"+"\n時刻"+datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S')) #売買時の時刻表示
    LINEmessage("買い注文を入れましたinitialLong")

  if now_Dcross_point==1 and position==0 and initialize==0:
    c=orders.OrderCreate(accountID,data=data2)
    api.request(c)
    trading_data=api.request(trades.OpenTrades(accountID=accountID))
    #ticket=oanda.create_order(account_id=account_id,instrument="USD_JPY",units=5000,side="sell",type ="market")
    position=2
    initialize=1
    print("売り"+"\n時刻"+datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S'))
    LINEmessage("売り注文を入れましたinitialShort")

  if now_Gcross_point==1 and position==2 and initialize==1:
    profit+=PLvalue() #利益を計算
    only_profit=PLvalue() #単体トレードの利益
    r=trades.TradeClose(accountID=accountID,tradeID=trading_data["trades"][0]["id"],data=datab) #最も新しく取引したトレードを売却 trading_data["lastTransactionID"]っていうのは最新取引ID
    api.request(r)
    c=orders.OrderCreate(accountID,data=data1)
    api.request(c)
    trading_data=api.request(trades.OpenTrades(accountID=accountID))
    #ticket=oanda.create_order(account_id=account_id,instrument="USD_JPY",units=5000,side="buy",type ="market")
    #成り行き注文で買い注文
    position=1
    print("買い"+"\n時刻"+datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S')) #売買時の時刻表示
    print("利益"+str(profit))
    LINEmessage("買い注文を入れました profit"+str(profit)+"JPY onlyprofit"+str(only_profit)+"JPY")

  if now_Dcross_point==1 and position==1 and initialize==1:
    profit+=PLvalue() #利益を計算
    only_profit=PLvalue() #単体トレード利益
    r=trades.TradeClose(accountID=accountID,tradeID=trading_data["trades"][0]["id"],data=datab) #最も新しく取引したトレードを売却 trading_data["lastTransactionID"]っていうのは最新取引ID
    api.request(r)
    c=orders.OrderCreate(accountID,data=data2)
    api.request(c)
    trading_data=api.request(trades.OpenTrades(accountID=accountID))
    #ticket=oanda.create_order(account_id=account_id,instrument="USD_JPY",units=5000,side="sell",type ="market")
    position=2
    print("売り"+"\n時刻"+datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S'))
    print("利益"+str(profit))
    LINEmessage("売り注文を入れました profit"+str(profit)+"JPY onlyprofit"+str(only_profit)+"JPY")

  #損切確認
  trading_data=LossCut(trading_data)

  #日によるプログラムの制御
  dt_now = datetime.now(pytz.timezone('Asia/Tokyo')) #抜日の設定
  dt_now_oanda =datetime.now()#backtestingの抜日に合わせる
  
  if dt_now.weekday()==5 and dt_now.hour==5 and dt_now.minute==50: #(土曜日の午前5時50分)
    print("停止期間")
    LINEmessage("今週もトレードお疲れさまでした。")
    while(not (dt_now.weekday()==0 and dt_now.hour==7 and dt_now.minute==5)):#(月曜日の午前７時5分)
      time.sleep(120)
      print("stop")
      dt_now = datetime.now(pytz.timezone('Asia/Tokyo'))
  
  if dt_now.weekday()==1 and dt_now.hour==9 and dt_now.minute==30:#火曜日を抜く(日本時間の火曜日9:30に停止)
    print("指定抜日期間に入りました。")
    LINEmessage("指定抜日期間に入りました。")
    time.sleep(61)#60s停止
    while(not (dt_now.hour==9 and dt_now.minute==30)):
      dt_now = datetime.now(pytz.timezone('Asia/Tokyo')) #抜日の設定 
      trading_data=LossCut(trading_data) #プログラム停止中の損切
      time.sleep(20)
      
  time.sleep(10)
