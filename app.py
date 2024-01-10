from dash import Dash, html, dcc, callback, Output, Input, State, dash_table
import dash_daq as daq
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import base64
import datetime
from classesIET import figureIET


df_colors = pd.read_csv('assets/colors.csv')
colordict = dict(zip(df_colors.variable, df_colors.color))
frDict = dict(zip(df_colors.variable, df_colors.label_fr))
enDict = dict(zip(df_colors.variable, df_colors.label_en))


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', 'https://fonts.googleapis.com/css2?family=News+Cycle&display=swap']

app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div([
    html.H1(
        children='Outil de génération de graphiques - IET',
        style={
            'textAlign': 'center',
        }
    ),
    html.Div([
        daq.ToggleSwitch(
            id='isFrenchToggle',
            value=False,
            label='Produire les graphiques en Français',
            labelPosition='top'
        ),
        daq.ToggleSwitch(
            id='dimensionsToggle',
            value=True,
            label='Contraindre les dimensions des graphiques à 1000x400 pixels',
            labelPosition='top'
        ),
        daq.ToggleSwitch(
            id='sourceToggle',
            value=False,
            label="Afficher la source lorsqu'elle est renseignée dans le fichier",
            labelPosition='top'
        ),
        daq.ToggleSwitch(
            id='showTitle',
            value=False,
            label="Afficher le titre lorsqu'il est renseigné dans le fichier",
            labelPosition='top'
        ),
        dbc.Button("Effacer les graphiques", id='boutonEffacer', color="primary", n_clicks=0),
    ], style={'display': 'flex', 'justifyContent': 'space-between', 'padding': 10}),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
    html.Div(id='output-data-upload'),
])

def parse_contents(contents, filename, date, isFrench, isDim, isSource, showTitle):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'txt' in filename:
            graph = figureIET(decoded, colordict, frDict, enDict, isFrench, isDim, isSource, showTitle)
    except Exception as e:
        print(e)
        return html.Div([
            'Il y a eu une erreur en traitant ce fichier : '+str(e)
        ])
    
    if isFrench:
        langue = 'fr'
    else:
        langue = 'en'

    return dcc.Graph(id=str([filename, date]), figure=graph.fig, config={'toImageButtonOptions':{'filename':filename.replace('.txt', '')},  'locale':langue})
    #     html.Div([
    #     html.H5(filename),
    #     html.H6(datetime.datetime.fromtimestamp(date)),

    #     dash_table.DataTable(
    #         graph.df.to_dict('records'),
    #         [{'name': i, 'id': i} for i in graph.df.columns]
    #     ),

    #     html.Hr(),  # horizontal line

    #     # For debugging, display the raw contents provided by the web browser
    #     html.Div('Raw Content'),
    #     html.Pre(contents[0:200] + '...', style={
    #         'whiteSpace': 'pre-wrap',
    #         'wordBreak': 'break-all'
    #     })
    # ]), dcc.Graph(id=str(date), figure=graph.fig)

@callback(Output('output-data-upload', 'children', allow_duplicate=True),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'),
              State('isFrenchToggle', 'value'),
              State('dimensionsToggle', 'value'),
              State('sourceToggle', 'value'),
              State('showTitle', 'value'),
              prevent_initial_call = True)
def update_output(list_of_contents, list_of_names, list_of_dates, isFrench, isDim, isSource, showTitle):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d, isFrench, isDim, isSource, showTitle) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children
    
@callback(
    Output('output-data-upload', 'children'),
    Input('boutonEffacer', 'n_clicks'),
    prevent_initial_call=True
)
def update_output(n_clicks):
    return None
if __name__ == '__main__':
    app.run(debug=True)
