import yfinance as yf
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import defaultdict
import math
from datetime import datetime
import time


def get_stock_price(ticker):
    ticker_data = yf.Ticker(ticker)

    # get the max data from stock prices
    # ticker_df = ticker_data.history(period="max")
    ticker_df = ticker_data.history(start="1998-01-01")

    ticker_df.reset_index(inplace=True)
    ticker_df['Date'] = ticker_df['Date'].dt.strftime('%Y-%m-%d')

    ticker_df = ticker_df.drop(['Dividends', 'Stock Splits'], axis=1)
    ticker_df = ticker_df.round(6)
    return ticker_df


def get_stock_earning_days(ticker):
    ticker_data = yf.Ticker(ticker)

    # get the max amount of earning days + 4 future days
    ticker_earnings_date = ticker_data.get_earnings_dates(limit=95)
    ticker_earnings_date.reset_index(inplace=True)

    ticker_earnings_date['Earnings Date'] = ticker_earnings_date['Earnings Date'].dt.strftime('%Y-%m-%d')

    ticker_earnings_dates = ticker_earnings_date.drop(['EPS Estimate', 'Reported EPS', 'Surprise(%)'], axis=1)

    return ticker_earnings_dates


# Calculate percentage change for earnings days
def calculate_price_differences(df, df_earnings):
    time_offsets = [-42, -35, -28, -21, -14, -7, 0, 7, 14, 21, 28, 35, 42]
    earnings_diffs = []
    # trading_days = set(df['Date'])  # Set of all trading days

    today = pd.Timestamp('today')  # Get today's date for future date check

    for earnings_day in df_earnings:
        if earnings_day > today:
            continue

        earnings_close = df.loc[df['Date'] == earnings_day.strftime('%Y-%m-%d'), 'Close']
        if earnings_close.empty:
            continue

        row = {}
        earnings_close = earnings_close.iloc[0]
        row['earnings_day'] = earnings_day

        for offset in time_offsets:
            date_offset = (earnings_day + pd.DateOffset(days=offset)).strftime('%Y-%m-%d')
            if offset != 0:
                day_price = df.loc[df['Date'] == date_offset, 'Close']

                if day_price.empty:
                    if offset >= 7:
                        day_price = df.loc[df['Date'] == (earnings_day + pd.DateOffset(days=offset + 5)).strftime('%Y-%m-%d'), 'Close']
                    elif offset <= -7:
                        day_price = df.loc[df['Date'] == (earnings_day + pd.DateOffset(days=offset - 5)).strftime('%Y-%m-%d'), 'Close']

            else:
                day_price = df.loc[df['Date'] == date_offset, 'Open']

            if not day_price.empty:
                day_price = day_price.iloc[0]
                if offset <= 0:
                    price_diff = (earnings_close - day_price) / earnings_close * 100
                else:
                    price_diff = (day_price - earnings_close) / day_price * 100
                row[offset] = round(price_diff, 2)
            else:
                row[offset] = None

        earnings_diffs.append(row)

    return earnings_diffs


# Function to calculate strength based on positive and negative differences
def calculate_strength_row(earnings_diffs):
    strength_list = []
    for entry in earnings_diffs:
        changes = [entry[key] for key in entry if key != 'earnings_day']
        positive_count = sum(1 for change in changes if change and change > 0)
        negative_count = sum(1 for change in changes if change and change < 0)
        strength = positive_count - negative_count
        strength_list.append(strength)
    return strength_list


# Function to calculate cumulative strength based on positive and negative differences
def calculate_cumulative_strength_col(earnings_diffs):
    cumulative_strength = {offset: 0 for offset in [-42, -35, -28, -21, -14, -7, 0, 7, 14, 21, 28, 35, 42]}

    for entry in earnings_diffs:
        for offset in cumulative_strength.keys():
            change = entry[offset]
            if change is not None:
                if change > 0:
                    cumulative_strength[offset] += 1  # Increment positive count
                elif change < 0:
                    cumulative_strength[offset] -= 1  # Decrement for negative change

    return cumulative_strength



def calculate_price_diff_for_earnings_day(earnings_day, df, today, x_range, y_range):
    row = {'earnings_day': earnings_day}

    # Skip future dates
    if earnings_day > today:
        return row

    # Cache for lookup of prices by date
    price_cache = {}

    for x in x_range:
        buy_date = (earnings_day + pd.DateOffset(days=x)).strftime('%Y-%m-%d')

        if buy_date not in price_cache:
            buy_day = df.loc[df['Date'] == buy_date, 'Close']
            price_cache[buy_date] = buy_day.iloc[0] if not buy_day.empty else None

        buy_price = price_cache[buy_date]

        if buy_price is None:
            continue

        for y in y_range:
            # Ensure y is greater than x to maintain the buy before sell logic
            if y <= x:
                continue

            sell_date = (earnings_day + pd.DateOffset(days=y)).strftime('%Y-%m-%d')

            if sell_date not in price_cache:
                sell_day = df.loc[df['Date'] == sell_date, 'Close']
                price_cache[sell_date] = sell_day.iloc[0] if not sell_day.empty else None

            sell_price = price_cache[sell_date]

            if sell_price is None:
                row[f'day_{x}_{y}'] = None
            else:
                # Calculate percentage difference
                price_diff = (sell_price - buy_price) / buy_price * 100
                row[f'day_{x}_{y}'] = round(price_diff, 2)

    return row


def calculate_price_differences_all_combinations_norepeat(df, df_earnings):
    today = pd.Timestamp('today')
    x_range = range(-71, 70)
    y_range = range(-70, 71)

    all_combination_earnings_diffs = []

    # Use ProcessPoolExecutor to parallelize across earnings days
    with ProcessPoolExecutor() as executor:
        results = executor.map(
            calculate_price_diff_for_earnings_day,
            df_earnings,
            [df] * len(df_earnings),
            [today] * len(df_earnings),
            [x_range] * len(df_earnings),
            [y_range] * len(df_earnings)
        )

        # Collect results
        for result in results:
            all_combination_earnings_diffs.append(result)

    return all_combination_earnings_diffs


# Helper function to process a chunk of data
def process_chunk(chunk):
    cumulative_strength = defaultdict(int)
    cumulative_movement = defaultdict(float)
    count = defaultdict(int)

    for entry in chunk:
        for key, value in entry.items():
            if key.startswith('day_') and value is not None:
                if value > 0:
                    cumulative_strength[key] += 1
                elif value < 0:
                    cumulative_strength[key] -= 1

                cumulative_movement[key] += value
                count[key] += 1

    return cumulative_strength, cumulative_movement, count


# Main function with parallel processing
def calculate_cumulative_strength_col_big_data(all_combinations, num_workers=4):
    # Split data into chunks
    chunk_size = len(all_combinations) // num_workers
    chunks = [all_combinations[i:i + chunk_size] for i in range(0, len(all_combinations), chunk_size)]

    cumulative_strength = defaultdict(int)
    cumulative_movement = defaultdict(float)
    count = defaultdict(int)

    # Process each chunk in parallel
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(process_chunk, chunk) for chunk in chunks]

        for future in as_completed(futures):
            chunk_strength, chunk_movement, chunk_count = future.result()

            # Merge chunk results into overall results
            for key in chunk_strength:
                cumulative_strength[key] += chunk_strength[key]
                cumulative_movement[key] += chunk_movement[key]
                count[key] += chunk_count[key]

    # Calculate average percentage movement
    average_movement = {k: cumulative_movement[k] / count[k] if count[k] > 0 else 0 for k in cumulative_movement}

    # Create a DataFrame for easy sorting
    results_df = pd.DataFrame({
        'day_combination': cumulative_strength.keys(),
        'strength': cumulative_strength.values(),
        'average_return': average_movement.values()
    })

    # Sort by strength or average_return and get the top combinations
    top_df = results_df.nlargest(100, 'average_return')  # Replace 100 with desired dynamic input

    return top_df






