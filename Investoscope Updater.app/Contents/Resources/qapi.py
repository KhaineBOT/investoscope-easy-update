import investoscope
import requests

requests.packages.urllib3.disable_warnings()

QAPI_URL   = "https://quoteapi.com"
QAPI_API   = "api/v5"
QAPI_APPID = "02ab19f92cec5cd5"
QAPI_HEDRS = {"Connection": "close",
              "Accept": "*/*",
              "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_2_5 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) CriOS/64.0.3282.112 Mobile/15D60 Safari/604.1",
              "Accept-Language": "en-au",
              "Referer": "https://quoteapi.com/",
              "Accept-Encoding": "gzip, deflate"}

def get_ticks(ticker):
  ENDPOINT = "/".join([QAPI_URL,
                       QAPI_API,
                       "symbols",
                       ticker,
                       "ticks"])
  PARAMS = {"adjustment": "capital",
            "appID":  QAPI_APPID,
            "fields": "all",
            "range": "4y"}

  response = requests.get(ENDPOINT,
                          params=PARAMS, headers=QAPI_HEDRS,
                          verify=False)

  if response.status_code != 200:
    raise RuntimeError("Unable to get data from QAPI")

  data = response.json()
  return data['ticks']


def qapi_update_market_and_code(ticker):
  # assume [code].[market]
  code_market = ticker['code'].lower().split('.')

  # return None as cannot update market
  if len(code_market) is not 2:
    return None

  # Grab code and market as variables
  code   = code_market[0]
  market = code_market[1]

  # if ASX
  if market == 'ax':
    ticker['code'] = code + '.asx'
    ticker['market'] = 'asx'
    return ticker

  return None


def ticker_known(ticker):
  if "^" in ticker['code']:
    return None

  ticker = qapi_update_market_and_code(ticker)
  if ticker is None:
    return None

  ENDPOINT = "/".join([QAPI_URL,QAPI_API, "symbol-names"])

  # only search the first portion
  # expecting [code].[market]
  PARAMS = {"appID":   QAPI_APPID,
            "markets": ticker['market'],
            "query":   ticker['code'].split('.')[0]}

  response = requests.get(ENDPOINT,
                          params=PARAMS, headers=QAPI_HEDRS,
                          verify=False)

  if response.status_code != 200:
    return None

  data = response.json()

  if 'itemCount' in data and data['itemCount'] == 0:
    return None

  # Exact match is a score of 1000
  if data['items'][0]['score'] != 1000:
    return None

  return ticker


def gen_historical_data_csv(ticker):
  ticker = ticker_known(ticker)
  if ticker is None:
    return None

  CSV_DATA = ["Date,Open,High,Low,Close,Volume"]
  data = get_ticks(ticker['code'])

  for idx in range(0,len(data['close'])-1):
    CSV_DATA.append(
      ",".join(
        [
          data['date'][idx],
          str(data['open'][idx]),
          str(data['high'][idx]),
          str(data['low'][idx]),
          str(data['close'][idx]),
          str(data['volume'][idx])
        ]
      )
    )
  
  CSV_DATA = "\n".join(CSV_DATA)

  csv_path = investoscope.generate_csv_file_name(ticker)
  with open(str(csv_path), 'w') as csv_file:
    csv_file.write(CSV_DATA)

  return CSV_DATA

if __name__ == "__main__":
  get_ticks('clh.asx')