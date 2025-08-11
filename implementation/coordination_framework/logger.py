import csv, os, time
from . import db

class RunLogger:
    def __init__(self):
        self.rows = []
        self.conn = db.initialize_database()

    def log(self, timestamp, agent_id, metric_name, metric_value, extra=""):
        self.rows.append({"t": timestamp, "agent": agent_id, "metric": metric_name, "value": metric_value, "extra": extra})
        db.write_event(self.conn, timestamp, agent_id, metric_name, metric_value, extra)

    def flush_csv(self, run_name='run'):
        os.makedirs('demonstration/execution_logs', exist_ok=True)
        path = f'demonstration/execution_logs/{run_name}_{int(time.time())}.csv'
        try:
            with open(path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['t','agent','metric','value','extra'])
                writer.writeheader()
                writer.writerows(self.rows)
            print('Saved logs to:', path)
        except Exception as e:
            # fallback: print to stdout
            print('Log write failed:', e)
            for row in self.rows[-10:]:
                print(row)
