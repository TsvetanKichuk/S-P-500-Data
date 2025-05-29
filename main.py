import os
from datetime import datetime, timedelta

import requests
import yfinance as yf
from bs4 import BeautifulSoup


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
                    print(f"  Data for {ticker} ({interval}) loaded successfully ({len(data)}).")
                else:
                    print(f" There is no data for {ticker} ({interval}) for the period.")
            except Exception as e:
                print(f"  Error  in data download {ticker} ({interval}): {e}")

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
            for config_name, config_data in all_sp500_data.items():
                print(f"\nConfiguration: '{config_name}'")
                downloaded_count = len([t for t, df in config_data.items() if not df.empty])
                print(f"Number of tickers with data: {downloaded_count} with {len(sp500_tickers)}")

                if 'S&P500' in config_data and not config_data['S&P500'].empty:
                    print(f"Data example S&P500 ({config_name}):")
                    print(config_data['S&P500'].head())
                    print(f"  Number of records S&P500: {len(config_data['S&P500'])}")
                else:
                    print(f" Data for S&P500 ({config_name}) not found.")

            base_output_dir = "sp500_historical_multi_timeframe_data"
            for config_name, config_data in all_sp500_data.items():
                config_output_dir = os.path.join(base_output_dir, config_name)
                os.makedirs(config_output_dir, exist_ok=True)
                for ticker, df in config_data.items():
                    if not df.empty:
                             file_path = os.path.join(config_output_dir, f"{ticker}.csv")
                             df.to_csv(file_path)
                             print(f"Data for {ticker} ({config_name}) saved at {file_path}")
                print(f"\n All data were saved at: {base_output_dir}")

        else:
            print("Couldn't get data for S&P 500.")
