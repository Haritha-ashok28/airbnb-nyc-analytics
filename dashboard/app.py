import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import os

# LOAD DATA

DATASET_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "dataset",
    "AB_NYC_2019_CleanedData.csv"
)


df = pd.read_csv(DATASET_PATH)

# DATA PREPROCESSING

# Remove extreme outliers

df = df[df["price"] < 2000]

# Fill missing values

df["reviews_per_month"] = df["reviews_per_month"].fillna(0)
df["availability_365"] = df["availability_365"].fillna(0)

# Occupancy calculation

df["occupancy_rate"] = (
    (365 - df["availability_365"]) / 365
) * 100

# APP INITIALIZATION

app = Dash(__name__)
server = app.server

# COLOR SYSTEM

COLORS = {
    "background": "#F4F7FB",
    "card": "#FFFFFF",
    "text": "#111827",
    "muted": "#6B7280",
    "border": "#E5E7EB",
    "primary": "#2563EB",
    "secondary": "#14B8A6",
    "accent": "#7C3AED",
    "success": "#059669",
    "warning": "#D97706"
}

# KPI CARD FUNCTION


def kpi_card(title, value, subtitle=""):
    return html.Div(
        className="kpi-card",
        children=[
            html.Div(className="kpi-title", children=title),
            html.Div(className="kpi-value", children=value),
            html.Div(className="kpi-subtitle", children=subtitle),
        ],
    )

# CHART STYLING


def style_chart(fig):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=COLORS["card"],
        plot_bgcolor=COLORS["card"],
        font=dict(
            family="Inter, sans-serif",
            size=12,
            color=COLORS["text"]
        ),
        title_font=dict(
            size=16,
            family="Inter, sans-serif",
            color=COLORS["text"]
        ),
        margin=dict(l=20, r=20, t=50, b=20),
        hovermode="closest",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    fig.update_xaxes(
        showgrid=False,
        linecolor="#E5E7EB"
    )

    fig.update_yaxes(
        gridcolor="rgba(229,231,235,0.5)",
        linecolor="#E5E7EB"
    )

    return fig

# APP LAYOUT

app.layout = html.Div(
    className="main-container",
    children=[

        
        # HEADER
      
        html.Div(
            className="header",
            children=[
                html.Div(
                    children=[
                        html.H1(
                            "NYC Airbnb Market Intelligence",
                            className="main-title"
                        ),
                        html.P(
                            "Interactive analytics dashboard for pricing, occupancy, and neighborhood insights.",
                            className="subtitle"
                        ),
                    ]
                )
            ]
        ),

        
        # FILTERS
        

        html.Div(
            className="filter-panel",
            children=[

                html.Div(
                    className="filter-box",
                    children=[
                        html.Label("Borough"),
                        dcc.Dropdown(
                            id="borough-dropdown",
                            options=[
                                {
                                    "label": i,
                                    "value": i
                                }
                                for i in sorted(
                                    df["neighbourhood_group"].unique()
                                )
                            ],
                            value=list(
                                df["neighbourhood_group"].unique()
                            ),
                            multi=True,
                        ),
                    ]
                ),

                html.Div(
                    className="filter-box",
                    children=[
                        html.Label("Room Type"),
                        dcc.Dropdown(
                            id="room-dropdown",
                            options=[
                                {
                                    "label": i,
                                    "value": i
                                }
                                for i in sorted(
                                    df["room_type"].unique()
                                )
                            ],
                            value=list(df["room_type"].unique()),
                            multi=True,
                        ),
                    ]
                ),

                html.Div(
                    className="filter-box slider-box",
                    children=[
                        html.Label("Price Range"),
                        dcc.RangeSlider(
                            id="price-slider",
                            min=0,
                            max=2000,
                            step=50,
                            value=[0, 500],
                            marks={
                                0: "$0",
                                500: "$500",
                                1000: "$1K",
                                2000: "$2K"
                            },
                        ),
                    ]
                ),
            ]
        ),

        
        # KPI SECTION
        

        html.Div(
            id="kpi-container",
            className="kpi-grid"
        ),

        
        # MAIN CHARTS
        

        html.Div(
            className="chart-grid",
            children=[

                html.Div(
                    className="chart-card large-card",
                    children=[
                        dcc.Graph(id="price-borough-chart")
                    ]
                ),

                html.Div(
                    className="chart-card",
                    children=[
                        dcc.Graph(id="room-distribution-chart")
                    ]
                ),

                html.Div(
                    className="chart-card",
                    children=[
                        dcc.Graph(id="reviews-price-chart")
                    ]
                ),

                html.Div(
                    className="chart-card large-card",
                    children=[
                        dcc.Graph(id="top-neighborhoods-chart")
                    ]
                ),
            ]
        ),

        
        # MAP
       

        html.Div(
            className="map-card",
            children=[
                dcc.Graph(id="map-chart")
            ]
        ),

        
        # HEATMAP
       

        html.Div(
            className="heatmap-card",
            children=[
                dcc.Graph(id="heatmap-chart")
            ]
        ),
    ]
)


# CALLBACKS


@app.callback(
    Output("kpi-container", "children"),
    [
        Input("borough-dropdown", "value"),
        Input("room-dropdown", "value"),
        Input("price-slider", "value"),
    ]
)

def update_kpis(selected_boroughs, selected_rooms, selected_price):

    filtered_df = df[
        (df["neighbourhood_group"].isin(selected_boroughs))
        & (df["room_type"].isin(selected_rooms))
        & (df["price"] >= selected_price[0])
        & (df["price"] <= selected_price[1])
    ]

    return [
        kpi_card(
            "Total Listings",
            f"{len(filtered_df):,}",
            "Active Airbnb properties"
        ),

        kpi_card(
            "Average Price",
            f"${filtered_df['price'].mean():.0f}",
            "Average nightly rate"
        ),

        kpi_card(
            "Occupancy Rate",
            f"{filtered_df['occupancy_rate'].mean():.1f}%",
            "Estimated occupancy"
        ),

        kpi_card(
            "Avg Reviews",
            f"{filtered_df['number_of_reviews'].mean():.0f}",
            "Customer engagement"
        ),
    ]

@app.callback(
    [
        Output("price-borough-chart", "figure"),
        Output("room-distribution-chart", "figure"),
        Output("reviews-price-chart", "figure"),
        Output("top-neighborhoods-chart", "figure"),
        Output("map-chart", "figure"),
        Output("heatmap-chart", "figure"),
    ],

    [
        Input("borough-dropdown", "value"),
        Input("room-dropdown", "value"),
        Input("price-slider", "value"),
    ]
)

def update_charts(selected_boroughs, selected_rooms, selected_price):

    filtered_df = df[
        (df["neighbourhood_group"].isin(selected_boroughs))
        & (df["room_type"].isin(selected_rooms))
        & (df["price"] >= selected_price[0])
        & (df["price"] <= selected_price[1])
    ]

    
    # PRICE BY BOROUGH
    

    borough_data = filtered_df.groupby(
        "neighbourhood_group"
    )["price"].mean().reset_index()

    fig1 = px.bar(
        borough_data,
        x="neighbourhood_group",
        y="price",
        title="Average Price by Borough",
        color="price",
        color_continuous_scale="Blues"
    )

    fig1 = style_chart(fig1)

    
    # ROOM DISTRIBUTION
    

    fig2 = px.pie(
        filtered_df,
        names="room_type",
        title="Room Type Distribution",
        hole=0.5,
        color_discrete_sequence=[
            COLORS["primary"],
            COLORS["secondary"],
            COLORS["accent"]
        ]
    )

    fig2 = style_chart(fig2)

    
    # REVIEWS VS PRICE
    

    fig3 = px.scatter(
        filtered_df.sample(min(1500, len(filtered_df))),
        x="number_of_reviews",
        y="price",
        color="room_type",
        size="minimum_nights",
        title="Reviews vs Pricing Analysis",
        opacity=0.7,
        color_discrete_sequence=[
            COLORS["primary"],
            COLORS["secondary"],
            COLORS["accent"]
        ]
    )

    fig3 = style_chart(fig3)

   
    # TOP NEIGHBORHOODS
    

    top_data = (
        filtered_df.groupby("neighbourhood")
        ["id"]
        .count()
        .nlargest(10)
        .reset_index()
        .rename(columns={"id": "count"})
    )

    fig4 = px.bar(
        top_data.sort_values("count"),
        x="count",
        y="neighbourhood",
        orientation="h",
        title="Top Performing Neighborhoods",
        color="count",
        color_continuous_scale="Teal"
    )

    fig4 = style_chart(fig4)


    # MAP
    
    map_df = filtered_df.sample(
        min(2000, len(filtered_df))
    )

    fig5 = px.scatter_map(
        map_df,
        lat="latitude",
        lon="longitude",
        color="price",
        size="number_of_reviews",
        zoom=10,
        height=600,
        title="NYC Airbnb Listing Density",
        hover_name="name",
        color_continuous_scale="Viridis",
        map_style="carto-positron"
    )

    fig5.update_layout(
        margin=dict(l=0, r=0, t=50, b=0)
    )

   
    # HEATMAP
   

    heatmap_data = filtered_df.pivot_table(
        values="price",
        index="room_type",
        columns="neighbourhood_group",
        aggfunc="mean"
    )

    fig6 = px.imshow(
        heatmap_data,
        title="Price Heatmap by Room Type and Borough",
        color_continuous_scale="Tealgrn"
    )

    fig6 = style_chart(fig6)

    return fig1, fig2, fig3, fig4, fig5, fig6

# RUN APP

if __name__ == "__main__":
    app.run(debug=True, port=8050)
