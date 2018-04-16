import os
import json
import requests
import urllib, http.client
import hmac, hashlib
import sys
import random
from decimal import Decimal
import time

buy_q = Decimal(sys.argv[1])
sell_q = Decimal(sys.argv[2])
balance_q = Decimal(sys.argv[3])
API_KEY = sys.argv[4]
API_SECRET = sys.argv[5].encode()

nonce_file = "./nonce"
if not os.path.exists(nonce_file):
    with open(nonce_file, "w") as out:
        out.write('1')


class YobitException(Exception):
    pass


def call_api(**kwargs):
    with open(nonce_file, 'r') as inp:
        nonce = int(inp.read().strip())
        with open(nonce_file, 'w') as inp1:
            inp1.write(str(nonce+1))

    payload = {'nonce': nonce}

    if kwargs:
        payload.update(kwargs)
    payload = urllib.parse.urlencode(payload)

    H = hmac.new(key=API_SECRET, digestmod=hashlib.sha512)
    H.update(payload.encode('utf-8'))
    sign = H.hexdigest()

    headers = {"Content-type": "application/x-www-form-urlencoded",
           "Key":API_KEY,
           "Sign":sign}
    conn = http.client.HTTPSConnection("yobit.net", timeout=60)
    conn.request("POST", "/tapi/", payload, headers)
    response = conn.getresponse().read()

    conn.close()

    try:
        obj = json.loads(response.decode('utf-8'))

        if 'error' in obj and obj['error']:
            raise YobitException(obj['error'])
        return obj
    except json.decoder.JSONDecodeError:
        raise YobitException('Fail', response)
start_time = time.time()
balance = Decimal(call_api(method='getInfo')['return']['funds']['btc']) * (Decimal(0.01) * balance_q)
print("Requested balance in --- %s seconds ---" % (time.time() - start_time))
num = 0
xxx_btc = input('Enter coin:')+"_btc"
#start_time1 = time.time()
start_time = time.time()
res = requests.get('https://yobit.net/api/3/ticker/'+xxx_btc)
time_coin_r = time.time() - start_time
print("Requested coin price in --- %s seconds ---" % time_coin_r)
coin = json.loads(res.text)[xxx_btc]
last = "%0.8f" % coin['last']
min = "%0.8f" % coin['low']
amount = (Decimal(balance) / ((Decimal(last)) * buy_q))
print("Balance: " + str(balance))
print("Pair: " + xxx_btc.upper())
print("Last price: " + str(last))
print("Min price: " + str(min))
print("Buy at: " + str(buy_q * 100) + "%")
print("Sell at: " + str(sell_q * 100) + "%")
print("Amount: " + str(amount))
orders = []

val = Decimal(coin['last']) >= (Decimal(coin['low']) * sell_q)
if val and time_coin_r < 2:
    min = last
elif val and time_coin_r > 2:
    print("Too late to do something. Train your hand, son.")
    exit(0)

buy_rate = "%0.8f" % (float(min) * float(buy_q))
sell_rate = "%0.8f" % (float(min) * float(sell_q))
buy_am = "%0.2f" % (amount / 10.0)
print("Buy %10 amount: " + buy_am)
for i in range(10):
    try:
        trade = call_api(method="Trade", pair=xxx_btc, type="buy", rate=buy_rate, amount=buy_am)
        if trade['success'] == 1:
            order_id = trade['return']['order_id']
            #print("Placed Buy order #"+str(order_id))
            orders.append(order_id)
            #print("Time for placing order (from coin name enter) --- %s seconds ---" % (time.time() - start_time1))
        else:
            print(trade)
    except YobitException as e:
        print("Cant : ", e)
time.sleep(1)
while num < 15:
    num += 1
    print(num, ".Trying to sell")
    try:
        trade = call_api(method="Trade", pair=xxx_btc, type="sell", rate=sell_rate, amount=buy_am)
        if trade['success'] == 1:
            print("Placed Sell order #"+str(trade['return']['order_id']))
    except:
        print("Cant")
        
print("Profit: " + str(Decimal(call_api(method='getInfo')['return']['funds']['btc']) * (Decimal(0.01) * balance_q) - balance))
for i in orders:
    try:
        cancel = call_api(method="CancelOrder", order_id=i)
    except:
        pass
