import dash_bootstrap_components.themes
from dash import Dash, dcc, html, Input, Output
from dash_bootstrap_templates import load_figure_template
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly_resampler import FigureResampler
import pandas as pd
import get_data

load_figure_template("CYBORG")
app = Dash(title="Stock Analysis",
           external_stylesheets=[dash_bootstrap_components.themes.CYBORG])

app.layout = html.Div([
    # Fixed container for the ticker input

    html.Div([
        html.H4('Stock Analysis',
                style={'display': 'inline-block', 'margin-right': '10px'}
                ),

        # Stock Ticker Input
        dcc.Input(
            id="stock-ticker",
            type="text",
            placeholder="Enter stock ticker (e.g., AAPL)",
            value="AAPL",
            debounce=True,
            style={'width': '100px', 'margin-right': '25px', 'display': 'inline-block', 'verticalAlign': 'middle'}
        )
    ], style={
        'position': 'fixed', 'top': '0', 'left': '50%', 'width': '100%', 'transform': 'translateX(-50%)', 'zIndex': '1000', 'backgroundColor': 'grey', 'padding': '12px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
        'boxShadow': '0 4px 8px rgba(0, 0, 0, 0.1)',
    }),

    dcc.Dropdown(
        id="select-event-dropdown",
        options=[
            {"label": "Earnings", "value": "earnings"},
            {"label": "Dividend", "value": "dividend"}
        ],
        placeholder="Select Event Type", clearable=False,
        style={'background-color': 'grey', 'color': 'black', 'margin': '10px 0', 'width': '150px'}
    ),

    # Input fields for start and end days
    dcc.Input(id="start-day-input", type="number", placeholder="x (Start Days)", value=0, style={'margin-right': '10px'}),
    dcc.Input(id="end-day-input", type="number", placeholder="y (End Days)", value=0, style={'margin-right': '10px'}),

    dcc.Store(id="stock-data-store"),  # Store for retrieved stock data

    dcc.Loading(
        id="loading-1", type="circle",
        children=[dcc.Graph(id="stock-chart", config={"displayModeBar": False, "autosizable": True, "scrollZoom": True}, style={'visibility': 'hidden'})]  # Hidden by default
    ),

    # Earnings and Dividend Sections in a Row
    html.Div([
        # Earnings Section
        html.Div([
            html.H5("Earnings", style={'textAlign': 'center', 'margin-bottom': '10px'}),

            html.Div([
                html.P("Sorting Type", style={'textAlign': 'center', 'margin-right': '20px', 'width': '175px'}),
                html.P("Quantity", style={'textAlign': 'center', 'margin-right': '20px', 'width': '120px'}),
                html.P("Sample Size", style={'textAlign': 'center', 'margin-right': '20px', 'width': '120px'}),
                html.P("Holding Time Min", style={'textAlign': 'center', 'margin-right': '20px', 'width': '110px'}),
                html.P("Holding Time Max", style={'textAlign': 'center', 'width': '110px'})
            ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center','margin-bottom': '10px'}),


            html.Div([
                dcc.Dropdown(
                    id="sort-type-dropdown",
                    options=[
                        {"label": "HP/AR/HT", "value": "hp_ar_ht"},
                        {"label": "HP/HT/AR", "value": "hp_ht_ar"},
                        {"label": "AR/HP/HT", "value": "ar_hp_ht"},
                        {"label": "AR/HT/HP", "value": "ar_ht_hp"},
                        {"label": "HT/AR/HP", "value": "ht_ar_hp"},
                        {"label": "HT/HP/AR", "value": "ht_hp_ar"},
                        {"label": "CS", "value": "cs"},

                    ],
                    value="hp_ar_ht",   placeholder="Select Sorting Type",   clearable=False,
                    style={'width': '175px', 'color': 'black', 'margin-right': '20px'}
                ),
                dcc.Input(
                    id="top-n-input", type="number", placeholder="Top N", value=25, min=1, max=1000,
                    style={'width': '120px', 'margin-right': '20px'}
                ),
                dcc.Input(
                    id="sample-n-rate", type="number",placeholder="Sample Rate",  value=12,  min=1,  max=100,
                    style={'width': '120px', 'margin-right': '20px'}
                ),
                dcc.Input(
                    id="hold-time-min-n-input", type="number", placeholder="Time min", value=1, min=1, max=180,
                    style={'width': '110px', 'margin-right': '20px'}
                ),
                dcc.Input(
                    id="hold-time-max-n-input", type="number", placeholder="Time max", value=30, min=2, max=181,
                    style={'width': '110px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'margin-bottom': '10px'}),

            dcc.Loading(
                id="loading-Earnings-1", type="circle",
                children=[
                    dcc.Graph(
                        id="all-combinations-container",
                        config={"displayModeBar": False},
                        style={'visibility': 'hidden'}
                    )
                ]
            ),
            dcc.Loading(
                id="loading-Earnings-2", type="circle",
                children=[
                    dcc.Graph(
                        id="all-combinations-container-quarterly",
                        config={"displayModeBar": False},
                        style={'visibility': 'hidden'}
                    )
                ]
            ),
            dcc.Loading(
                id="loading-Earnings-3", type="circle",
                children=[
                    html.Div(id="earnings-table-container", style={'visibility': 'hidden'})
                ]
            ),
        ], style={'flex': '1', 'padding': '10px', 'minWidth': '1000px'}),

        # Dividend Section
        html.Div([
            html.H5("Dividend", style={'textAlign': 'center', 'margin-bottom': '10px'}),

            html.Div([
                html.P("Sorting Type", style={'textAlign': 'center', 'margin-right': '20px', 'width': '175px'}),
                html.P("Quantity", style={'textAlign': 'center', 'margin-right': '20px', 'width': '120px'}),
                html.P("Sample Size", style={'textAlign': 'center', 'margin-right': '20px', 'width': '120px'}),
                html.P("Holding Time Min", style={'textAlign': 'center', 'margin-right': '20px', 'width': '110px'}),
                html.P("Holding Time Max", style={'textAlign': 'center', 'width': '110px'})
            ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'margin-bottom': '10px'}),

            html.Div([
                dcc.Dropdown(
                    id="sort-type-dropdown_dividend",
                    options=[
                        {"label": "HP/AR/HT", "value": "hp_ar_ht"},
                        {"label": "HP/HT/AR", "value": "hp_ht_ar"},
                        {"label": "AR/HP/HT", "value": "ar_hp_ht"},
                        {"label": "AR/HT/HP", "value": "ar_ht_hp"},
                        {"label": "HT/AR/HP", "value": "ht_ar_hp"},
                        {"label": "HT/HP/AR", "value": "ht_hp_ar"},
                        {"label": "CS", "value": "cs"},

                    ],
                    value="hp_ar_ht", placeholder="Select Sorting Type", clearable=False,
                    style={'width': '175px', 'color': 'black', 'margin-right': '20px'}
                ),
                dcc.Input(
                    id="top-n-input_dividend", type="number", placeholder="Top N", value=25, min=1, max=1000,
                    style={'width': '120px', 'margin-right': '20px'}
                ),
                dcc.Input(
                    id="sample-n-rate_dividend", type="number", placeholder="Sample Rate", value=12, min=1, max=100,
                    style={'width': '120px', 'margin-right': '20px'}
                ),
                dcc.Input(
                    id="hold-time-min-n-input_dividend", type="number", placeholder="Time min", value=1, min=1,  max=180,
                    style={'width': '110px', 'margin-right': '20px'}
                ),
                dcc.Input(
                    id="hold-time-max-n-input_dividend", type="number", placeholder="Time max", value=30, min=2, max=181,
                    style={'width': '110px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'margin-bottom': '10px'}),

            dcc.Loading(
                id="loading-4", type="circle",
                children=[
                    dcc.Graph(
                        id="all-combinations-container_dividend",
                        config={"displayModeBar": False},
                        style={'visibility': 'hidden'}
                    )
                ]
            ),
            dcc.Loading(
                id="loading-5", type="circle",
                children=[
                    html.Div(id="dividend-table-container", style={'visibility': 'hidden'})
                ]
            ),
        ], style={'flex': '1', 'padding': '10px', 'minWidth': '1000px'})

    ], style={'display': 'flex', 'flex-wrap': 'wrap', 'gap': '10px', 'marginTop': '20px'})

], style={'paddingTop': '80px', 'paddingLeft': '20px', 'paddingRight': '20px'})


@app.callback(
    Output("stock-data-store", "data"),
    Input("stock-ticker", "value"),
    Input("sample-n-rate", "value"),
    Input("sample-n-rate_dividend", "value")
)
def retrieve_stock_data(value, sr_earning, sr_ex_date):
    # Fetch the stock price and earnings data once
    value = value.upper()
    stock_price = get_data.get_stock_price(value)
    # stock_earning_days = get_data.get_stock_earning_days(value, sr_earning)
    stock_earning_days = get_data.get_historical_stock_earning_days_EDGAR(value, sr_earning)
    future_earning_date = get_data.get_future_earning_day_yahoo_custom(value)
    stock_ex_dividend_days = get_data.get_stock_ex_dividend_days(value, sr_ex_date)

    # Store both dataframes as dictionaries
    return {
        "stock_price": stock_price.to_dict("records"),
        # "stock_earning_days": stock_earning_days.tolist(),
        "stock_earning_days": stock_earning_days,
        "future_earning_date": future_earning_date,
        "stock_ex_dividend_days": stock_ex_dividend_days.tolist(),
        "stock_ticker": value
    }


@app.callback(
    Output("stock-chart", "figure"),
    Output("stock-chart", "style"),
    Output("select-event-dropdown", "options"),
    Input("stock-data-store", "data"),
    Input("select-event-dropdown", "value"),
    Input("start-day-input", "value"),
    Input("end-day-input", "value"),

)
def display_graph(data, selected_event, start_days, end_days):
    if data is None:
        return None, {"visibility": "hidden"}, []

    # Prepare data
    stock_price = pd.DataFrame(data["stock_price"])

    data["stock_earning_days"].insert(0, data["future_earning_date"])
    stock_earning_days = pd.to_datetime(data["stock_earning_days"])
    # stock_future_earning_day = pd.to_datetime(data["future_earning_date"])
    stock_ex_dividend_days = pd.to_datetime(data["stock_ex_dividend_days"])

    stock_ticker = data["stock_ticker"]

    # Create the base figure with historical stock data
    fig = FigureResampler(go.Figure(make_subplots(specs=[[{"secondary_y": True}]])))
    fig.add_traces(go.Scatter(x=stock_price['Date'], y=(stock_price['Open'] + stock_price['Close']) / 2), max_n_samples=[3000], secondary_ys=[True])

    # Generate dropdown options based on available data
    options = []
    if not stock_earning_days.empty:
        options.append({"label": "Earnings", "value": "earnings"})

    if not stock_ex_dividend_days.empty:
        options.append({"label": "Dividend", "value": "dividend"})

    # Only proceed with line drawing if all required inputs are provided and valid
    if selected_event and start_days is not None and end_days is not None:
        # Validation: Ensure start_days <= end_days, and they are not equal
        if start_days < end_days:
            # Select event dates based on user selection
            event_dates = stock_earning_days if selected_event == "earnings" else stock_ex_dividend_days

            # Draw vertical lines only if the dates exist in the stock data
            for event_date in event_dates:
                start_line_date = event_date + pd.DateOffset(days=start_days)
                end_line_date = event_date + pd.DateOffset(days=end_days)

                fig.add_vline(x=event_date, line_width=1, line_dash="dash", line_color="grey", secondary_y=True)

                # if start_line_date in stock_price['Date'].values:
                fig.add_vline(x=start_line_date, line_width=1, line_dash="dot", line_color="green", secondary_y=True)

                # if end_line_date in stock_price['Date'].values:
                fig.add_vline(x=end_line_date, line_width=1, line_dash="dot", line_color="red", secondary_y=True)

    # Update layout to enhance visibility
    fig.update_layout(
        title=f'Historical data for {stock_ticker}',
        height=650,
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date"
        )
    )

    return fig, {"visibility": "visible"}, options


def style_cell(diff):
    if diff is None:
        return {"color": "black"}

    if diff < -20:
        return {"backgroundColor": "#b30000 ", "color": "white", 'border': '1px solid black', "marginLeft": "auto", "text-align": "center", "marginRight": "auto"}  # Dark Red
    elif -20 <= diff < -10:
        return {"backgroundColor": "#cc3300 ", "color": "white", 'border': '1px solid black', "marginLeft": "auto", "text-align": "center", "marginRight": "auto"}  # Tomato
    elif -10 <= diff < -5:
        return {"backgroundColor": "#e65c00 ", "color": "black", 'border': '1px solid black', "marginLeft": "auto", "text-align": "center", "marginRight": "auto"}  # Light Coral
    elif -5 <= diff < 0:
        return {"backgroundColor": "#ff944d", "color": "black", 'border': '1px solid black', "marginLeft": "auto", "text-align": "center", "marginRight": "auto"}  # Gold
    elif 0 <= diff < 5:
        return {"backgroundColor": "#99cc66", "color": "black", 'border': '1px solid black', "marginLeft": "auto", "text-align": "center", "marginRight": "auto"}  # Green Yellow
    elif 5 <= diff < 10:
        return {"backgroundColor": "#66b266", "color": "white", 'border': '1px solid black', "marginLeft": "auto", "text-align": "center", "marginRight": "auto"}  # Lime Green
    elif 10 <= diff < 20:
        return {"backgroundColor": "#4d994d", "color": "white", 'border': '1px solid black', "marginLeft": "auto", "text-align": "center", "marginRight": "auto"}  # Green
    elif 20 <= diff:
        return {"backgroundColor": "#267326", "color": "white", 'border': '1px solid black', "marginLeft": "auto", "text-align": "center", "marginRight": "auto"}  # Dark Green


def style_other():
    return {'border': '5px solid black', 'padding': '7px', "margin": "auto", "text-align": "center", "font-weight": "bold", "font-size": "20px"}


# Callback to update the earnings table
@app.callback(
    Output("earnings-table-container", "children"),
    Input("stock-data-store", "data")
)
def update_table_earnings(data):
    if data is None:
        return html.Div("Loading data...")  # Return nothing if no data is available

    stock_price = pd.DataFrame(data["stock_price"])
    stock_earning_days = pd.to_datetime(data["stock_earning_days"])

    earnings_diffs = get_data.calculate_price_differences(stock_price, stock_earning_days)

    # Calculate hit point
    hit_point_list = get_data.calculate_hit_point_row(earnings_diffs)
    cumulative_hit_point = get_data.calculate_cumulative_hit_point_col(earnings_diffs)

    # Create the table header
    table_header = html.Thead(html.Tr([
        html.Th("Time Frame", style={'border': '5px solid black', 'padding': '25px', "marginLeft": "auto"}),
        html.Th("42d Before", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("35d Before", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("28d Before", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("21d Before", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("14d Before", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("7d Before", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("On Earnings Day", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("7d After", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("14d After", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("21d After", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("28d After", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("35d After", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("42d After", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("Hit point", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"})
    ]))

    # Create the table body with color-coded cells
    table_body = html.Tbody([
                                html.Tr([
                                    html.Td(diff['day'].strftime('%Y-%m-%d'), style={'border': '5px solid black', 'padding': '2px', "marginLeft": "auto", "text-align": "center"}),
                                    html.Td(diff[-42], style=style_cell(diff[-42])),
                                    html.Td(diff[-35], style=style_cell(diff[-35])),
                                    html.Td(diff[-28], style=style_cell(diff[-28])),
                                    html.Td(diff[-21], style=style_cell(diff[-21])),
                                    html.Td(diff[-14], style=style_cell(diff[-14])),
                                    html.Td(diff[-7], style=style_cell(diff[-7])),
                                    html.Td(diff[0], style=style_cell(diff[0])),
                                    html.Td(diff[7], style=style_cell(diff[7])),
                                    html.Td(diff[14], style=style_cell(diff[14])),
                                    html.Td(diff[21], style=style_cell(diff[21])),
                                    html.Td(diff[28], style=style_cell(diff[28])),
                                    html.Td(diff[35], style=style_cell(diff[35])),
                                    html.Td(diff[42], style=style_cell(diff[42])),
                                    html.Td(hit_point_list[index], style=style_other())  # Add hit point value here
                                ]) for index, diff in enumerate(earnings_diffs)
                            ] + [
                                html.Tr([
                                    "Cumulative Changes",
                                    html.Td(cumulative_hit_point[-42], style=style_other()),
                                    html.Td(cumulative_hit_point[-35], style=style_other()),
                                    html.Td(cumulative_hit_point[-28], style=style_other()),
                                    html.Td(cumulative_hit_point[-21], style=style_other()),
                                    html.Td(cumulative_hit_point[-14], style=style_other()),
                                    html.Td(cumulative_hit_point[-7], style=style_other()),
                                    html.Td(cumulative_hit_point[0], style=style_other()),
                                    html.Td(cumulative_hit_point[7], style=style_other()),
                                    html.Td(cumulative_hit_point[14], style=style_other()),
                                    html.Td(cumulative_hit_point[21], style=style_other()),
                                    html.Td(cumulative_hit_point[28], style=style_other()),
                                    html.Td(cumulative_hit_point[35], style=style_other()),
                                    html.Td(cumulative_hit_point[42], style=style_other())
                                ])
                            ])

    # Return the full table (header + body)
    return html.Table([table_header, table_body], style={"visibility": "visible", "width": "85%", "padding": "1% 1% 1% 1%", "borderCollapse": "collapse", "border": "2px solid black", "marginTop": "10px", "marginLeft": "auto", "marginRight": "auto"})


@app.callback(
    Output("all-combinations-container", "figure"),
    Output("all-combinations-container", "style"),
    Input("stock-data-store", "data"),
    Input("sort-type-dropdown", "value"),
    Input("top-n-input", "value"),
    Input("hold-time-min-n-input", "value"),
    Input("hold-time-max-n-input", "value")
)
def update_all_combinations_earnings(data, sort_type, top_n, ht_min, ht_max):
    if data is None:
        return go.Figure(), {"visibility": "hidden"}  # Return empty figure if no data is available

    # Convert to DataFrame and Parse Ticker
    stock_price = pd.DataFrame(data["stock_price"])
    stock_earning_days = pd.to_datetime(data["stock_earning_days"])
    stock_ticker = data["stock_ticker"]
    sort_columns = []

    # Calculate price differences and cumulative hit point
    all_combinations = get_data.calculate_price_differences_all_combinations_norepeat(stock_price, stock_earning_days)

    # Use Dynamic Sorting and Limit Top N Entries
    primary_sort = sort_type or "s_ar_hp"
    # Adjust sorting logic based on the selected primary sort type
    match primary_sort:
        case "hp_ar_ht":
            sort_columns = ["hit point", "average return", "holding time", "cs"]
        case "hp_ht_ar":
            sort_columns = ["hit point", "holding time", "average return", "cs"]
        case "ar_hp_ht":
            sort_columns = ["average return", "hit point", "holding time", "cs"]
        case "ar_ht_hp":
            sort_columns = ["average return", "holding time", "hit point", "cs"]
        case "ht_ar_hp":
            sort_columns = ["holding time", "average return", "hit point", "cs"]
        case "ht_hp_ar":
            sort_columns = ["holding time", "hit point", "average return", "cs"]
        case "cs":
            sort_columns = ["cs", "holding time", "hit point", "average return"]

    # Call the data processing function with dynamic sorting
    top_df = get_data.calculate_cumulative_hit_point_col_big_data(
        all_combinations,
        primary_sort=sort_columns[0],
        secondary_sort=sort_columns[1],
        third_sort=sort_columns[2],
        fourth_sort=sort_columns[3],
        top_n=top_n,
        ht_min=ht_min,
        ht_max=ht_max
    )

    # Extract data for plotting
    days = top_df['day_combination']
    hit_point_values = top_df['hit point']
    average_values = top_df['average return']
    holding_time = top_df['holding time']
    fourth_sort = top_df['cs']

    # Create Bar Chart without Tools
    fig = go.Figure()

    # Add cumulative hit point bar
    fig.add_trace(go.Bar(
        x=days,
        y=hit_point_values,
        name='Cumulative Hit Point',
        marker_color='green'
    ))

    # Add average return as a secondary y-axis
    fig.add_trace(go.Bar(
        x=days,
        y=average_values,
        name='Average % Return',
        marker_color='blue'
    ))
    # Add average return as a secondary y-axis
    fig.add_trace(go.Bar(
        x=days,
        y=holding_time,
        name='Holding Time',
        marker_color='red'
    ))

    fig.add_trace(go.Bar(
        x=days,
        y=fourth_sort,
        name='Custom scoring',
        marker_color='pink'
    ))

    # Update layout with two y-axes
    fig.update_layout(
        height=750,
        title=f'Top {top_n} Days by {sort_columns[0].capitalize()}, {sort_columns[1].capitalize()} and {sort_columns[2].capitalize()} for {stock_ticker}',
        yaxis=dict(title='Cumulative hit point'),
        xaxis_title='Day Combination',
        barmode='group'
    )

    return fig, {"visibility": "visible"}


@app.callback(
    Output("all-combinations-container-quarterly", "figure"),
    Output("all-combinations-container-quarterly", "style"),
    Input("stock-data-store", "data"),
    Input("sort-type-dropdown", "value"),
    Input("top-n-input", "value"),
    Input("hold-time-min-n-input", "value"),
    Input("hold-time-max-n-input", "value")
)
def update_all_combinations_earnings_based_on_quarterly_results(data, sort_type, top_n, ht_min, ht_max):
    if data is None:
        return go.Figure(), {"visibility": "hidden"}  # Return empty figure if no data is available

    # Convert to DataFrame and Parse Ticker
    stock_ticker = data["stock_ticker"]
    stock_price = pd.DataFrame(data["stock_price"])
    stock_earning_days = pd.to_datetime(data["stock_earning_days"])
    stock_future_earning_day = pd.to_datetime(data["future_earning_date"])
    sort_columns = []

    stock_earning_days_filtered = get_data.filter_earning_day(stock_future_earning_day, stock_earning_days)

    # Calculate price differences and cumulative hit point
    all_combinations_quarterly = get_data.calculate_price_differences_all_combinations_norepeat(stock_price, stock_earning_days_filtered)

    # Use Dynamic Sorting and Limit Top N Entries
    primary_sort = sort_type or "s_ar_hp"
    # Adjust sorting logic based on the selected primary sort type
    match primary_sort:
        case "hp_ar_ht":
            sort_columns = ["hit point", "average return", "holding time", "cs"]
        case "hp_ht_ar":
            sort_columns = ["hit point", "holding time", "average return", "cs"]
        case "ar_hp_ht":
            sort_columns = ["average return", "hit point", "holding time", "cs"]
        case "ar_ht_hp":
            sort_columns = ["average return", "holding time", "hit point", "cs"]
        case "ht_ar_hp":
            sort_columns = ["holding time", "average return", "hit point", "cs"]
        case "ht_hp_ar":
            sort_columns = ["holding time", "hit point", "average return", "cs"]
        case "cs":
            sort_columns = ["cs", "holding time", "hit point", "average return"]

    # Call the data processing function with dynamic sorting
    top_df = get_data.calculate_cumulative_hit_point_col_big_data(
        all_combinations_quarterly,
        primary_sort=sort_columns[0],
        secondary_sort=sort_columns[1],
        third_sort=sort_columns[2],
        fourth_sort=sort_columns[3],
        top_n=top_n,
        ht_min=ht_min,
        ht_max=ht_max
    )

    # Extract data for plotting
    days = top_df['day_combination']
    hit_point_values = top_df['hit point']
    average_values = top_df['average return']
    holding_time = top_df['holding time']
    fourth_sort = top_df['cs']

    # Create Bar Chart without Tools
    fig = go.Figure()

    # Add cumulative hit point bar
    fig.add_trace(go.Bar(
        x=days,
        y=hit_point_values,
        name='Cumulative Hit Point',
        marker_color='green'
    ))

    # Add average return as a secondary y-axis
    fig.add_trace(go.Bar(
        x=days,
        y=average_values,
        name='Average % Return',
        marker_color='blue'
    ))

    fig.add_trace(go.Bar(
        x=days,
        y=holding_time,
        name='Holding Time',
        marker_color='red'
    ))

    fig.add_trace(go.Bar(
        x=days,
        y=fourth_sort,
        name='Custom scoring',
        marker_color='pink'
    ))

    # Update layout with two y-axes
    fig.update_layout(
        height=750,
        title=f'Top {top_n} Days by {sort_columns[0].capitalize()}, {sort_columns[1].capitalize()} and {sort_columns[2].capitalize()} for {stock_ticker}',
        yaxis=dict(title='Cumulative Hit Point'),
        xaxis_title='Day Combination',
        barmode='group'
    )

    return fig, {"visibility": "visible"}


# Callback to update the dividend table
@app.callback(
    Output("dividend-table-container", "children"),
    Input("stock-data-store", "data")
)
def update_table_dividend(data):
    if data is None:
        return html.Div("Loading data...")  # Return nothing if no data is available

    stock_price = pd.DataFrame(data["stock_price"])
    stock_ex_dividend_days = pd.to_datetime(data["stock_ex_dividend_days"])

    ex_dividend_diffs = get_data.calculate_price_differences(stock_price, stock_ex_dividend_days, 'dividend')

    # Calculate hit point
    hit_point_list = get_data.calculate_hit_point_row(ex_dividend_diffs)
    cumulative_hit_point = get_data.calculate_cumulative_hit_point_col(ex_dividend_diffs, 'dividend')

    # Create the table header
    table_header = html.Thead(html.Tr([
        html.Th("Time Frame", style={'border': '5px solid black', 'padding': '25px', "marginLeft": "auto"}),
        html.Th("84d Before", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("77d Before", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("70d Before", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("63d Before", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("56d Before", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("49d Before", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("42d Before", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("35d Before", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("28d Before", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("21d Before", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("14d Before", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("7d Before", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("On Ex-Dividend Day", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"}),
        html.Th("Hit point", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"})
    ]))

    # Create the table body with color-coded cells
    table_body = html.Tbody([
                                html.Tr([
                                    html.Td(diff['day'].strftime('%Y-%m-%d'), style={'border': '5px solid black', 'padding': '2px', "marginLeft": "auto", "text-align": "center"}),
                                    html.Td(diff[-84], style=style_cell(diff[-84])),
                                    html.Td(diff[-77], style=style_cell(diff[-77])),
                                    html.Td(diff[-70], style=style_cell(diff[-70])),
                                    html.Td(diff[-63], style=style_cell(diff[-63])),
                                    html.Td(diff[-56], style=style_cell(diff[-56])),
                                    html.Td(diff[-49], style=style_cell(diff[-49])),
                                    html.Td(diff[-42], style=style_cell(diff[-42])),
                                    html.Td(diff[-35], style=style_cell(diff[-35])),
                                    html.Td(diff[-28], style=style_cell(diff[-28])),
                                    html.Td(diff[-21], style=style_cell(diff[-21])),
                                    html.Td(diff[-14], style=style_cell(diff[-14])),
                                    html.Td(diff[-7], style=style_cell(diff[-7])),
                                    html.Td(diff[0], style=style_cell(diff[0])),
                                    html.Td(hit_point_list[index], style=style_other())  # Add hit point value here
                                ]) for index, diff in enumerate(ex_dividend_diffs)
                            ] + [
                                html.Tr([
                                    "Cumulative Changes",
                                    html.Td(cumulative_hit_point[-84], style=style_other()),
                                    html.Td(cumulative_hit_point[-77], style=style_other()),
                                    html.Td(cumulative_hit_point[-70], style=style_other()),
                                    html.Td(cumulative_hit_point[-63], style=style_other()),
                                    html.Td(cumulative_hit_point[-56], style=style_other()),
                                    html.Td(cumulative_hit_point[-49], style=style_other()),
                                    html.Td(cumulative_hit_point[-42], style=style_other()),
                                    html.Td(cumulative_hit_point[-35], style=style_other()),
                                    html.Td(cumulative_hit_point[-28], style=style_other()),
                                    html.Td(cumulative_hit_point[-21], style=style_other()),
                                    html.Td(cumulative_hit_point[-14], style=style_other()),
                                    html.Td(cumulative_hit_point[-7], style=style_other()),
                                    html.Td(cumulative_hit_point[0], style=style_other()),
                                ])
                            ])

    # Return the full table (header + body)
    return html.Table([table_header, table_body], style={"visibility": "visible", "width": "85%", "padding": "1% 1% 1% 1%", "borderCollapse": "collapse", "border": "2px solid black", "marginTop": "10px", "marginLeft": "auto", "marginRight": "auto"})


@app.callback(
    Output("all-combinations-container_dividend", "figure"),
    Output("all-combinations-container_dividend", "style"),
    Input("stock-data-store", "data"),
    Input("sort-type-dropdown_dividend", "value"),
    Input("top-n-input_dividend", "value"),
    Input("hold-time-min-n-input_dividend", "value"),
    Input("hold-time-max-n-input_dividend", "value")
)
def update_all_combinations_dividend(data, sort_type, top_n, ht_min, ht_max):
    if data is None:
        return go.Figure(), {"visibility": "hidden"}  # Return empty figure if no data is available

    # Convert to DataFrame and Parse Ticker
    stock_price = pd.DataFrame(data["stock_price"])
    stock_ex_dividend_days = pd.to_datetime(data["stock_ex_dividend_days"])
    stock_ticker = data["stock_ticker"]
    sort_columns = []

    # Calculate price differences and cumulative hit point
    all_combinations = get_data.calculate_price_differences_all_combinations_norepeat(stock_price, stock_ex_dividend_days, False)

    # Use Dynamic Sorting and Limit Top N Entries
    primary_sort = sort_type or "s_ar_hp"
    # Adjust sorting logic based on the selected primary sort type
    match primary_sort:
        case "hp_ar_ht":
            sort_columns = ["hit point", "average return", "holding time","cs"]
        case "hp_ht_ar":
            sort_columns = ["hit point", "holding time", "average return","cs"]
        case "ar_hp_ht":
            sort_columns = ["average return", "hit point", "holding time","cs"]
        case "ar_ht_hp":
            sort_columns = ["average return", "holding time", "hit point","cs"]
        case "ht_ar_hp":
            sort_columns = ["holding time", "average return", "hit point","cs"]
        case "ht_hp_ar":
            sort_columns = ["holding time", "hit point", "average return","cs"]
        case "cs":
            sort_columns = ["cs", "holding time", "hit point", "average return"]

    top_df = get_data.calculate_cumulative_hit_point_col_big_data(
        all_combinations,
        primary_sort=sort_columns[0],
        secondary_sort=sort_columns[1],
        third_sort=sort_columns[2],
        fourth_sort=sort_columns[3],
        top_n=top_n,
        ht_min=ht_min,
        ht_max=ht_max
    )

    # Extract data for plotting
    days = top_df['day_combination']
    hit_point_values = top_df['hit point']
    average_values = top_df['average return']
    holding_time = top_df['holding time']
    fourth_sort = top_df['cs']

    # Create Bar Chart without Tools
    fig = go.Figure()

    # Add cumulative hit point bar
    fig.add_trace(go.Bar(
        x=days,
        y=hit_point_values,
        name='Cumulative Hit Point',
        marker_color='green'
    ))

    # Add average return as a secondary y-axis
    fig.add_trace(go.Bar(
        x=days,
        y=average_values,
        name='Average % Return',
        marker_color='blue'
    ))

    fig.add_trace(go.Bar(
        x=days,
        y=holding_time,
        name='Holding Time',
        marker_color='red'
    ))

    fig.add_trace(go.Bar(
        x=days,
        y=fourth_sort,
        name='Custom scoring',
        marker_color='pink'
    ))

    # Update layout with two y-axes
    fig.update_layout(
        height=750,
        title=f'Top {top_n} Days by {sort_columns[0].capitalize()}, {sort_columns[1].capitalize()} and {sort_columns[2].capitalize()} for {stock_ticker}',
        yaxis=dict(title='Cumulative Hit Point'),
        xaxis_title='Day Combination',
        barmode='group'
    )

    return fig, {"visibility": "visible"}


if __name__ == '__main__':
    app.run_server(debug=True)
