A prototype web app that simulates a stock trading platform, built with Python and Flask.

Users can register an account, log in, and manage a virtual portfolio with $10,000 in starting cash.
They can look up real stock prices, buy and sell shares, add cash to their account, and check their transaction history.

Note: Stock price data is fetched from CS50's finance API. The app is fully functional at the time of writing,
but this dependency may break in the future if the API is taken down. 
Migrating to a public alternative like Yahoo Finance or Alpha Vantage is a planned improvement.

User data (username and password) will only be stored locally in app.db,
which gets created automatically in your local project folder the first time you run the app. 
It will never leave your machine, but if you are not convinced you can use a mock username and password.

INSTALLATION

```
git clone https://github.com/GuillemCA10/stock-trading-simulator.git
cd stock-trading-simulator
```

SETUP

Install the required dependencies:
```
pip install -r requirements.txt
```
Run the app:
```
flask run
```
Then open your browser and go to http://127.0.0.1:5000. The database will be created automatically on first run.
