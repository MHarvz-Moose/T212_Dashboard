from radar.report import build_report

if __name__ == "__main__":
    daily = build_report("daily", refresh_prices=True)
    weekly = build_report("weekly", refresh_prices=False)
    print(f"Daily report: {daily}")
    print(f"Weekly report: {weekly}")
