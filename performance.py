import time
from functools import wraps
from datetime import datetime
import pandas as pd


class PerformanceMetrics:
    def __init__(self):
        self.metrics = {
            'download': {},
            'database': {},
            'total': {}
        }

    def time_it(self, category):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()

                execution_time = end_time - start_time

                if category == 'download':
                    if isinstance(result, dict):
                        for config_name in result.keys():
                            self.metrics[category][config_name] = execution_time
                elif category == 'database':
                    if len(args) > 1 and isinstance(args[1], dict):
                        for config_name in args[1].keys():
                            self.metrics[category][config_name] = execution_time

                return result

            return wrapper

        return decorator

    def calculate_total_metrics(self):
        for config_name in self.metrics['download'].keys():
            self.metrics['total'][config_name] = (
                    self.metrics['download'].get(config_name, 0) +
                    self.metrics['database'].get(config_name, 0)
            )

    def get_summary(self):
        self.calculate_total_metrics()

        data = []
        for config_name in self.metrics['download'].keys():
            data.append({
                'Configuration': config_name,
                'Loading time, (sec)': round(self.metrics['download'].get(config_name, 0), 2),
                'Writing time to DB, (sec)': round(self.metrics['database'].get(config_name, 0), 2),
                'Total time, (sec)': round(self.metrics['total'].get(config_name, 0), 2)
            })

        return pd.DataFrame(data)

    def save_report(self, filename=None):
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'performance_report_{timestamp}.csv'

        df = self.get_summary()
        df.to_csv(filename, index=False)
        print(f"\nReport saved at file: {filename}")
