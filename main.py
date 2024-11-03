import dash_bootstrap_components.themes
from dash import Dash, dcc, html, Input, Output
from dash import dash_table
from dash_bootstrap_templates import load_figure_template
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly_resampler import FigureResampler
import pandas as pd
import time
import get_data
import json


load_figure_template("CYBORG")
app = Dash(title="Stock Earnings Analysis",
           external_stylesheets=[dash_bootstrap_components.themes.CYBORG])

app.layout = html.Div([
    html.H4('Stock Chart'),
    dcc.Input(id="stock-ticker", type="text", placeholder="", value="AAPL", debounce=True),
    dcc.Store(id="stock-data-store"),  # Store for retrieved stock data

    dcc.Loading(
            id="loading-1",type="circle",
            children=[dcc.Graph(id="stock-chart", config={"scrollZoom": True}, style={'visibility': 'hidden'})]  # Hidden by default
                ),

    dcc.Loading(
                id="loading-2",type="circle",
                children=[html.Div(id="earnings-table-container", style={'visibility': 'hidden'})]  # Hidden by default
                ),

    # dcc.Loading(
    #             id="loading-3",type="circle",
    #             children=[html.Div(id="all-combinations-container")]  # Hidden by default
    #             ),
    dcc.Loading(id="loading-3", type="circle",
                children=[dcc.Graph(id="all-combinations-container", config={"scrollZoom": True}, style={'visibility': 'hidden'})]),

])


@app.callback(
    Output("stock-data-store", "data"),
    Input("stock-ticker", "value")
)
def retrieve_stock_data(value):
    # Fetch the stock price and earnings data once
    stock_price = get_data.get_stock_price(value)
    stock_earning_days = get_data.get_stock_earning_days(value)
    stock_earning_days = pd.to_datetime(stock_earning_days['Earnings Date'])

    # Store both dataframes as dictionaries
    return {
        "stock_price": stock_price.to_dict("records"),
        "stock_earning_days": stock_earning_days.tolist(),
        "stock_ticker": value
    }


@app.callback(
    Output("stock-chart", "figure"),
    Output("stock-chart", "style"),
    Input("stock-data-store", "data")
)
def display_graph(data):
    if data is None:
        return None  # Return empty figure if no data is available

    stock_price = pd.DataFrame(data["stock_price"])
    stock_earning_days = pd.to_datetime(data["stock_earning_days"])
    stock_ticker = data["stock_ticker"]

    fig = FigureResampler(go.Figure(make_subplots(specs=[[{"secondary_y": True}]])))

    # Add traces for the chart (simplified version)
    fig.add_traces(go.Scatter(x=stock_price['Date'], y=(stock_price['Open'] + stock_price['Close']) / 2), max_n_samples=[3500], secondary_ys=[True])

    for earnings_date in stock_earning_days:
        fig.add_vline(x=earnings_date, line_width=1, line_dash="dash", line_color="grey", secondary_y=True)

    fig.update_layout(
        title=f'Historical data for  {stock_ticker}',

        height=650,
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(step="all")
                ])),
            rangeslider=dict(visible=True),
            type="date"
        )
    )
    # return fig
    return fig, {"visibility":"visible"}


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
        return {"backgroundColor": "#99cc66", "color": "black", 'border': '1px solid black', "marginLeft": "auto", "text-align": "center",  "marginRight": "auto"}  # Green Yellow
    elif 5 <= diff < 10:
        return {"backgroundColor": "#66b266", "color": "white", 'border': '1px solid black', "marginLeft": "auto", "text-align": "center", "marginRight": "auto"}  # Lime Green
    elif 10 <= diff < 20:
        return {"backgroundColor": "#4d994d", "color": "white", 'border': '1px solid black', "marginLeft": "auto", "text-align": "center", "marginRight": "auto"}  # Green
    elif 20 <= diff:
        return {"backgroundColor": "#267326", "color": "white", 'border': '1px solid black', "marginLeft": "auto", "text-align": "center", "marginRight": "auto"}  # Dark Green


def style_other():
    return {'border': '5px solid black', 'padding': '14px', "margin": "auto", "text-align": "center", "font-weight": "bold", "font-size": "20px"}


# Callback to update the earnings table
@app.callback(
    Output("earnings-table-container", "children"),
    Input("stock-data-store", "data")
)
def update_table(data):
    if data is None:
        time.sleep(7)
        return html.Div("Loading data...")   # Return nothing if no data is available

    stock_price = pd.DataFrame(data["stock_price"])
    stock_earning_days = pd.to_datetime(data["stock_earning_days"])

    earnings_diffs = get_data.calculate_price_differences(stock_price, stock_earning_days)

    # Calculate strength
    strength_list = get_data.calculate_strength_row(earnings_diffs)
    cumulative_strength = get_data.calculate_cumulative_strength_col(earnings_diffs)

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
        html.Th("Strength", style={'border': '5px solid black', 'padding': '8px', "marginLeft": "auto"})
    ]))

    # Create the table body with color-coded cells
    table_body = html.Tbody([
        html.Tr([
            html.Td(diff['earnings_day'].strftime('%Y-%m-%d')),
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
            html.Td(strength_list[index], style=style_other())  # Add strength value here
        ]) for index, diff in enumerate(earnings_diffs)
    ] + [
        html.Tr([
            "Cumulative Changes",
            html.Td(cumulative_strength[-42], style=style_other()),
            html.Td(cumulative_strength[-35], style=style_other()),
            html.Td(cumulative_strength[-28], style=style_other()),
            html.Td(cumulative_strength[-21], style=style_other()),
            html.Td(cumulative_strength[-14], style=style_other()),
            html.Td(cumulative_strength[-7], style=style_other()),
            html.Td(cumulative_strength[0], style=style_other()),
            html.Td(cumulative_strength[7], style=style_other()),
            html.Td(cumulative_strength[14], style=style_other()),
            html.Td(cumulative_strength[21], style=style_other()),
            html.Td(cumulative_strength[28], style=style_other()),
            html.Td(cumulative_strength[35], style=style_other()),
            html.Td(cumulative_strength[42], style=style_other())
        ])
    ])

    # Return the full table (header + body)
    return html.Table([table_header, table_body], style={"visibility":"visible", "width": "75%", "padding": "1% 15% 1% 15%", "borderCollapse": "collapse", "border": "2px solid black", "marginTop": "20px", "marginLeft": "auto", "marginRight": "auto"})


@app.callback(
    Output("all-combinations-container", "figure"),
    Output("all-combinations-container", "style"),
    # Output("all-combinations-container", "children"),
    Input("stock-data-store", "data")
)
def update_all_combinations(data):
    if data is None:
        time.sleep(7)
        return html.Div("Loading data...")  # Return nothing if no data is available

    stock_price = pd.DataFrame(data["stock_price"])
    stock_earning_days = pd.to_datetime(data["stock_earning_days"])
    stock_ticker = data["stock_ticker"]

    # Calculate price differences and cumulative strength
    all_combinations = get_data.calculate_price_differences_all_combinations_norepeat(stock_price, stock_earning_days)
    top_25_df = get_data.calculate_cumulative_strength_col_big_data(all_combinations)

    # Extract data for plotting
    days = top_25_df['day_combination']
    strength_values = top_25_df['strength']
    average_values = top_25_df['average_return']

    # Create bar chart
    fig = go.Figure()

    # Add cumulative strength bar
    fig.add_trace(go.Bar(
        x=days,
        y=strength_values,
        name='Cumulative Strength',
        marker_color='blue'
    ))

    # Add average return as a secondary y-axis
    fig.add_trace(go.Bar(
        x=days,
        y=average_values,
        name='Average % Return',
        marker_color='green'
    ))

    # Update layout with two y-axes
    fig.update_layout(
        height=750,
        title=f'Top 25 Days by Strength and Average % Return for {stock_ticker}',
        yaxis=dict(title='Cumulative Strength'),
        xaxis_title='Day Combination',
        barmode='group'
    )

    return fig, {"visibility": "visible"}


if __name__ == '__main__':
    app.run_server(debug=True)
