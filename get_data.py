import yfinance as yf
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
from datetime import datetime


def get_stock_price(ticker):
    """
        Gets Historical Price Data for a specific Stock ticker
    """

    ticker_data = yf.Ticker(ticker)

    # Gets the data since the date below
    ticker_df = ticker_data.history(start="1998-01-01")

    ticker_df.reset_index(inplace=True)
    ticker_df['Date'] = ticker_df['Date'].dt.strftime('%Y-%m-%d')

    # Removing columns 'Dividends', 'Stock Splits'
    ticker_df = ticker_df.drop(['Dividends', 'Stock Splits'], axis=1)

    # returns the data in a dataframe format
    return ticker_df


def get_historical_stock_earning_days_EDGAR(ticker, ss):
    SEC_HEADERS = {
        'user-agent': 'Edgar oit@sec.gov',
        'accept-encoding': 'gzip, deflate',
        'host': 'www.sec.gov',
        'referer': 'https://www.sec.gov/',
        'cache-control': 'no-cache',
        'connection': 'close'
        # 'connection': 'keep-alive'
    }

    master_list = []
    endpoint = r"https://www.sec.gov/cgi-bin/browse-edgar"
    for filling_type in ['10-q', '10-k']:
        if '10-k' == filling_type:
            sample_size = ss // 4
        else:
            sample_size = ss // 4 * 3

        param_dict = {'action': 'getcompany',
                      'ticker': ticker,
                      'type': filling_type,
                      'owner': 'exclude',
                      'start': '',
                      'output': '',
                      'count': 100}

        response = requests.get(url=endpoint, params=param_dict, headers=SEC_HEADERS)
        soup = BeautifulSoup(response.content, 'html.parser')

        doc_table = soup.find_all('table', class_='tableFile2')

        for row in doc_table[0].find_all('tr')[:sample_size + 1]:
            # find all the columns
            cols = row.find_all('td')
            # if there are no columns move on to the next row.
            if len(cols) != 0:
                # grab the text
                filing_date = datetime.strptime(cols[3].text.strip(), '%Y-%m-%d').date()

                master_list.append(filing_date)

    master_list.sort(reverse=True)

    return master_list


def get_future_earning_day_yahoo_custom(ticker):
    url = f"https://finance.yahoo.com/quote/{ticker}"
    response = requests.get(url=url)

    soup = BeautifulSoup(response.content, 'html.parser')
    doc_table = soup.find_all('span', class_='value yf-11uk5vd')

    future_filing_date = ' '.join(doc_table[12].text.strip().split(' ')[0:3])
    new_date = datetime.strptime(future_filing_date, '%b %d, %Y').date()
    new_date.strftime('%Y-%m-%d')

    return new_date


def filter_earning_day(future_date, event_dates, day_t=24):
    current_date = pd.Timestamp('today').strftime('%Y-%m-%d')

    filtered_dates = event_dates[
        (event_dates < current_date) &  # Only past dates
        (
                (event_dates.month == future_date.month) |
                (event_dates.month == (future_date + pd.DateOffset(days=day_t)).month) |
                (event_dates.month == (future_date - pd.DateOffset(days=day_t)).month)
        )
        ]

    return filtered_dates


def get_stock_ex_dividend_days(ticker, ss):
    """
          Retrieves n ex_dividend days and the reported data for them,
          ss - stands for Sample Size

          !!! Missing feature we need!!!
          Get the next Ex-Date
    """
    # Low priority spaghetti code to get a future date
    future_date = (pd.Timestamp('today') + pd.DateOffset(years=1)).strftime('%Y-%m-%d')

    ticker_data = yf.Ticker(ticker)

    # Getting all passed ex_dividends dates
    df = ticker_data.get_dividends().to_frame()

    df.reset_index(inplace=True)

    # Formatting the date
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')

    # Filtering data from 1999-12-31
    df = df.loc[(df['Date'] > '1999-12-31') & (df['Date'] < future_date)]

    df = df.iloc[::-1]
    # if sr < len(df):
    df = df.iloc[0:ss]

    df.reset_index(inplace=True)

    df = df.drop(['Dividends'], axis=1)

    df = pd.to_datetime(df['Date'])

    return df


# Calculate percentage change for days
def calculate_price_differences(df, df_date, dt=None):
    """
       Calculating the price difference for the earning and for the ex-date events
    """

    # List for the earnings table
    time_offsets = [-42, -35, -28, -21, -14, -7, 0, 7, 14, 21, 28, 35, 42]

    # Checking if we have a Dividend flag raised. If so we overwrite the List
    if dt == 'dividend':
        time_offsets = [-84, -77, -70, -63, -56, -49, -42, -35, -28, -21, -14, -7, 0, ]
    diffs = []
    # trading_days = set(df['Date'])  # Set of all trading days

    today = pd.Timestamp('today')  # Get today's date for future date check

    # Looping over every event date
    for day in df_date:
        if day > today:  # Checking if the event day has passed
            continue

        day_close = df.loc[df['Date'] == day.strftime('%Y-%m-%d'), 'Close']  # Getting the Close price for the event day.     !!! In the future we could change to a different price, or be dynamic.
        if day_close.empty:
            continue

        row = {}
        day_close = day_close.iloc[0]
        row['day'] = day

        # We loop over all the offsets we got based on the event
        for offset in time_offsets:
            date_offset = (day + pd.DateOffset(days=offset)).strftime('%Y-%m-%d')
            if offset != 0:  # If the day we are comparing is different from the event day. We use the Closing price for the day.     !!! In the future we could change to a different price, or be dynamic.
                day_price = df.loc[df['Date'] == date_offset, 'Close']

                if day_price.empty:  # Checking if the price for the day is empty
                    pass
            else:  # Since we are checking the same day as the event day we get the Open price
                day_price = df.loc[df['Date'] == date_offset, 'Open']

            if not day_price.empty:
                day_price = day_price.iloc[0]  # Checking if the price for the day is empty. Just in case
                if offset <= 0:  # If we are comparing previous events we calculated like this     (EVENT_PRICE - BUY_PRICE) / BUY_PRICE * 100    to get the % diff
                    price_diff = (day_close - day_price) / day_close * 100
                else:  # The formula for the case where we buy on the day of the event and sell after wards we use     (SELL_PRICE - EVENT_PRICE) / EVENT_PRICE * 100    to get the % diff
                    price_diff = (day_price - day_close) / day_price * 100
                row[offset] = round(price_diff, 2)
            else:
                row[offset] = None

        diffs.append(row)

    return diffs


# Function to calculate hit point based on positive and negative differences
def calculate_hit_point_row(diffs):
    hit_point_list = []
    for entry in diffs:
        changes = [entry[key] for key in entry if key != 'day']
        positive_count = sum(1 for change in changes if change and change > 0)
        negative_count = sum(1 for change in changes if change and change < 0)
        hit_point = positive_count - negative_count
        hit_point_list.append(hit_point)
    return hit_point_list


# Function to calculate cumulative hit point based on positive and negative differences
def calculate_cumulative_hit_point_col(diffs, dt=None):
    time_offsets = [-42, -35, -28, -21, -14, -7, 0, 7, 14, 21, 28, 35, 42]

    if dt == 'dividend':
        time_offsets = [-84, -77, -70, -63, -56, -49, -42, -35, -28, -21, -14, -7, 0, ]

    cumulative_hit_point = {offset: 0 for offset in time_offsets}

    for entry in diffs:
        for offset in cumulative_hit_point.keys():
            change = entry[offset]
            if change is not None:
                if change > 0:
                    cumulative_hit_point[offset] += 1  # Increment positive count
                elif change < 0:
                    cumulative_hit_point[offset] -= 1  # Decrement for negative change

    return cumulative_hit_point


def calculate_price_diff_for_day(day, df, today, x_range, y_range):
    row = {'day': day}

    # Skip future dates
    if day > today:
        return row

    # Cache for lookup of prices by date
    price_cache = {}

    for x in x_range:
        buy_date = (day + pd.DateOffset(days=x)).strftime('%Y-%m-%d')

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

            sell_date = (day + pd.DateOffset(days=y)).strftime('%Y-%m-%d')

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


def calculate_price_differences_all_combinations_norepeat(df, df_day, future_day=True):
    today = pd.Timestamp('today')

    all_combination_diffs = []

    x_range = range(-91, -1)
    y_range = range(0, 1)

    if future_day:
        x_range = range(-91, 90)
        y_range = range(-90, 91)

    # Use ProcessPoolExecutor to parallelize across
    with ProcessPoolExecutor() as executor:
        results = executor.map(
            calculate_price_diff_for_day,
            df_day,
            [df] * len(df_day),
            [today] * len(df_day),
            [x_range] * len(df_day),
            [y_range] * len(df_day)
        )

        # Collect results
        for result in results:
            all_combination_diffs.append(result)

    return all_combination_diffs


# Main function with parallel processing
def calculate_cumulative_hit_point_col_big_data(all_combinations, ht_min=1, ht_max=181, primary_sort="hit point", secondary_sort="average return", third_sort="holding time", fourth_sort="cs", ss=12, top_n=50):
    cumulative_hit_point = {}
    cumulative_movement = {}
    count = {}
    holding_periods = {}

    if ht_min > ht_max:
        raise ValueError("The minimum holding time cannot be greater than the maximum holding time.")

    # Calculate cumulative hit point, average movement, and holding period
    for entry in all_combinations:
        for key, value in entry.items():
            if key.startswith('day_'):
                if key not in cumulative_hit_point:
                    cumulative_hit_point[key] = 0
                    cumulative_movement[key] = 0
                    count[key] = 0

                    # Extract the holding period from the key (e.g., 'day_x_y')
                    try:
                        _, x, y = key.split('_')
                        holding_period = int(y) - int(x)
                        holding_periods[key] = holding_period
                    except ValueError:
                        holding_periods[key] = None  # Default to None if parsing fails

                if value is not None:
                    # Hit point calculation
                    if value > 0:
                        cumulative_hit_point[key] += 1
                    elif value < 0:
                        cumulative_hit_point[key] -= 1

                    # Sum for average calculation
                    cumulative_movement[key] += value
                    count[key] += 1

    # Average movement calculation
    average_movement = {
        k: cumulative_movement[k] / count[k] if count[k] > 0 else 0
        for k in cumulative_movement
    }

    custom_scoring = []

    dc = list(cumulative_hit_point.keys())
    hp = list(cumulative_hit_point.values())
    ar = list(average_movement.values())
    ht = [holding_periods[k] if holding_periods[k] is not None else float('inf')
          for k in cumulative_hit_point.keys()]

    for i in range(0, len(list(cumulative_hit_point.keys()))):
        if 0 < ar[i] < 20:
            percentage_points = pow(ar[i],2) * 0.0083 - ar[i] * 0.0083
        elif ar[i] >= 20:
            percentage_points = (pow(ar[i],3) * 0.0083 - pow(ar[i],2) * 0.0083) * 0.0083
        else:
            percentage_points = - ar[i] * 0.083 - 0.83

        barney_score = ((hp[i] / ss) * 8.3) + percentage_points + (((100 / ht[i])/100) * 0.83)

        custom_scoring.append(barney_score)

    # Convert to DataFrame and include all relevant data
    results_df = pd.DataFrame({
        'day_combination': dc,
        "hit point": hp,
        'average return': ar,
        'holding time': ht,
        'cs': custom_scoring
    })

    # Filter by holding time range
    filtered_df = results_df[
        (results_df['holding time'] >= ht_min) &
        (results_df['holding time'] <= ht_max)
    ]

    # Ensure sorting columns exist in DataFrame
    valid_sort_columns = ["hit point", "average return", "holding time", "cs"]
    sort_columns = [primary_sort, secondary_sort, third_sort, fourth_sort]
    sort_columns = [col for col in sort_columns if col in valid_sort_columns]

    # Sorting order: Descending for hit point/returns, Ascending for holding_period
    ascending_order = [False if col != "holding time" else True for col in sort_columns]

    # Apply sorting
    sorted_df = filtered_df.sort_values(
        by=sort_columns,
        ascending=ascending_order
    ).head(top_n)

    return sorted_df

