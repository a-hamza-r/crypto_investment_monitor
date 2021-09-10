import pandas as pd;

from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json

config_data = json.load(open("config"));

info_file = config_data["info_file"];		# file containing info about crypto
stats_file = config_data["stats_file"];	# statistics about your investment
api_key = config_data["api_key"];				# file storing your API key
currency = config_data["currency"];			# currency to show values in

data = pd.read_csv(info_file, header=0);
data = data.fillna(0);

allSymb = data["Symbol"].to_numpy();
allSymbStr = ",".join(allSymb);

url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
parameters = {
  'symbol': allSymbStr,
  'convert': currency,
}
headers = {
  'Accepts': 'application/json',
  'X-CMC_PRO_API_KEY': api_key,
}

session = Session()
session.headers.update(headers)

try:
	response = session.get(url, params=parameters)
	api_data = json.loads(response.text)
	allData = api_data["data"]

except (ConnectionError, Timeout, TooManyRedirects) as e:
  print(e)

data["Current_coins_CB"] = data["Current_coins_CB"]+data["Coins_change_CB"];
data["Current_coins_CC"] = data["Current_coins_CC"]+data["Coins_change_CC"];
data["Invested_CB"] = data["Invested_CB"]+data["Invested_change_CB"];
data["Invested_CC"] = data["Invested_CC"]+data["Invested_change_CC"];
data["Coins_change_CB"].values[:] = 0;
data["Coins_change_CC"].values[:] = 0;
data["Invested_change_CB"].values[:] = 0;
data["Invested_change_CC"].values[:] = 0;

for symb in allSymb:
	mask = data["Symbol"] == symb;
	price = allData[symb]["quote"][currency]["price"];
	data.loc[mask, "Current_value_CB"] = price*data.loc[mask, "Current_coins_CB"];
	data.loc[mask, "Current_value_CC"] = price*data.loc[mask, "Current_coins_CC"];
	data.loc[mask, "Coin_price"] = price;

data.to_csv(info_file, index=False);

stats = pd.read_csv(stats_file, header=0);

withdrawn = stats.loc[0, "withdrawn"];	# withdrawn till now
total_invested = data["Invested_CB"].sum()+data["Invested_CC"].sum();	# total invested on coins
total_spent = total_invested+data["Extra_fees"].sum();	# total spent = total_invested+fees
bonus_earning = data["Bonus"].sum();
current_earning = data["Current_value_CB"].sum()+data["Current_value_CC"].sum()-bonus_earning;	# current values include bonus earnings. we want to see how much we actually earned from investing
current_revenue = current_earning + withdrawn - total_spent;

stats.loc[0, "total_invested"] = total_invested;
stats.loc[0, "total_spent"] = total_spent;
stats.loc[0, "bonus_earning"] = bonus_earning;
stats.loc[0, "current_earning"] = current_earning;
stats.loc[0, "current_revenue"] = current_revenue;

stats.to_csv(stats_file, index=False);
