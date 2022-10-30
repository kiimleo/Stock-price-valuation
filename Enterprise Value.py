### 기업가치 (기업의 적정 시가총액과 적정 주가 산정)
import requests
import pandas as pd
from bs4 import BeautifulSoup  # HTML을 파싱하는 모듈
import math


code = input('기업 코드명을 입력하세요 : ')

# 1) 지배주주 지분 : temp_df

url = 'https://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=' + code + \
      '&cID=&MenuYn=Y&ReportGB=&NewMenuID=101&stkGb=701'  # fnguide - 기업정보 - Snapshot

fr_page = requests.get(url)  # url 주소 가져와서 변수에 저장
fr_tables = pd.read_html(fr_page.text)  # 여러 테이블 가져오기
temp_df = fr_tables[10]  # Financial Highlight 표에 도착! (10번째 테이블 가져오기)
temp_df = temp_df.set_index(temp_df.columns[0])  # 표의 첫째 열을 인덱스로 설정 (원래는 0부터 시작되는 숫자 인덱스)
temp_df = temp_df.loc['지배주주지분']  # 표에서 지배주주지분 행 데이터만 가져오기
temp_df = float(temp_df[4] * 100000000)  # 지배주주지분 데이터에서 4번째 열(최근년도 지배주주지분)에 있는 값 가져오기 + 억단위 반영 + 실수화

### 2) 예상 ROE : eROE

eROE = fr_tables[11]  # fnguide - 기업정보 - Snapshot - Financial Highlight 표에 도착! (11번째 테이블 가져오기. '전체'가 아닌 '연간'이므로)
eROE = eROE.set_index(eROE.columns[0])  # 표의 첫째 열을 인덱스로 설정 (원래는 0부터 시작되는 숫자 인덱스)
eROE = eROE.loc['ROE']  # 표에서 ROE 행 데이터만 가져오기
if math.isnan(eROE[6]):  # 만약 차년도 ROE값이 nan이면 (=True이면, =값이 없으면)
    eROE = eROE[4]/100       # 전년도 ROE 값 가져오기 (상승 or 하락 추세가 있을 때 사용. 추세가 없을 땐 가중 평균을 써야 하는데 이건 나중에 수정하자) # Todo
else:                    # 차년도 ROE 값이 있으면
    eROE = eROE[6]/100       # 차년도 ROE 값 가져오기

# 3) 주주의 기대 수익률 : 기대수익률

response = requests.get('https://www.kisrating.com/ratingsStatistics/statics_spread.do')   # 한국신용평가
soup = BeautifulSoup(response.content, 'html.parser')

table = soup.find('div', { 'class': 'table_ty1' })

기대수익률 = 0

for tr in table.find_all('tr'):
    tds = list(tr.find_all('td'))
    for td in tds:
        if tds[0].text=='BBB-':
            기대수익률=float(tds[8].text)/100     # 회사채 BBB- 5년 금리


# 4) 발행총주식수 : tt = TS(the total issued stock) + TRS(treasury stock) ※ [시세현황]의 발행주식수 합 + [주주구분 현황]의 자기주식

TS = fr_tables[0]  # fnguide - 기업정보 - Snapshot - 시세현황 표에 도착! (0번째 테이블 가져오기)
TS = TS.set_index(TS.columns[0])  # 표의 첫째 열을 인덱스로 설정 (원래는 0부터 시작되는 숫자 인덱스)
TS = TS.loc['발행주식수(보통주/ 우선주)']  # 표에서 발행주식수 행 데이터만 가져오기
TS = TS[1].split('/')  # 데이터에서 1번째 열에 있는 값 가져오기. 보통주/우선주로 표시되어 있으므로 /로 값 구분
TS = int(TS[0].replace(',',''))  # 천단위 콤마 기호 지우고 정수형으로 변환

TRS = fr_tables[4]  # fnguide - 기업정보 - Snapshot - 주주구분 현황 표에 도착! (4번째 테이블 가져오기)
TRS = TRS.set_index(TRS.columns[0])  # 표의 첫째 열을 인덱스로 설정 (원래는 0부터 시작되는 숫자 인덱스)
TRS = TRS.loc['자기주식 (자사주+자사주신탁)']  # 표에서 자기주식 행 데이터만 가져오기 todo 여기서 에러발생
TRS = TRS[1]
# TRS = np.array(TRS, dtype=np.float16)    # 해당 값이 NaN이면 0으로 바꿔주는...?1 뭔가 이상함. 나중에 다시!!!
# np.nan_to_num(TRS, copy=False)           # 해당 값이 NaN이면 0으로 바꿔주는...?2 뭔가 이상함. 나중에 다시!!!

tt = TS + TRS     # 발행 총 주식수

# 기업의 적정가치 : cv

cv = temp_df+(temp_df*(eROE-기대수익률))/기대수익률   # 지배주주지분 + (지배주주지분*(예상ROE-주주의기대수익률)) / 주주의기대수익률

# 매수가 = pp ### 여기가 이상하다. 여기부터 시작해.

pp = temp_df+(temp_df*(eROE-기대수익률)*0.8)/(1+기대수익률-0.8)    # 지속계수 = 0.8 (초과이익이 해마다 80%만 지속되고 20%는 감소)

print('매수가 = ', pp)

# 매도가 = sp

sp = format(cv / tt, ',')    # 기업의 적정가치 / 발행총주식수  # 천단위 콤마 넣기

print('매도가 = ', sp)
print(cv)