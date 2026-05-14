# Trading 212 ISA Market Radar

A GitHub + Streamlit MVP for a daily and weekly market-awareness report across instruments you can track for a Trading 212 Stocks & Shares ISA.

The project is designed as a **market radar**, not a trading bot. It generates momentum, breakout, and “waking up” tables to help you notice emerging themes earlier.

## Architecture

```text
GitHub Actions
  ├── runs the daily report on weekdays
  └── runs the weekly report on Sundays

Python report engine
  ├── loads the instrument universe
  ├── fetches price data
  ├── calculates signals
  └── writes Markdown + CSV outputs

Streamlit Community Cloud
  └── displays the latest saved reports and explorer tables
```

## Repo structure

```text
trading212-market-radar/
├── app.py                         # Streamlit app
├── requirements.txt
├── README.md
├── config/
│   └── settings.yaml
├── data/
│   ├── universe_seed.csv           # Starter universe for immediate testing
│   └── price_cache/                # Created after first run
├── reports/
│   ├── daily/                      # Dated daily reports
│   ├── weekly/                     # Dated weekly reports
│   ├── outputs/                    # Latest CSVs for Streamlit tables
│   ├── latest_daily.md             # Latest daily report
│   └── latest_weekly.md            # Latest weekly report
├── src/radar/
│   ├── config.py
│   ├── trading212.py
│   ├── universe.py
│   ├── prices.py
│   ├── signals.py
│   ├── report.py
│   └── backtest_detection.py
└── .github/workflows/
    ├── daily_report.yml
    └── weekly_report.yml
```

## Quick local run

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export PYTHONPATH=src          # Windows PowerShell: $env:PYTHONPATH="src"
python -m radar.report --kind daily --refresh-prices
python -m radar.report --kind weekly --refresh-prices
streamlit run app.py
```

## Deploy with GitHub + Streamlit Community Cloud

1. Create a new GitHub repository.
2. Upload all files from this project.
3. In Streamlit Community Cloud, create a new app from the GitHub repo.
4. Set the app entrypoint to:

```text
app.py
```

5. In GitHub, go to **Actions** and manually run:
   - `Generate daily market radar`
   - `Generate weekly market radar`

6. Once those actions commit `reports/latest_daily.md`, `reports/latest_weekly.md`, and CSV outputs, refresh the Streamlit app.

## GitHub Actions schedule

The default schedules are:

- Daily report: weekdays at `07:30` UTC/GMT.
- Weekly report: Sundays at `09:00` UTC/GMT.

GitHub cron uses UTC. Change the cron lines in:

```text
.github/workflows/daily_report.yml
.github/workflows/weekly_report.yml
```

## Secrets

The starter version uses `data/universe_seed.csv` and free Yahoo Finance data, so you do **not** need Trading 212 credentials for the first run.

When you later switch to a Trading 212 universe, add these GitHub repository secrets:

```text
TRADING212_ENV=live
TRADING212_API_KEY=your_key
TRADING212_API_SECRET=your_secret
```

Do not commit API keys into the repo.

## Switching from seed universe to Trading 212 universe

The MVP currently uses:

```yaml
data:
  universe_source: "seed"
```

in `config/settings.yaml`.

To use Trading 212 metadata later:

1. Add your API credentials locally or as GitHub secrets.
2. Fetch raw instruments:

```bash
export PYTHONPATH=src
python -m radar.trading212
```

3. This creates:

```text
data/trading212_instruments_raw.csv
```

4. Then run the universe mapping process and fill in the external market-data tickers. This part is deliberately manual at first, because Trading 212 symbols and Yahoo/EODHD/Stooq symbols do not always match perfectly.

## Important limitations

- This is an awareness tool, not financial advice or a buy/sell system.
- Free market data can have gaps and ticker-mapping issues.
- Yahoo Finance is fine for prototyping but not ideal as a production-grade data source.
- The instrument universe will need cleaning before you use it as a full Trading 212 ISA scanner.
- GitHub Actions scheduled jobs are suitable for daily/weekly reports, not precise intraday alerts.

## Next development steps

1. Run the seed version and check whether the report format is useful.
2. Expand `data/universe_seed.csv` with instruments you care about.
3. Create a cleaned `instrument_mapping.csv` from Trading 212 to Yahoo/EODHD/Stooq tickers.
4. Add more theme tags.
5. Add charts to the weekly report.
6. Add a historical “would I have noticed this?” detection test.
