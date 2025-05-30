import os
from datetime import datetime, timedelta
from urllib.parse import urlparse

import requests
import yfinance as yf
from bs4 import BeautifulSoup

from database_conf import DatabaseHandler
from performance import PerformanceMetrics

metrics = PerformanceMetrics()

@metrics.time_it('download')
def get_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'id': 'constituents'})

        if not table:
            print("Table with tickers not found")
            return []

        tickers = []
        rows = table.find_all('tr')

        for row in rows[1:]:
            cols = row.find_all('td')
            if cols and len(cols) > 0:
                ticker = cols[0].text.strip().replace('.', '-')
                if ticker:
                    tickers.append(ticker)

        if not tickers:
            print("Can't found tickers in table")
            return []

        return tickers

    except requests.exceptions.RequestException as e:
        print(f"Error while receiving data: {e}")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []


@metrics.time_it('database')
def download_sp500_historical_data(
        tickers,
        period_config: dict
):

    if not tickers:
        print("List of tickers is empty")
        return {}

    all_downloaded_data = {}

    for config_name, config_params in period_config.items():
        interval = config_params['interval']
        days_back = config_params['days_back']

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        print(f"\n--- Data download for configuration: '{config_name}' ---")
        print(
            f"Interval: {interval}, Period: {days_back} days (at {start_date.strftime('%Y-%m-%d')} for {end_date.strftime('%Y-%m-%d')})")

        current_config_data = {}
        for ticker in tickers:
            try:
                data = yf.download(
                    ticker,
                    start=start_date.strftime('%Y-%m-%d'),
                    end=end_date.strftime('%Y-%m-%d'),
                    interval=interval,
                    auto_adjust=True
                )

                if not data.empty:
                    current_config_data[ticker] = data[['Open', 'High', 'Low', 'Close', 'Volume',]]
                    print(f"  Data for ticker: {ticker}, interval ({interval}) loaded successfully ({len(data)}).")
                else:
                    print(f" There is no data for {ticker} ({interval}) for the period.")
            except Exception as e:
                print(f"  Error in data download {ticker} ({interval}): {e}")

        all_downloaded_data[config_name] = current_config_data

    return all_downloaded_data


if __name__ == "__main__":
    sp500_tickers = get_sp500_tickers()

    if not sp500_tickers:
        print("Could not delete the list of S&P 500 tickers. The program ends.")
    else:
        print(f"Get {len(sp500_tickers)} tickers S&P 500.")

        data_configurations = {
            "daily_2_years": {
                "interval": "1d",
                "days_back": 730
            },
            "hourly_20_days": {
                "interval": "1h",
                "days_back": 20
            },
            "five_min_2_days": {
                "interval": "5m",
                "days_back": 2
            }
        }

        all_sp500_data = download_sp500_historical_data(sp500_tickers, data_configurations)

        if all_sp500_data:
            print("\n--- DATA DOWNLOAD COMPLETE! ---")

            db_config = {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ.get('POSTGRES_DB'),
                'USER': os.environ.get('POSTGRES_USER'),
                'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
                'HOST': os.environ.get('POSTGRES_HOST'),
                'PORT': 5432,
            }

            db_handler = DatabaseHandler(db_config)
            db_handler.save_stock_data(all_sp500_data)
            save_method = metrics.time_it('database')(db_handler.save_stock_data)
            save_method(all_sp500_data)

            print("\nPerformance report:")
            print(metrics.get_summary().to_string())
            metrics.save_report()
