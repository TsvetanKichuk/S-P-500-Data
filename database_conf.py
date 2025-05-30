from sqlalchemy import create_engine
from sqlalchemy.types import Float, String, DateTime


class DatabaseHandler:
    def __init__(self, db_config):
        self.connection_string = (
            f"postgresql://{db_config['USER']}:{db_config['PASSWORD']}"
            f"@{db_config['HOST']}:{db_config['PORT']}/{db_config['NAME']}"
        )
        self.engine = None

    def _create_engine(self):
        if not self.engine:
            self.engine = create_engine(self.connection_string)
        return self.engine

    def save_stock_data(self, data_dict):
        dtype_mapping = {
            'Open': Float,
            'High': Float,
            'Low': Float,
            'Close': Float,
            'Volume': Float
        }

        engine = self._create_engine()

        try:
            for config_name, config_data in data_dict.items():
                print(f"\nSaving data for configuration: '{config_name}'")

                total_rows = 0
                for ticker, df in config_data.items():
                    if not df.empty:
                        df_to_save = df.reset_index()
                        df_to_save['ticker'] = ticker
                        df_to_save['timeframe'] = config_name
                        df_to_save = df_to_save.rename(columns={'index': 'datetime'})

                        table_name = 'stock_prices'
                        df_to_save.to_sql(
                            table_name,
                            engine,
                            if_exists='append',
                            index=False,
                            dtype={
                                'datetime': DateTime,
                                'ticker': String,
                                'timeframe': String,
                                **dtype_mapping
                            }
                        )
                        total_rows += len(df_to_save)
                print(f"  Saved for records: {config_name}: {total_rows}")

            print("\nAll data has been successfully saved to PostgreSQL.")

        except Exception as e:
            print(f"Error saving data to PostgreSQL: {e}")
        finally:
            self.close()

    def close(self):
        if self.engine:
            self.engine.dispose()
            self.engine = None
