# 5年分の馬の情報をnetkeibaからスクレイピングするスクリプト
# 取得したい年のrace_id=以降の情報を第一引数とする
# 例 201905030211 (2019安田記念)
import requests
from tqdm import tqdm
import time
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import sys

# net競馬のurl
Base = "http://race.sp.netkeiba.com/?pid=race_result&race_id="
dst = ''
df_col = ['year', 'date', 'field', 'race', 'race_name'
          , 'course', 'head_count', 'rank', 'horse_name'
          , 'gender', 'age', 'trainerA', 'trainerB', 'weight', 'c_weight', 'jackie', 'j_weight'
          , 'odds','popu', 'time', 'last3f']
df = pd.DataFrame()

# 年
y = sys.argv[1][0:4]
# レースコード
r_code = sys.argv[1][4:]

# 5年間のリストを作成
# 例 2014 2015 2016 2017 2018
y_5_list = [y for y in range(int(y) - 5 , int(y))]

for year in y_5_list:
    url = Base + str(year) + str(r_code)
    time.sleep(1)
    html = requests.get(url)
    html.encoding = 'EUC-JP'

    # scraping
    soup = BeautifulSoup(html.text, 'html.parser')

    #共通部分を抜き出す
    CommonYear = year
    CommonDate = soup.find_all('div', attrs={'class', 'Change_Btn Day'})[0].string.strip()
    CommonField= soup.find_all('div', attrs={'class', 'Change_Btn Course'})[0].string.strip()
    CommonRace = soup.find_all('div', attrs={'Race_Num'})[0].span.string
    CommonRname= soup.find_all('dt', attrs={'class', 'Race_Name'})[0].contents[0].strip()
    CommonCourse= soup.find_all('dd', attrs={'Race_Data'})[0].span.string
    CommonHcount= soup.find_all('dd', attrs={'class', 'Race_Data'})[0].contents[3].split()[1]

    for m in range(len(soup.find_all('div', attrs='Rank'))):
        dst = pd.Series(index=df_col)
        try:
            dst['year'] = CommonYear 
            dst['date'] = CommonDate
            dst['field']= CommonField #開催場所
            dst['race'] = CommonRace # 何レース
            dst['race_name'] = CommonRname
            dst['course'] = CommonCourse
            dst['head_count'] = CommonHcount #頭数
            dst['rank'] = soup.find_all('div', attrs='Rank')[m].contents[0]
            dst['horse_name'] = soup.find_all('dt', attrs=['class', 'Horse_Name'])[m].a.string
            detailL = soup.find_all('span', attrs=['class', 'Detail_Left'])[m]
            dst['gender'] = list(detailL.contents[0].split()[0])[0]
            dst['age'] = list(detailL.contents[0].split()[0])[1]
            dst['trainerA'] = detailL.span.string.split('･')[0] # 調教師
            dst['trainerB'] = detailL.span.string.split('･')[1] # 厩舎
            if len(detailL.contents[0].split())>=2:
                dst['weight'] = detailL.contents[0].split()[1].split('(')[0] # 馬の体重
                if len(detailL.contents[0].split()[1].split('('))>=2:
                    dst['c_weight'] = detailL.contents[0].split()[1].split('(')[1].strip(')') #馬の体重変動
            detailR = soup.find_all('span', attrs=['class', 'Detail_Right'])[m].contents
            if  "\n" in detailR or "\n▲" in detailR or '\n☆' in detailR:
                detailR.pop(0)
            dst['jackie'] = detailR[0].string.strip() 
            dst['j_weight'] = detailR[2].strip().replace('(', '').replace(')', '') #jackieの総重量
            Odds = soup.find_all('td', attrs=['class', 'Odds'])[m].contents[1]
            if Odds.dt.string is not None:
                dst['odds'] = Odds.dt.string.strip('倍')
                dst['popu'] = Odds.dd.string.strip('人気') #何番人気か
            Time = soup.find_all('td', attrs=['class', 'Time'])[m]
            dst['time'] = Time.contents[1].dt.string.strip() # タイム
            dst['last3f'] = str(Time).split('<dd>')[2][1:5] # 上がり3ハロン
        except:
            pass
        dst.name = str(year) + str(r_code)

        df = df.append(dst)

# csv出力
df.to_csv('keiba_{}.csv'.format(r_code), encoding='shift-jis')