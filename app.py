import os
import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import openpyxl

# Load the dataset
data_path = os.path.join(os.path.dirname(__file__), 'RAI_Measures_Dataset.xlsx')
dropped_df = pd.read_excel(data_path)
dropped_df.columns = dropped_df.iloc[0]  # Use the second row as the column names
dropped_df = dropped_df.iloc[1:]  # Remove the first two rows

# SECTION: GROUP THE COLUMNS FOR THE SUNBURST DIAGRAM
subset_df_process = dropped_df[
    ['Principle', 'Component of the ML System', 'Measure', 'Measurement Process',
     'Lead Author(s)', 'Title', 'Type of Assessment', 'Application Area', 'Publication Year']
]

# Group the data
grouped_df_process = subset_df_process.groupby(
    ['Principle', 'Component of the ML System', 'Measurement Process',
     'Lead Author(s)', 'Title', 'Type of Assessment', 'Application Area', 'Publication Year']
)['Measure'].apply(list).reset_index()

grouped_df_process['Principle'] = grouped_df_process['Principle'].astype(str).str.split(', ')
grouped_df_process['Component of the ML System'] = grouped_df_process['Component of the ML System'].astype(str).str.split(', ')

grouped_df_process = grouped_df_process.explode('Principle')
grouped_df_process = grouped_df_process.explode('Component of the ML System')

grouped_df_process['Principle'] = grouped_df_process['Principle'].str.strip()
grouped_df_process['Component of the ML System'] = grouped_df_process['Component of the ML System'].str.strip()

grouped_df_process['Measure'] = grouped_df_process['Measure'].apply(
    lambda x: x if isinstance(x, list) else [x]
)
grouped_df_process = grouped_df_process.explode('Measure')
grouped_df_process['Measure'] = grouped_df_process['Measure'].str.strip()

# Add hover text
grouped_df_process['Hover_Text'] = grouped_df_process.apply(
    lambda row: f"<b>{row['Measure']}</b><br>Measurement Process: {row['Measurement Process']}"
    if pd.notna(row['Measurement Process'])
    else f"<b>{row['Principle']}</b>",
    axis=1
)

# Sunburst color palette
custom_palette = [
    "#9c0040", "#ff7e3c", "#ff3d54", "#ffc68e", "#e9e807",
    "#87ed2d", "#66c2a5", "#3288bd", "#5e4fa2", "#0a2e58",
    "#adadad"
]

# Create sunburst diagram
fig = px.sunburst(
    grouped_df_process,
    path=["Principle", "Component of the ML System", "Measure"],
    values=None,
    title=" ",
    color="Principle",
    color_discrete_sequence=custom_palette
)

fig.update_traces(
    hovertemplate="<b>%{label}</b><br>Parent: %{parent}<br>Principle: %{customdata[0]}<extra></extra>",
    customdata=fig.data[0].customdata if "customdata" in fig.data[0] else None
)

fig.update_layout(
    margin=dict(l=20, r=20, t=30, b=20),
    height=700,
    width=1500,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        tracegroupgap=10,
        font=dict(family="Source Sans Pro, Arial, sans-serif")
    ),
    uniformtext_minsize=8,
    font=dict(family="Source Sans Pro, Arial, sans-serif")
)

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server  # Expose for deployment

# Layout
app.layout = html.Div(
    style={"font-family": "Source Sans Pro, Arial, sans-serif", "margin": "20px"},
    children=[
        html.H1(
            "Responsible AI Measures Dataset",
            style={"text-align": "center", "color": "#151417"}
        ),
        html.Div(
            id='click-output',
            style={
                "margin-bottom": "20px",
                "font-size": "16px",
                "color": "#151417",
                "text-align": "left"
            }
        ),
        dcc.Graph(
            id='sunburst-chart',
            figure=fig,
            config={'displayModeBar': False}
        )
    ]
)

# Callback logic
@app.callback(
    Output('click-output', 'children'),
    Input('sunburst-chart', 'clickData')
)
def display_click_data(clickData):
    if clickData is None:
        return html.Div([
            html.B("Instructions for Use:"),
            html.Ul([
                html.Li("Please select a principle, then the ML system component you are interested in."),
                html.Li("Hover to see the current level, the parent level, and the associated principle."),
                html.Li("Click on a measure to view its associated measurement process."),
                html.Li("Use the metadata to trace the publication for deeper understanding of the measure.")
            ]),
            html.I("Some processes include paper-specific terminology or formulas. Use the paper title and author for additional context.")
        ])

    clicked_label = clickData['points'][0]['label']
    if clicked_label in grouped_df_process['Measure'].values:
        row = grouped_df_process.loc[grouped_df_process['Measure'] == clicked_label].iloc[0]

        return html.Div([
            html.B(f"{clicked_label}: "), html.Span(row['Measurement Process']),
            html.Br(), html.Br(),
            html.B("Paper Title: "), html.Span(row['Title']),
            html.Br(),
            html.B("Lead Author(s): "), html.Span(row['Lead Author(s)']),
            html.Br(),
            html.B("Publication Year: "), html.Span(row['Publication Year']),
            html.Br(), html.Br(),
            html.B("Type of Assessment: "), html.Span(row['Type of Assessment']),
            html.Br(), html.B("Application Area: "), html.Span(row['Application Area']),
            html.Br(), html.Br(),
            html.I("Please consult the original publication for technical formulas or terms.")
        ])
    else:
        return html.Span(
            "Please click on an RAI Measure in the last tier.",
            style={"font-family": "Source Sans Pro, Arial, sans-serif"}
        )

# Run the app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8051))
    app.run_server(host='0.0.0.0', port=port)

