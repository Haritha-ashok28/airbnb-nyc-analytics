import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import os

# ================================
# LOAD DATA
# ================================

dataset_path = os.path.join(os.path.dirname(__file__), "..", "dataset", "AB_NYC_2019_CleanedData.csv")
df = pd.read_csv(dataset_path)

# Data preprocessing
df = df[df["price"] < 2000]
df["reviews_per_month"] = df["reviews_per_month"].fillna(0)
df["availability_365"] = df["availability_365"].fillna(0)
df["occupancy_rate"] = (365 - df["availability_365"]) / 365 * 100

# ================================
# APP INITIALIZATION
# ================================

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# ================================
# COLOR PALETTE - Neutral & Inclusive
# ================================

# Neutral Professional Colors
COLORS = {
    "primary_bg": "#F8F9FA",
    "secondary_bg": "#FFFFFF",
    "header": "#475569",
    "teal": "#0D9488",
    "indigo": "#4F46E5",
    "emerald": "#059669",
    "amber": "#D97706",
    "slate": "#64748B",
    "text_primary": "#1F2937",
    "text_secondary": "#6B7280",
    "border": "#E5E7EB",
}

# Color scale for gradients
COLOR_SCALE_GRADIENT = [[0, "#99F6E4"], [0.5, "#A5B4FC"], [1, "#FED7AA"]]

# ================================
# HELPER FUNCTIONS
# ================================

def get_kpi_card(title, value, color_class="slate"):
    """Create a KPI card with CSS class styling"""
    return html.Div(
        className=f"kpi-card {color_class}",
        children=[
            html.H6(title, className="kpi-title"),
            html.H3(value, className="kpi-value"),
        ]
    )

def apply_chart_template(fig, title=""):
    """Apply professional template to charts"""
    fig.update_layout(
        template="plotly_white",
        plot_bgcolor="rgba(255, 255, 255, 0.7)",
        paper_bgcolor=COLORS["secondary_bg"],
        font=dict(
            family="'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
            size=12,
            color=COLORS["text_primary"]
        ),
        title_font=dict(
            size=15,
            color=COLORS["text_primary"],
            family="'Segoe UI', 'Helvetica Neue', Arial"
        ),
        hovermode="closest",
        margin=dict(l=50, r=50, t=60, b=50),
        showlegend=True,
        legend=dict(
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor=COLORS["border"],
            borderwidth=1,
        ),
    )
    fig.update_xaxes(
        gridcolor="rgba(226, 232, 240, 0.5)",
        showgrid=True,
        linecolor=COLORS["border"]
    )
    fig.update_yaxes(
        gridcolor="rgba(226, 232, 240, 0.5)",
        showgrid=True,
        linecolor=COLORS["border"]
    )
    return fig

# ================================
# APP LAYOUT
# ================================

app.layout = html.Div(
    style={
        "backgroundColor": COLORS["primary_bg"],
        "padding": "20px",
        "fontFamily": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
        "minHeight": "100vh",
    },
    children=[
        # Header
        html.Div(
            className="dashboard-header",
            children=[
                html.H1("NYC Airbnb Analytics Dashboard"),
                html.P("Explore Airbnb listings, pricing trends, and market insights across NYC neighborhoods"),
            ]
        ),

        # Filter Section
        html.Div(
            className="filters-section",
            children=[
                html.H4("Filters"),
                html.Div(
                    className="filter-group",
                    children=[
                        html.Div(
                            className="filter-item",
                            children=[
                                html.Label("Borough", className="filter-label"),
                                dcc.Dropdown(
                                    id="borough-dropdown",
                                    options=[{"label": i, "value": i} for i in sorted(df["neighbourhood_group"].unique())],
                                    multi=True,
                                    value=list(df["neighbourhood_group"].unique()),
                                    placeholder="Select boroughs...",
                                ),
                            ]
                        ),

                        html.Div(
                            className="filter-item",
                            children=[
                                html.Label("Room Type", className="filter-label"),
                                dcc.Dropdown(
                                    id="room-dropdown",
                                    options=[{"label": i, "value": i} for i in sorted(df["room_type"].unique())],
                                    multi=True,
                                    value=list(df["room_type"].unique()),
                                    placeholder="Select room types...",
                                ),
                            ]
                        ),

                        html.Div(
                            className="filter-item",
                            children=[
                                html.Label("Price Range ($/night)", className="filter-label"),
                                dcc.RangeSlider(
                                    id="price-slider",
                                    min=0,
                                    max=2000,
                                    step=50,
                                    value=[0, 500],
                                    marks={0: "$0", 500: "$500", 1000: "$1K", 2000: "$2K"},
                                    tooltip={"placement": "bottom"},
                                ),
                            ]
                        ),

                        html.Div(
                            className="filter-item",
                            children=[
                                html.Label("Min Reviews", className="filter-label"),
                                dcc.Slider(
                                    id="reviews-slider",
                                    min=0,
                                    max=500,
                                    step=10,
                                    value=0,
                                    marks={0: "0", 100: "100", 250: "250", 500: "500"},
                                    tooltip={"placement": "bottom"},
                                ),
                            ]
                        ),
                    ],
                ),
            ]
        ),

        # KPI Cards
        html.Div(
            id="kpi-container",
            className="kpi-container",
        ),

        # Charts Row 1
        html.Div(
            className="chart-row",
            children=[
                html.Div(dcc.Graph(id="avg-price-borough"), className="chart-container"),
                html.Div(dcc.Graph(id="room-type-distribution"), className="chart-container"),
            ]
        ),

        # Charts Row 2
        html.Div(
            className="chart-row",
            children=[
                html.Div(dcc.Graph(id="price-distribution"), className="chart-container"),
                html.Div(dcc.Graph(id="reviews-vs-price"), className="chart-container"),
            ]
        ),

        # Charts Row 3
        html.Div(
            className="chart-row",
            children=[
                html.Div(dcc.Graph(id="reviews-per-month"), className="chart-container"),
                html.Div(dcc.Graph(id="availability-chart"), className="chart-container"),
            ]
        ),

        # Charts Row 4
        html.Div(
            className="chart-row",
            children=[
                html.Div(dcc.Graph(id="price-vs-minimum-nights"), className="chart-container"),
                html.Div(dcc.Graph(id="top-neighborhoods"), className="chart-container"),
            ]
        ),

        # Map
        html.Div(
            className="map-container",
            children=[dcc.Graph(id="map-chart")]
        ),

        # Heatmap
        html.Div(
            className="heatmap-container",
            children=[dcc.Graph(id="heatmap-chart")]
        ),
    ]
)

# ================================
# CALLBACKS
# ================================

@app.callback(
    Output("kpi-container", "children"),
    [
        Input("borough-dropdown", "value"),
        Input("room-dropdown", "value"),
        Input("price-slider", "value"),
        Input("reviews-slider", "value"),
    ],
)
def update_kpis(selected_boroughs, selected_rooms, selected_price, min_reviews):
    filtered_df = df[
        (df["neighbourhood_group"].isin(selected_boroughs))
        & (df["room_type"].isin(selected_rooms))
        & (df["price"] >= selected_price[0])
        & (df["price"] <= selected_price[1])
        & (df["number_of_reviews"] >= min_reviews)
    ]

    return [
        get_kpi_card("Total Listings", f"{len(filtered_df):,}", "slate"),
        get_kpi_card("Avg Price", f"${filtered_df['price'].mean():.0f}/nt", "teal"),
        get_kpi_card("Avg Reviews", f"{filtered_df['number_of_reviews'].mean():.0f}", "indigo"),
        get_kpi_card("Reviews/Month", f"{filtered_df['reviews_per_month'].mean():.2f}", "emerald"),
        get_kpi_card("Occupancy %", f"{filtered_df['occupancy_rate'].mean():.1f}%", "amber"),
        get_kpi_card("Top Room Type", f"{filtered_df['room_type'].mode()[0]}", "slate"),
    ]

@app.callback(
    [
        Output("avg-price-borough", "figure"),
        Output("room-type-distribution", "figure"),
        Output("price-distribution", "figure"),
        Output("reviews-vs-price", "figure"),
        Output("reviews-per-month", "figure"),
        Output("availability-chart", "figure"),
        Output("price-vs-minimum-nights", "figure"),
        Output("top-neighborhoods", "figure"),
        Output("map-chart", "figure"),
        Output("heatmap-chart", "figure"),
    ],
    [
        Input("borough-dropdown", "value"),
        Input("room-dropdown", "value"),
        Input("price-slider", "value"),
        Input("reviews-slider", "value"),
    ],
)
def update_charts(selected_boroughs, selected_rooms, selected_price, min_reviews):
    filtered_df = df[
        (df["neighbourhood_group"].isin(selected_boroughs))
        & (df["room_type"].isin(selected_rooms))
        & (df["price"] >= selected_price[0])
        & (df["price"] <= selected_price[1])
        & (df["number_of_reviews"] >= min_reviews)
    ]

    # 1. Average Price by Borough
    borough_data = filtered_df.groupby("neighbourhood_group").agg({
        "price": "mean",
        "id": "count"
    }).reset_index().rename(columns={"id": "count"})
    
    fig1 = px.bar(
        borough_data,
        x="neighbourhood_group",
        y="price",
        title="Average Price by Borough",
        labels={"price": "Price ($)", "neighbourhood_group": "Borough"},
        color="price",
        color_continuous_scale=COLOR_SCALE_GRADIENT,
    )
    fig1.update_traces(textposition="auto")
    fig1 = apply_chart_template(fig1)

    # 2. Room Type Distribution
    room_counts = filtered_df["room_type"].value_counts().reset_index()
    neutral_colors = [COLORS["teal"], COLORS["indigo"], COLORS["emerald"]]
    fig2 = px.pie(
        filtered_df,
        names="room_type",
        title="Room Type Distribution",
        color_discrete_sequence=neutral_colors,
    )
    fig2.update_traces(textposition="inside", textinfo="label+percent")
    fig2 = apply_chart_template(fig2)

    # 3. Price Distribution
    fig3 = px.histogram(
        filtered_df,
        x="price",
        nbins=40,
        title="Price Distribution",
        labels={"price": "Price ($)"},
        color_discrete_sequence=[COLORS["indigo"]],
    )
    fig3 = apply_chart_template(fig3)

    # 4. Reviews vs Price (Scatter)
    room_color_map = {room: color for room, color in zip(filtered_df["room_type"].unique(), neutral_colors[:len(filtered_df["room_type"].unique())])}
    fig4 = px.scatter(
        filtered_df,
        x="number_of_reviews",
        y="price",
        color="room_type",
        size="minimum_nights",
        hover_data=["neighbourhood", "reviews_per_month"],
        title="Reviews vs Price",
        labels={"number_of_reviews": "Number of Reviews", "price": "Price ($)"},
        color_discrete_map=room_color_map,
    )
    fig4 = apply_chart_template(fig4)

    # 5. Reviews Per Month by Borough
    reviews_data = filtered_df.groupby("neighbourhood_group")["reviews_per_month"].mean().reset_index()
    fig5 = px.bar(
        reviews_data,
        x="neighbourhood_group",
        y="reviews_per_month",
        title="Average Reviews per Month",
        labels={"reviews_per_month": "Reviews/Month", "neighbourhood_group": "Borough"},
        color="reviews_per_month",
        color_continuous_scale=[[0, COLORS["teal"]], [1, COLORS["emerald"]]],
    )
    fig5 = apply_chart_template(fig5)

    # 6. Availability Analysis
    availability_data = filtered_df.groupby("neighbourhood_group")["availability_365"].mean().reset_index()
    fig6 = px.bar(
        availability_data,
        x="neighbourhood_group",
        y="availability_365",
        title="Annual Availability by Borough",
        labels={"availability_365": "Days Available", "neighbourhood_group": "Borough"},
        color="availability_365",
        color_continuous_scale=[[0, COLORS["amber"]], [1, COLORS["teal"]]],
    )
    fig6 = apply_chart_template(fig6)

    # 7. Price vs Minimum Nights
    fig7 = px.scatter(
        filtered_df.sample(min(1000, len(filtered_df))),
        x="minimum_nights",
        y="price",
        color="room_type",
        title="Price vs Minimum Stay Required",
        labels={"minimum_nights": "Minimum Nights", "price": "Price ($)"},
        color_discrete_map=room_color_map,
    )
    fig7.update_xaxes(type="log")
    fig7 = apply_chart_template(fig7)

    # 8. Top 10 Neighborhoods
    top_neighborhoods = filtered_df.groupby("neighbourhood")["id"].count().nlargest(10).reset_index().rename(columns={"id": "count"})
    fig8 = px.bar(
        top_neighborhoods.sort_values("count"),
        x="count",
        y="neighbourhood",
        orientation="h",
        title="Top 10 Neighborhoods",
        labels={"count": "Number of Listings", "neighbourhood": "Neighborhood"},
        color="count",
        color_continuous_scale=[[0, COLORS["indigo"]], [1, COLORS["teal"]]],
    )
    fig8 = apply_chart_template(fig8)

    # 9. Map with Leaflet style - High contrast colors for visibility
    map_sample = filtered_df.sample(min(2000, len(filtered_df))) if len(filtered_df) > 0 else filtered_df
    fig9 = px.scatter_map(
        map_sample,
        lat="latitude",
        lon="longitude",
        color="price",
        size="number_of_reviews",
        hover_name="name",
        hover_data={"room_type": True, "neighbourhood_group": True, "price": ":.0f"},
        zoom=10,
        height=600,
        title="Airbnb Listings Map - NYC",
        color_continuous_scale=[
            [0, COLORS["emerald"]],      # Dark emerald for low prices
            [0.5, COLORS["indigo"]],     # Dark indigo for mid prices
            [1, COLORS["amber"]]         # Dark amber for high prices
        ],
        map_style="open-street-map",
    )
    fig9.update_layout(hovermode="closest")

    # 10. Heatmap - Price by Room Type and Borough
    heatmap_data = filtered_df.pivot_table(values="price", index="room_type", columns="neighbourhood_group", aggfunc="mean")
    fig10 = px.imshow(
        heatmap_data,
        labels=dict(x="Borough", y="Room Type", color="Avg Price ($)"),
        title="Price Heatmap: Room Type vs Borough",
        color_continuous_scale=COLOR_SCALE_GRADIENT,
        aspect="auto",
    )
    fig10 = apply_chart_template(fig10)

    return fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9, fig10

# ================================
# RUN APP
# ================================

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)