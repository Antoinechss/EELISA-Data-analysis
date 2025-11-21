from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd

jobs_dataset = '/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/eures_jobs_full_withcoordinates.csv'

jobs = pd.read_csv(jobs_dataset)

# Ensure coordinates are split into lat/lon columns
jobs[['lat', 'lon']] = jobs['coordinates'].apply(lambda x: pd.Series(eval(str(x))) if pd.notnull(x) else pd.Series([None, None]))

fields = jobs['field'].dropna().unique()
fields = sorted(fields)

app = Dash(__name__)

app.layout = html.Div([
    html.H4('Working field demand heatmap by location'),
    html.P("Select a working field:"),
    dcc.Dropdown(
        id='field_selector',
        options=[{'label': f, 'value': f} for f in fields],
        value=fields[0],
        multi=False
    ),
    dcc.Graph(id="heatmap"),
])

@app.callback(
    Output("heatmap", "figure"),
    Input("field_selector", "value"))
def display_heatmap(selected_field):
    df_field = jobs[jobs['field'] == selected_field].dropna(subset=['lat', 'lon'])
    fig = px.density_mapbox(
        df_field,
        lat="lat",
        lon="lon",
        z=None,  # No intensity column, just density
        radius=15,  # Increase for smoother heatmap
        center={"lat": 54, "lon": 10},
        zoom=3,
        mapbox_style="carto-positron",
        hover_name="region",
        hover_data=["job_title", "company_name"],
        height=700,
        color_continuous_scale="Viridis"
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig


if __name__ == "__main__":
    app.run(debug=True)