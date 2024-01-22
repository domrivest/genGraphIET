from dash import Dash, html, dcc, callback, Output, Input, State, dash_table
import dash_daq as daq
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import base64
import datetime
from classesIET import figureIET
import io


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
        )], style={'display': 'flex', 'justifyContent': 'space-between', 'padding': 10}),
        html.Div([
            # daq.ToggleSwitch(
            # id='downloadAll',
            # value=False,
            # label="Télécharger toutes les figures dans le format spécifié lors du téléversement",
            # labelPosition='top'
            # ),
            # dcc.Dropdown(['png', 'svg', 'pdf'], 'png', id='downloadFormatdd'),
            dbc.Button("Effacer les graphiques", id='boutonEffacer', color="primary", n_clicks=0),
        ], style={'display': 'flex', 'justifyContent': 'space-around', 'padding': 10}),
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

def parse_contents(contents, filename, date, isFrench, isDim, isSource, showTitle): #, downloadFormat, downloadAll):
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
        
    configOptions = {'toImageButtonOptions':{'format':'png', 'scale':10, 'filename':filename.replace('.txt', '')}, 'locale':langue}

    # if downloadAll: # Si le bouton download est activé
    #     if downloadFormat == 'png':
    #         graph.fig.write_image(filename.replace('.txt', '.'+ downloadFormat), format=downloadFormat, scale=10)
    #         in_memory_image = graph.fig.to_image(format=downloadFormat, engine="kaleido", scale=10)
    #         dcc.Download(id = str([filename, date]), data=dcc.send_bytes(in_memory_image, filename=filename.replace('.txt', '.'+downloadFormat)))
    #     else:
    #         graph.fig.write_image(filename.replace('.txt', '.'+downloadFormat), format=downloadFormat)

    return dcc.Graph(id=str([filename, date]), figure=graph.fig, config=configOptions)

@callback(Output('output-data-upload', 'children', allow_duplicate=True),
              Output('upload-data', 'contents'),
              Output('upload-data', 'filename'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'),
              State('isFrenchToggle', 'value'),
              State('dimensionsToggle', 'value'),
              State('sourceToggle', 'value'),
              State('showTitle', 'value'),
            #   State('downloadFormatdd', 'value'),
            #   State('downloadAll', 'value'),
              prevent_initial_call = True)
def update_output(list_of_contents, list_of_names, list_of_dates, isFrench, isDim, isSource, showTitle):#, downloadFormat, downloadAll):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d, isFrench, isDim, isSource, showTitle) for c, n, d in   #, downloadFormat, downloadAll) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children, None, None
    
@callback(
    Output('output-data-upload', 'children'),
    Input('boutonEffacer', 'n_clicks'),
    prevent_initial_call=True
)
def update_output(n_clicks):
    return None

if __name__ == '__main__':
    app.run(debug=True)
