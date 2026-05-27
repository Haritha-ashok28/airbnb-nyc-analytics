import os
import io
import json
import base64
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

from dash import Dash, dcc, html, ctx
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    PageBreak,
)

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# =====================================================
# LOAD DATA
# =====================================================

DATASET_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "dataset",
    "AB_NYC_2019_CleanedData.csv"
)

df = pd.read_csv(DATASET_PATH)

# =====================================================
# CLEAN
# =====================================================

df = df[df["price"] < 1000]

df["reviews_per_month"] = (
    df["reviews_per_month"]
    .fillna(0)
)

df["availability_365"] = (
    df["availability_365"]
    .fillna(0)
)

df["occupancy_rate"] = (
    (365 - df["availability_365"]) / 365
) * 100

# =====================================================
# NYC BOROUGHS GEOJSON
# (inline minimal GeoJSON for the 5 boroughs)
# =====================================================

NYC_GEOJSON_URL = (
    "https://raw.githubusercontent.com/dwillis/nyc-maps/master/"
    "boroughs.geojson"
)

try:
    resp = requests.get(NYC_GEOJSON_URL, timeout=10)
    NYC_GEOJSON = resp.json()
    # Normalise the borough-name field so it matches df values
    # The GeoJSON uses "BoroName"; df uses "neighbourhood_group"
    BOROUGH_KEY = "BoroName"
except Exception:
    NYC_GEOJSON = None
    BOROUGH_KEY = None

# =====================================================
# APP
# =====================================================

app = Dash(__name__)
server = app.server

# =====================================================
# THEMES
# =====================================================

LIGHT = {
    "bg": "#F4F7FB",
    "card": "#FFFFFF",
    "text": "#111827",
    "grid": "rgba(0,0,0,0.08)"
}

DARK = {
    "bg": "#0F172A",
    "card": "#111827",
    "text": "#F8FAFC",
    "grid": "rgba(255,255,255,0.08)"
}

# =====================================================
# KPI CARD
# =====================================================

def kpi_card(title, value, subtitle=""):

    return html.Div(
        className="kpi-card",
        children=[

            html.Div(title, className="kpi-title"),

            html.Div(value, className="kpi-value"),

            html.Div(subtitle, className="kpi-subtitle")
        ]
    )

# =====================================================
# STYLE CHART
# =====================================================

def style_chart(fig, dark=False):

    theme = DARK if dark else LIGHT

    fig.update_layout(

        template=(
            "plotly_dark"
            if dark
            else "plotly_white"
        ),

        paper_bgcolor=theme["card"],
        plot_bgcolor=theme["card"],

        font=dict(
            family="Inter",
            color=theme["text"]
        ),

        margin=dict(
            l=20,
            r=20,
            t=55,
            b=20
        ),

        hoverlabel=dict(
            bgcolor=theme["card"],
            font_color=theme["text"]
        )
    )

    fig.update_xaxes(
        gridcolor=theme["grid"],
        color=theme["text"]
    )

    fig.update_yaxes(
        gridcolor=theme["grid"],
        color=theme["text"]
    )

    return fig

# =====================================================
# FILTER FUNCTION
# =====================================================

def filter_df(boroughs, rooms, prices):

    filtered = df[
        (
            df["neighbourhood_group"]
            .isin(boroughs)
        )
        &
        (
            df["room_type"]
            .isin(rooms)
        )
        &
        (
            df["price"] >= prices[0]
        )
        &
        (
            df["price"] <= prices[1]
        )
    ]

    return filtered

# =====================================================
# ALL OPTIONS
# =====================================================

ALL_BOROUGHS = sorted(df["neighbourhood_group"].unique())
ALL_ROOMS    = sorted(df["room_type"].unique())

# =====================================================
# LAYOUT
# =====================================================

app.layout = html.Div(

    id="main-container",
    className="light-theme",

    children=[

        dcc.Store(
            id="theme-store",
            data="light"
        ),

        # =====================================================
        # HEADER
        # =====================================================

        html.Div(

            className="header",

            children=[

                html.Div([

                    html.H1(
                        "NYC Airbnb Market Intelligence",
                        className="main-title"
                    ),

                    html.P(
                        "Enterprise analytics dashboard for Airbnb market trends and pricing intelligence.",
                        className="subtitle"
                    )
                ]),

                html.Div(

                    className="header-actions",

                    children=[

                        html.Button(
                            "🌙 Toggle Theme",
                            id="theme-toggle",
                            className="theme-btn",
                            n_clicks=0
                        ),

                        html.Button(
                            "⬇ Export PDF",
                            id="pdf-btn",
                            className="export-btn",
                            n_clicks=0
                        ),

                        dcc.Download(id="download-pdf")
                    ]
                )
            ]
        ),

        # =====================================================
        # FILTERS
        # =====================================================

        html.Div(

            className="filter-panel",

            children=[

                # --- Borough filter ---
                html.Div(

                    className="filter-box",

                    children=[

                        html.Label("Borough"),

                        # Select All / Deselect All buttons
                        html.Div(
                            className="filter-btn-row",
                            children=[
                                html.Button(
                                    "Select All",
                                    id="borough-select-all",
                                    className="filter-action-btn",
                                    n_clicks=0
                                ),
                                html.Button(
                                    "Deselect All",
                                    id="borough-deselect-all",
                                    className="filter-action-btn filter-action-btn--danger",
                                    n_clicks=0
                                ),
                            ]
                        ),

                        dcc.Dropdown(
                            id="borough-dropdown",

                            options=[
                                {"label": i, "value": i}
                                for i in ALL_BOROUGHS
                            ],

                            value=list(ALL_BOROUGHS),

                            multi=True,

                            clearable=True,

                            className="themed-dropdown"
                        )
                    ]
                ),

                # --- Room Type filter ---
                html.Div(

                    className="filter-box",

                    children=[

                        html.Label("Room Type"),

                        html.Div(
                            className="filter-btn-row",
                            children=[
                                html.Button(
                                    "Select All",
                                    id="room-select-all",
                                    className="filter-action-btn",
                                    n_clicks=0
                                ),
                                html.Button(
                                    "Deselect All",
                                    id="room-deselect-all",
                                    className="filter-action-btn filter-action-btn--danger",
                                    n_clicks=0
                                ),
                            ]
                        ),

                        dcc.Dropdown(
                            id="room-dropdown",

                            options=[
                                {"label": i, "value": i}
                                for i in ALL_ROOMS
                            ],

                            value=list(ALL_ROOMS),

                            multi=True,

                            clearable=True,

                            className="themed-dropdown"
                        )
                    ]
                ),

                # --- Price Range filter ---
                html.Div(

                    className="filter-box",

                    children=[

                        html.Label("Price Range"),

                        dcc.RangeSlider(
                            id="price-slider",

                            min=0,
                            max=1000,
                            step=25,

                            value=[0, 500],

                            marks={
                                0: "$0",
                                250: "$250",
                                500: "$500",
                                750: "$750",
                                1000: "$1K"
                            }
                        )
                    ]
                )
            ]
        ),

        html.Div(
            id="kpi-container",
            className="kpi-grid"
        ),

        html.Div(
            id="insight-box",
            className="insight-card"
        ),

        html.Div(

            className="chart-grid",

            children=[

                html.Div(
                    className="chart-card",
                    children=[
                        dcc.Graph(id="borough-chart")
                    ]
                ),

                html.Div(
                    className="chart-card",
                    children=[
                        dcc.Graph(id="room-chart")
                    ]
                ),

                html.Div(
                    className="chart-card",
                    children=[
                        dcc.Graph(id="review-chart")
                    ]
                ),

                html.Div(
                    className="chart-card",
                    children=[
                        dcc.Graph(id="neighborhood-chart")
                    ]
                )
            ]
        ),

        html.Div(
            className="map-card",
            children=[
                dcc.Graph(id="map-chart")
            ]
        ),

        html.Div(
            className="heatmap-card",
            children=[
                dcc.Graph(id="heatmap-chart")
            ]
        )
    ]
)

# =====================================================
# BOROUGH SELECT / DESELECT ALL
# =====================================================

@app.callback(
    Output("borough-dropdown", "value"),
    [
        Input("borough-select-all",   "n_clicks"),
        Input("borough-deselect-all", "n_clicks"),
    ],
    prevent_initial_call=True
)
def borough_select_all(select_n, deselect_n):
    triggered = ctx.triggered_id
    if triggered == "borough-select-all":
        return list(ALL_BOROUGHS)
    if triggered == "borough-deselect-all":
        return []
    raise PreventUpdate

# =====================================================
# ROOM SELECT / DESELECT ALL
# =====================================================

@app.callback(
    Output("room-dropdown", "value"),
    [
        Input("room-select-all",   "n_clicks"),
        Input("room-deselect-all", "n_clicks"),
    ],
    prevent_initial_call=True
)
def room_select_all(select_n, deselect_n):
    triggered = ctx.triggered_id
    if triggered == "room-select-all":
        return list(ALL_ROOMS)
    if triggered == "room-deselect-all":
        return []
    raise PreventUpdate

# =====================================================
# THEME TOGGLE
# =====================================================

@app.callback(

    [
        Output("main-container", "className"),
        Output("theme-store", "data")
    ],

    Input("theme-toggle", "n_clicks")
)

def toggle_theme(n):

    if n and n % 2 != 0:
        return "dark-theme", "dark"

    return "light-theme", "light"

# =====================================================
# KPI
# =====================================================

@app.callback(

    Output("kpi-container", "children"),

    [
        Input("borough-dropdown", "value"),
        Input("room-dropdown", "value"),
        Input("price-slider", "value")
    ]
)

def update_kpis(boroughs, rooms, prices):

    boroughs = boroughs or []
    rooms    = rooms    or []

    filtered = filter_df(boroughs, rooms, prices)

    if filtered.empty:
        return [kpi_card("No Data", "—", "Adjust filters")]

    return [

        kpi_card(
            "Total Listings",
            f"{len(filtered):,}",
            "Active listings"
        ),

        kpi_card(
            "Average Price",
            f"${filtered['price'].mean():.0f}",
            "Nightly average"
        ),

        kpi_card(
            "Occupancy Rate",
            f"{filtered['occupancy_rate'].mean():.1f}%",
            "Estimated occupancy"
        ),

        kpi_card(
            "Avg Reviews",
            f"{filtered['number_of_reviews'].mean():.0f}",
            "Customer engagement"
        )
    ]

# =====================================================
# INSIGHTS
# =====================================================

@app.callback(

    Output("insight-box", "children"),

    [
        Input("borough-dropdown", "value"),
        Input("room-dropdown", "value"),
        Input("price-slider", "value")
    ]
)

def update_insights(boroughs, rooms, prices):

    boroughs = boroughs or []
    rooms    = rooms    or []

    filtered = filter_df(boroughs, rooms, prices)

    if filtered.empty:

        return html.Div(
            "No insights available.",
            className="empty-insight"
        )

    borough_prices = (
        filtered.groupby("neighbourhood_group")["price"].mean()
    )
    top_borough = borough_prices.idxmax() if not borough_prices.empty else "N/A"

    avg_price = filtered["price"].mean()

    mode_vals = filtered["room_type"].mode()
    top_room  = mode_vals[0] if not mode_vals.empty else "N/A"

    borough_reviews = (
        filtered.groupby("neighbourhood_group")["number_of_reviews"].mean()
    )
    busiest = borough_reviews.idxmax() if not borough_reviews.empty else "N/A"

    return [

        html.H3(
            "📊 Automated Business Insights"
        ),

        html.P(
            f"🏆 {top_borough} has the highest average Airbnb pricing."
        ),

        html.P(
            f"💰 Average listing price is ${avg_price:.0f} per night."
        ),

        html.P(
            f"🏠 Most common room type is {top_room}."
        ),

        html.P(
            f"⭐ {busiest} shows the highest customer engagement."
        )
    ]

# =====================================================
# CHARTS
# =====================================================

@app.callback(

    [
        Output("borough-chart",      "figure"),
        Output("room-chart",         "figure"),
        Output("review-chart",       "figure"),
        Output("neighborhood-chart", "figure"),
        Output("map-chart",          "figure"),
        Output("heatmap-chart",      "figure")
    ],

    [
        Input("borough-dropdown", "value"),
        Input("room-dropdown",    "value"),
        Input("price-slider",     "value"),
        Input("theme-store",      "data")
    ]
)

def update_charts(boroughs, rooms, prices, theme):

    dark      = theme == "dark"
    boroughs  = boroughs or []
    rooms     = rooms    or []
    filtered  = filter_df(boroughs, rooms, prices)
    theme_cfg = DARK if dark else LIGHT

    # --------------------------------------------------
    # Helper: blank placeholder figure for empty states
    # --------------------------------------------------
    def empty_fig(title):
        fig = go.Figure()
        fig.update_layout(
            title=title,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            annotations=[dict(
                text="No data — adjust your filters",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14, color=theme_cfg["text"])
            )],
            paper_bgcolor=theme_cfg["card"],
            plot_bgcolor=theme_cfg["card"],
            font=dict(family="Inter", color=theme_cfg["text"])
        )
        return fig

    # =====================================================
    # BOROUGH BAR
    # =====================================================

    if filtered.empty:
        fig1 = empty_fig("Average Price by Borough")
    else:
        borough_df = (
            filtered.groupby("neighbourhood_group")["price"]
            .mean()
            .reset_index()
        )
        fig1 = px.bar(
            borough_df,
            x="neighbourhood_group",
            y="price",
            color="price",
            title="Average Price by Borough",
            color_continuous_scale="Blues"
        )
        fig1 = style_chart(fig1, dark)

    # =====================================================
    # ROOM TYPE PIE
    # =====================================================

    if filtered.empty:
        fig2 = empty_fig("Room Type Distribution")
    else:
        room_df = (
            filtered["room_type"]
            .value_counts()
            .reset_index()
        )
        fig2 = px.pie(
            room_df,
            names="room_type",
            values="count",
            title="Room Type Distribution",
            hole=0.45
        )
        fig2 = style_chart(fig2, dark)

    # =====================================================
    # SCATTER – Reviews vs Price
    # =====================================================

    if filtered.empty:
        fig3 = empty_fig("Reviews vs Pricing")
    else:
        sample = filtered.sample(
            min(2500, len(filtered)),
            random_state=42
        ).copy()
        sample["jitter_price"] = (
            sample["price"] +
            np.random.normal(0, 5, len(sample))
        )
        fig3 = px.scatter(
            sample,
            x="number_of_reviews",
            y="jitter_price",
            color="room_type",
            opacity=0.4,
            title="Reviews vs Pricing",
            hover_data=["neighbourhood_group", "minimum_nights"]
        )
        fig3.update_traces(marker=dict(size=6))
        fig3.update_xaxes(type="log")
        fig3 = style_chart(fig3, dark)

    # =====================================================
    # TOP NEIGHBORHOODS
    # =====================================================

    if filtered.empty:
        fig4 = empty_fig("Top Neighborhoods")
    else:
        top_df = (
            filtered.groupby("neighbourhood")["id"]
            .count()
            .nlargest(10)
            .reset_index()
        )
        fig4 = px.bar(
            top_df.sort_values("id"),
            x="id",
            y="neighbourhood",
            orientation="h",
            color="id",
            title="Top Neighborhoods",
            color_continuous_scale="Viridis"
        )
        fig4 = style_chart(fig4, dark)

    # =====================================================
    # CHOROPLETH MAP — Borough-level avg price
    # =====================================================

    borough_avg = pd.DataFrame()
    if not filtered.empty:
        borough_avg = (
            filtered.groupby("neighbourhood_group")["price"]
            .mean()
            .reset_index()
            .rename(columns={
                "neighbourhood_group": "borough",
                "price": "avg_price"
            })
        )

    use_choropleth = (
        NYC_GEOJSON is not None
        and not borough_avg.empty
        and borough_avg["avg_price"].nunique() > 0
    )

    if use_choropleth:
        price_min = borough_avg["avg_price"].min()
        price_max = borough_avg["avg_price"].max()
        # Guard against zero-range colorscale
        if price_min == price_max:
            price_min = max(0, price_min - 1)
            price_max = price_max + 1

        fig5 = px.choropleth_mapbox(
            borough_avg,
            geojson=NYC_GEOJSON,
            featureidkey=f"properties.{BOROUGH_KEY}",
            locations="borough",
            color="avg_price",
            color_continuous_scale=[
                [0.0,  "#cfe2f3"],
                [0.25, "#84bbd8"],
                [0.5,  "#3690c0"],
                [0.75, "#0570b0"],
                [1.0,  "#034e7b"],
            ],
            range_color=(price_min, price_max),
            mapbox_style=(
                "carto-darkmatter" if dark else "carto-positron"
            ),
            zoom=9,
            center=dict(lat=40.7128, lon=-74.0060),
            opacity=0.75,
            labels={"avg_price": "Avg Price ($)"},
            title="Average Airbnb Price by Borough",
            hover_data={"avg_price": ":.0f"}
        )
        fig5.update_layout(
            margin=dict(l=0, r=0, t=50, b=0),
            paper_bgcolor=theme_cfg["card"],
            font=dict(family="Inter", color=theme_cfg["text"]),
            coloraxis_colorbar=dict(
                title="Avg $",
                tickprefix="$",
                thickness=14,
                len=0.6
            )
        )

    elif not filtered.empty:
        # GeoJSON unavailable — fallback scatter map
        fig5 = px.scatter_mapbox(
            filtered,
            lat="latitude",
            lon="longitude",
            color="price",
            size_max=8,
            opacity=0.5,
            title="NYC Airbnb Listings",
            color_continuous_scale="Blues",
            mapbox_style=(
                "carto-darkmatter" if dark else "carto-positron"
            ),
            center=dict(lat=40.7128, lon=-74.0060),
            zoom=9
        )
        fig5.update_layout(
            margin=dict(l=0, r=0, t=50, b=0),
            paper_bgcolor=theme_cfg["card"],
            font=dict(family="Inter", color=theme_cfg["text"])
        )

    else:
        fig5 = empty_fig("Average Airbnb Price by Borough")
        fig5.update_layout(margin=dict(l=0, r=0, t=50, b=0))

    # =====================================================
    # HEATMAP — Price by Room Type × Borough
    # =====================================================

    if filtered.empty:
        fig6 = empty_fig("Price Heatmap")
    else:
        try:
            heatmap = filtered.pivot_table(
                values="price",
                index="room_type",
                columns="neighbourhood_group",
                aggfunc="mean"
            )
            fig6 = px.imshow(
                heatmap,
                text_auto=True,
                title="Price Heatmap",
                aspect="auto"
            )
            fig6 = style_chart(fig6, dark)
        except Exception:
            fig6 = empty_fig("Price Heatmap")

    return fig1, fig2, fig3, fig4, fig5, fig6

# =====================================================
# PDF
# =====================================================

# Brand colours (match dashboard gradient)
PDF_BLUE  = colors.HexColor("#2563EB")
PDF_TEAL  = colors.HexColor("#14B8A6")
PDF_DARK  = colors.HexColor("#111827")
PDF_GREY  = colors.HexColor("#6B7280")
PDF_LIGHT = colors.HexColor("#F4F7FB")
PDF_WHITE = colors.white


def build_pdf_styles():
    """Return a dict of custom ParagraphStyles."""

    base = getSampleStyleSheet()

    return {
        "report_title": ParagraphStyle(
            "report_title",
            fontSize=26,
            fontName="Helvetica-Bold",
            textColor=PDF_WHITE,
            alignment=TA_LEFT,
            leading=32,
        ),
        "report_subtitle": ParagraphStyle(
            "report_subtitle",
            fontSize=11,
            fontName="Helvetica",
            textColor=colors.HexColor("#CBD5E1"),
            alignment=TA_LEFT,
            leading=16,
        ),
        "section_heading": ParagraphStyle(
            "section_heading",
            fontSize=14,
            fontName="Helvetica-Bold",
            textColor=PDF_BLUE,
            spaceBefore=18,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body",
            fontSize=10,
            fontName="Helvetica",
            textColor=PDF_DARK,
            leading=16,
            spaceAfter=6,
        ),
        "kpi_label": ParagraphStyle(
            "kpi_label",
            fontSize=9,
            fontName="Helvetica",
            textColor=PDF_GREY,
            alignment=TA_CENTER,
        ),
        "kpi_value": ParagraphStyle(
            "kpi_value",
            fontSize=20,
            fontName="Helvetica-Bold",
            textColor=PDF_BLUE,
            alignment=TA_CENTER,
            leading=24,
        ),
        "kpi_sub": ParagraphStyle(
            "kpi_sub",
            fontSize=8,
            fontName="Helvetica",
            textColor=PDF_GREY,
            alignment=TA_CENTER,
        ),
        "table_header": ParagraphStyle(
            "table_header",
            fontSize=9,
            fontName="Helvetica-Bold",
            textColor=PDF_WHITE,
            alignment=TA_CENTER,
        ),
        "table_cell": ParagraphStyle(
            "table_cell",
            fontSize=9,
            fontName="Helvetica",
            textColor=PDF_DARK,
            alignment=TA_CENTER,
        ),
        "footer": ParagraphStyle(
            "footer",
            fontSize=8,
            fontName="Helvetica",
            textColor=PDF_GREY,
            alignment=TA_CENTER,
        ),
        "insight_bullet": ParagraphStyle(
            "insight_bullet",
            fontSize=10,
            fontName="Helvetica",
            textColor=PDF_DARK,
            leading=16,
            leftIndent=12,
            spaceAfter=4,
        ),
    }


def draw_header_bg(canvas, doc):
    """Draw a gradient-style header banner on every page."""
    canvas.saveState()
    w, h = letter

    # Header rectangle
    canvas.setFillColor(PDF_BLUE)
    canvas.rect(0, h - 110, w, 110, fill=1, stroke=0)

    # Teal accent strip at bottom of header
    canvas.setFillColor(PDF_TEAL)
    canvas.rect(0, h - 115, w, 5, fill=1, stroke=0)

    # Footer line
    canvas.setStrokeColor(colors.HexColor("#E5E7EB"))
    canvas.setLineWidth(0.5)
    canvas.line(inch * 0.75, 48, w - inch * 0.75, 48)

    # Footer text
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(PDF_GREY)
    canvas.drawCentredString(
        w / 2, 34,
        "NYC Airbnb Market Intelligence Dashboard  •  Generated automatically"
    )
    canvas.drawRightString(
        w - inch * 0.75, 34,
        f"Page {doc.page}"
    )

    canvas.restoreState()


@app.callback(

    Output("download-pdf", "data"),

    [
        Input("pdf-btn", "n_clicks"),
    ],

    [
        State("borough-dropdown", "value"),
        State("room-dropdown",    "value"),
        State("price-slider",     "value"),
    ],

    prevent_initial_call=True
)

def export_pdf(n, boroughs, rooms, prices):

    boroughs = boroughs or list(ALL_BOROUGHS)
    rooms    = rooms    or list(ALL_ROOMS)
    filtered = filter_df(boroughs, rooms, prices)

    styles = build_pdf_styles()

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=130,          # space for header banner
        bottomMargin=70,
        leftMargin=inch * 0.75,
        rightMargin=inch * 0.75,
    )

    W = letter[0] - inch * 1.5   # usable width

    story = []

    # --------------------------------------------------
    # PAGE 1 HEADER CONTENT (sits inside the blue banner
    # via topMargin; we place it as first story items)
    # --------------------------------------------------
    # The blue banner is drawn by draw_header_bg.
    # We overlay white text on it using a table with
    # a transparent background placed at the very top.

    header_title = Paragraph(
        "NYC Airbnb Market Intelligence",
        styles["report_title"]
    )
    header_sub = Paragraph(
        "Comprehensive analytics report · 2019 dataset",
        styles["report_subtitle"]
    )

    # Negative top spacer pulls content into the banner area
    story.append(Spacer(1, -90))
    story.append(header_title)
    story.append(Spacer(1, 4))
    story.append(header_sub)
    story.append(Spacer(1, 50))

    # --------------------------------------------------
    # ACTIVE FILTERS SUMMARY
    # --------------------------------------------------
    story.append(
        Paragraph("Active Filters", styles["section_heading"])
    )
    story.append(
        HRFlowable(
            width="100%", thickness=1,
            color=colors.HexColor("#E5E7EB"), spaceAfter=8
        )
    )

    boroughs_str = ", ".join(boroughs) if boroughs else "None"
    rooms_str    = ", ".join(rooms)    if rooms    else "None"

    story.append(
        Paragraph(
            f"<b>Boroughs:</b> {boroughs_str}",
            styles["body"]
        )
    )
    story.append(
        Paragraph(
            f"<b>Room Types:</b> {rooms_str}",
            styles["body"]
        )
    )
    story.append(
        Paragraph(
            f"<b>Price Range:</b> ${prices[0]} – ${prices[1]}",
            styles["body"]
        )
    )
    story.append(Spacer(1, 10))

    # --------------------------------------------------
    # KPI CARDS (2 × 2 grid via Table)
    # --------------------------------------------------
    story.append(
        Paragraph("Key Performance Indicators", styles["section_heading"])
    )
    story.append(
        HRFlowable(
            width="100%", thickness=1,
            color=colors.HexColor("#E5E7EB"), spaceAfter=10
        )
    )

    if filtered.empty:
        story.append(Paragraph("No data available for selected filters.", styles["body"]))
    else:
        avg_price    = filtered["price"].mean()
        total        = len(filtered)
        occupancy    = filtered["occupancy_rate"].mean()
        avg_reviews  = filtered["number_of_reviews"].mean()

        def kpi_cell(label, value, sub=""):
            return [
                Paragraph(label, styles["kpi_label"]),
                Paragraph(value, styles["kpi_value"]),
                Paragraph(sub,   styles["kpi_sub"]),
            ]

        kpi_data = [
            [
                kpi_cell("TOTAL LISTINGS",  f"{total:,}",          "Active listings"),
                kpi_cell("AVERAGE PRICE",   f"${avg_price:.0f}",   "Per night"),
                kpi_cell("OCCUPANCY RATE",  f"{occupancy:.1f}%",   "Estimated"),
                kpi_cell("AVG REVIEWS",     f"{avg_reviews:.0f}",  "Per listing"),
            ]
        ]

        kpi_col_w = W / 4

        kpi_table = Table(kpi_data, colWidths=[kpi_col_w] * 4)

        kpi_table.setStyle(TableStyle([
            ("BOX",         (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("INNERGRID",   (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [PDF_LIGHT, PDF_LIGHT]),
            ("TOPPADDING",  (0, 0), (-1, -1), 14),
            ("BOTTOMPADDING",(0, 0),(-1, -1), 14),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",(0, 0), (-1, -1), 8),
            ("ROUNDEDCORNERS", (0, 0), (-1, -1), [6, 6, 6, 6]),
        ]))

        story.append(kpi_table)
        story.append(Spacer(1, 16))

    # --------------------------------------------------
    # AUTOMATED INSIGHTS
    # --------------------------------------------------
    story.append(
        Paragraph("Automated Business Insights", styles["section_heading"])
    )
    story.append(
        HRFlowable(
            width="100%", thickness=1,
            color=colors.HexColor("#E5E7EB"), spaceAfter=8
        )
    )

    if not filtered.empty:
        bp = filtered.groupby("neighbourhood_group")["price"].mean()
        top_borough = bp.idxmax() if not bp.empty else "N/A"

        mode_vals = filtered["room_type"].mode()
        top_room  = mode_vals[0] if not mode_vals.empty else "N/A"

        br = filtered.groupby("neighbourhood_group")["number_of_reviews"].mean()
        busiest = br.idxmax() if not br.empty else "N/A"

        insights = [
            f"&#9654;  <b>{top_borough}</b> has the highest average Airbnb pricing among the selected boroughs.",
            f"&#9654;  Average nightly price across all filtered listings is <b>${filtered['price'].mean():.0f}</b>.",
            f"&#9654;  Most common room type is <b>{top_room}</b>, reflecting dominant market supply.",
            f"&#9654;  <b>{busiest}</b> shows the highest customer engagement based on average review count.",
            f"&#9654;  {len(filtered):,} active listings match the current filter criteria.",
        ]

        for line in insights:
            story.append(Paragraph(line, styles["insight_bullet"]))
    else:
        story.append(Paragraph("No data to generate insights.", styles["body"]))

    story.append(Spacer(1, 16))

    # --------------------------------------------------
    # BOROUGH BREAKDOWN TABLE
    # --------------------------------------------------
    story.append(
        Paragraph("Borough Breakdown", styles["section_heading"])
    )
    story.append(
        HRFlowable(
            width="100%", thickness=1,
            color=colors.HexColor("#E5E7EB"), spaceAfter=10
        )
    )

    if not filtered.empty:
        borough_stats = (
            filtered.groupby("neighbourhood_group")
            .agg(
                Listings  = ("id",                "count"),
                Avg_Price = ("price",             "mean"),
                Occupancy = ("occupancy_rate",    "mean"),
                Avg_Reviews=("number_of_reviews", "mean"),
            )
            .reset_index()
            .sort_values("Avg_Price", ascending=False)
        )

        col_labels = [
            Paragraph("Borough",      styles["table_header"]),
            Paragraph("Listings",     styles["table_header"]),
            Paragraph("Avg Price",    styles["table_header"]),
            Paragraph("Occupancy",    styles["table_header"]),
            Paragraph("Avg Reviews",  styles["table_header"]),
        ]
        table_data = [col_labels]

        for _, row in borough_stats.iterrows():
            table_data.append([
                Paragraph(row["neighbourhood_group"],      styles["table_cell"]),
                Paragraph(f"{int(row['Listings']):,}",    styles["table_cell"]),
                Paragraph(f"${row['Avg_Price']:.0f}",     styles["table_cell"]),
                Paragraph(f"{row['Occupancy']:.1f}%",     styles["table_cell"]),
                Paragraph(f"{row['Avg_Reviews']:.0f}",    styles["table_cell"]),
            ])

        col_widths = [W * 0.28, W * 0.16, W * 0.18, W * 0.18, W * 0.20]

        tbl = Table(table_data, colWidths=col_widths, repeatRows=1)

        tbl.setStyle(TableStyle([
            # Header row
            ("BACKGROUND",   (0, 0), (-1, 0),  PDF_BLUE),
            ("TEXTCOLOR",    (0, 0), (-1, 0),  PDF_WHITE),
            ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, 0),  9),
            ("TOPPADDING",   (0, 0), (-1, 0),  10),
            ("BOTTOMPADDING",(0, 0), (-1, 0),  10),
            # Alternating rows
            ("ROWBACKGROUNDS",(0, 1),(-1, -1), [PDF_WHITE, PDF_LIGHT]),
            ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",     (0, 1), (-1, -1), 9),
            ("TOPPADDING",   (0, 1), (-1, -1), 8),
            ("BOTTOMPADDING",(0, 1), (-1, -1), 8),
            # Grid
            ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
            ("LINEBELOW",    (0, 0), (-1, 0),  1.5, PDF_TEAL),
        ]))

        story.append(tbl)
        story.append(Spacer(1, 16))

    # --------------------------------------------------
    # ROOM TYPE BREAKDOWN TABLE
    # --------------------------------------------------
    story.append(
        Paragraph("Room Type Breakdown", styles["section_heading"])
    )
    story.append(
        HRFlowable(
            width="100%", thickness=1,
            color=colors.HexColor("#E5E7EB"), spaceAfter=10
        )
    )

    if not filtered.empty:
        room_stats = (
            filtered.groupby("room_type")
            .agg(
                Listings   = ("id",    "count"),
                Avg_Price  = ("price", "mean"),
                Min_Price  = ("price", "min"),
                Max_Price  = ("price", "max"),
            )
            .reset_index()
            .sort_values("Listings", ascending=False)
        )

        col_labels_r = [
            Paragraph("Room Type",   styles["table_header"]),
            Paragraph("Listings",    styles["table_header"]),
            Paragraph("Avg Price",   styles["table_header"]),
            Paragraph("Min Price",   styles["table_header"]),
            Paragraph("Max Price",   styles["table_header"]),
        ]
        table_data_r = [col_labels_r]

        for _, row in room_stats.iterrows():
            table_data_r.append([
                Paragraph(row["room_type"],              styles["table_cell"]),
                Paragraph(f"{int(row['Listings']):,}",  styles["table_cell"]),
                Paragraph(f"${row['Avg_Price']:.0f}",   styles["table_cell"]),
                Paragraph(f"${row['Min_Price']:.0f}",   styles["table_cell"]),
                Paragraph(f"${row['Max_Price']:.0f}",   styles["table_cell"]),
            ])

        tbl_r = Table(table_data_r, colWidths=col_widths, repeatRows=1)

        tbl_r.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0),  PDF_TEAL),
            ("TEXTCOLOR",    (0, 0), (-1, 0),  PDF_WHITE),
            ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, 0),  9),
            ("TOPPADDING",   (0, 0), (-1, 0),  10),
            ("BOTTOMPADDING",(0, 0), (-1, 0),  10),
            ("ROWBACKGROUNDS",(0, 1),(-1, -1), [PDF_WHITE, PDF_LIGHT]),
            ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",     (0, 1), (-1, -1), 9),
            ("TOPPADDING",   (0, 1), (-1, -1), 8),
            ("BOTTOMPADDING",(0, 1), (-1, -1), 8),
            ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
            ("LINEBELOW",    (0, 0), (-1, 0),  1.5, PDF_BLUE),
        ]))

        story.append(tbl_r)

    # --------------------------------------------------
    # BUILD
    # --------------------------------------------------

    doc.build(
        story,
        onFirstPage=draw_header_bg,
        onLaterPages=draw_header_bg,
    )

    pdf = buffer.getvalue()
    buffer.close()

    return dict(
        content=base64.b64encode(pdf).decode(),
        filename="nyc_airbnb_report.pdf",
        base64=True
    )

# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":
    app.run(debug=True, port=8050)
