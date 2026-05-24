A web app that simulates a stock trading platform, built with Python and Flask.

Users can register an account, log in, and manage a virtual portfolio with $10,000 in starting cash.
They can look up real stock prices, buy and sell shares, add cash to their account, and check their transaction history.

Note: Stock price data is fetched from CS50's finance API. The app is fully functional at the time of writing,
but this dependency may break in the future if the API is taken down.

Migrating to a public alternative like Yahoo Finance or Alpha Vantage is a planned improvement.

SETUP

First you'll have to clone the repository:

```
git clone https://github.com/your-username/stock-trading-app.git
cd stock-trading-app
```

Then, install the required dependencies:
```
pip install -r requirements.txt
```
Run the app:
```
flask run
```
Finally, open your browser and go to http://127.0.0.1:5000.
