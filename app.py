from flask import Flask, render_template, request
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import requests
from datetime import datetime

app = Flask(__name__)

API_KEY = "OQB8R778HZIKCKFQ"

def load_symbols():
    df = pd.read_csv("stocks.csv")
    return sorted(df["Symbol"].tolist())

SYMBOLS = load_symbols()

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", symbols=SYMBOLS)

@app.route("/", methods=["POST"])
def run_chart():
    symbol = request.form.get("symbol")
    chart_type = request.form.get("chart_type")
    series = request.form.get("series")
    start = request.form.get("start_date")
    end = request.form.get("end_date")

    errors = []

    if symbol not in SYMBOLS:
        errors.append("Invalid symbol selected.")

    if chart_type not in ["line", "bar"]:
        errors.append("Invalid chart type.")

    if series not in ["daily", "weekly", "monthly"]:
        errors.append("Invalid time series.")

    if start == "" or end == "":
        errors.append("Start and end dates required.")
    else:
        try:
            sd = datetime.strptime(start, "%Y-%m-%d")
            ed = datetime.strptime(end, "%Y-%m-%d")
            if ed <= sd:
                errors.append("End date must be after Start date.")
        except:
            errors.append("Invalid date format.")

    if errors:
        return render_template("index.html", symbols=SYMBOLS, errors=errors)

    function_map = {
        "daily": "TIME_SERIES_DAILY",
        "weekly": "TIME_SERIES_WEEKLY",
        "monthly": "TIME_SERIES_MONTHLY"
    }

    url = f"https://www.alphavantage.co/query?function={function_map[series]}&symbol={symbol}&apikey={API_KEY}"
    r = requests.get(url)
    data = r.json()

    key_map = {
        "daily": "Time Series (Daily)",
        "weekly": "Weekly Time Series",
        "monthly": "Monthly Time Series"
    }

    ts = data[key_map[series]]

    df = pd.DataFrame(ts).T
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    df = df.loc[start:end]

    plt.figure(figsize=(10,5))

    if chart_type == "line":
        plt.plot(df.index, df["4. close"])
    else:
        plt.bar(df.index, df["4. close"])

    plt.title(f"{symbol} Closing Prices ({series})")
    plt.xlabel("Date")
    plt.ylabel("Closing Price")

    chart_path = "static/chart.png"
    plt.savefig(chart_path)
    plt.close()

    return render_template("index.html", symbols=SYMBOLS, chart="chart.png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
