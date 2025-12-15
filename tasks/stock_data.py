from datetime import datetime, timedelta
import yfinance as yf

from celery_app import app
from db import get_db, execute, fetch_one, transaction


@app.task(name="tasks.stock_data.fetch_stock_prices")
def fetch_stock_prices(company_id: int, ticker_symbol: str, days: int = 60):
    """
    Fetches historical stock prices for a company from Yahoo Finance
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        hist = stock.history(start=start_date, end=end_date)

        if hist.empty:
            return {"success": False, "error": "No data found for ticker", "inserted_count": 0}

        inserted_count = 0

        with get_db() as db:
            for date, row in hist.iterrows():
                try:
                    existing = fetch_one(
                        db,
                        "SELECT price_id FROM stock_price WHERE company_id = %s AND date = %s",
                        (company_id, date.date())
                    )

                    if not existing:
                        with transaction(db):
                            execute(
                                db,
                                """
                                INSERT INTO stock_price
                                (company_id, date, open_price, close_price, high_price, low_price, volume, currency)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                """,
                                (
                                    company_id,
                                    date.date(),
                                    float(row['Open']),
                                    float(row['Close']),
                                    float(row['High']),
                                    float(row['Low']),
                                    int(row['Volume']),
                                    'USD'
                                )
                            )
                        inserted_count += 1

                except Exception as e:
                    print(f"Error inserting price for {date}: {e}")
                    continue

        return {"success": True, "inserted_count": inserted_count}

    except Exception as e:
        return {"success": False, "error": str(e), "inserted_count": 0}


@app.task(name="tasks.stock_data.fetch_asset_prices")
def fetch_asset_prices(asset_id: int, ticker_symbol: str, days: int = 60):
    """
    Fetches historical prices for an asset from Yahoo Finance
    """
    try:
        asset_ticker = yf.Ticker(ticker_symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        hist = asset_ticker.history(start=start_date, end=end_date)

        if hist.empty:
            return {"success": False, "error": "No data found for ticker", "inserted_count": 0}

        inserted_count = 0

        with get_db() as db:
            for date, row in hist.iterrows():
                try:
                    existing = fetch_one(
                        db,
                        "SELECT asset_price_id FROM asset_price WHERE asset_id = %s AND date = %s",
                        (asset_id, date.date())
                    )

                    if not existing:
                        with transaction(db):
                            execute(
                                db,
                                """
                                INSERT INTO asset_price
                                (asset_id, date, price, currency)
                                VALUES (%s, %s, %s, %s)
                                """,
                                (
                                    asset_id,
                                    date.date(),
                                    float(row['Close']),
                                    'USD'
                                )
                            )
                        inserted_count += 1

                except Exception as e:
                    print(f"Error inserting price for {date}: {e}")
                    continue

        return {"success": True, "inserted_count": inserted_count}

    except Exception as e:
        return {"success": False, "error": str(e), "inserted_count": 0}