from dash import Dash, html, dcc, callback, Output, Input, State, dash_table, ALL
import dash_daq as daq
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import base64
import chart_studio.plotly as py
import chart_studio.tools
from classesIET import figureIET
import io
import plotly.graph_objects as go
from base64 import standard_b64decode, b64decode, b64encode

# Setting dash credentials for the server
chart_studio.tools.set_credentials_file(username='domrivest', api_key='X4rnV82LxBFDOuKSEN6x')


df_colors = pd.read_csv('assets/colors.csv')
colordict = dict(zip(df_colors.variable, df_colors.color))
frDict = dict(zip(df_colors.variable, df_colors.label_fr))
enDict = dict(zip(df_colors.variable, df_colors.label_en))


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', 'https://fonts.googleapis.com/css2?family=News+Cycle&display=swap']
app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

nbDccDownload = 100 # Nombre de figures pouvant être téléchargées simultanément

# Liste des figures
listeFigures = []
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
            html.Button("Télélécharger en lot", id='download-button'),
            *[
                dcc.Download(id={"type": 'download', "index": i}) for i in range(nbDccDownload) # 100 figures à télécharger maximum
            ],
            dcc.Dropdown(['png', 'svg', 'pdf'], placeholder= "Sélectionnez le format pour l'export en lot", id='downloadFormatdd', style={'width': '340px'}),
            #html.I("Renseignez à droite le préfixe pour l'export dans ChartStudio."),
            dcc.Input(id="prefixeChartStudio", type="text", placeholder="Préfixe pour Chart-Studio", style={'marginRight':'10px'}, value=str()),
            dbc.Button("Publier dans Chart-Studio", id='boutonChartStudio', color="primary", n_clicks=0),
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
    html.Div(id="placeholderChartStudio")
])

def parse_contents(contents, filename, date, isFrench, isDim, isSource, showTitle): #, downloadFormat, downloadAll):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'txt' in filename:
            graph = figureIET(decoded, colordict, frDict, enDict, isFrench, isDim, isSource, showTitle)
            listeFigures.append(graph)
    except Exception as e:
        print(e)
        return html.Div([
            'Il y a eu une erreur en traitant ce fichier : '+str(e)
        ])
    
    if isFrench:
        langue = 'fr'
    else:
        langue = 'en'
        
    graph.filename = filename.replace('.txt', '')
    listeFigures.append(graph)
    configOptions = {'toImageButtonOptions':{'format':'png', 'scale':10, 'filename':filename.replace('.txt', '')}, 'locale':langue}

    return dcc.Graph(id=str([filename, date]), figure=graph.fig, config=configOptions, className="figure")

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
              prevent_initial_call = True)
def update_output(list_of_contents, list_of_names, list_of_dates, isFrench, isDim, isSource, showTitle):#, downloadFormat, downloadAll):
    listeFigures = []
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d, isFrench, isDim, isSource, showTitle) for c, n, d in   #, downloadFormat, downloadAll) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children, None, None
    
def fig_to_data(graph, formatDownload) -> dict:
    buffer = io.BytesIO()
    # Sélection du format et application du facteur d'échelle aux png
    if formatDownload == 'png':
        graph.fig.write_image(buffer, format='png', scale= 10)
    elif formatDownload == 'svg':
        graph.fig.write_image(buffer, format='svg')
    elif formatDownload == 'pdf':
        graph.fig.write_image(buffer, format='pdf')
    buffer.seek(0)
    encoded = base64.b64encode(buffer.getvalue())
    returnDict = {
        "content": encoded.decode(),
        "filename": graph.filename+'.'+formatDownload,
        "base64": True
    }
    return returnDict 

# Effacement des figures
@callback(
    Output('output-data-upload', 'children'),
    Input('boutonEffacer', 'n_clicks'),
    prevent_initial_call=True
)
def update_output(n_clicks):
    listeFigures = []
    return None

# Téléchargement en lot des figures
@callback(
    Output({"type": "download", "index": ALL}, "data"),
    [
        Input("download-button", "n_clicks"),
        State("downloadFormatdd", "value"),
    ],
    prevent_initial_call=True
)
def download_figure(n_clicks, formatDownload):
    retourDownload = []
    for i in range(nbDccDownload):
        if i in range(len(listeFigures)):
            retourDownload.append(fig_to_data(listeFigures[i], formatDownload))
        else:
            retourDownload.append(None)
    return retourDownload

@callback(
    Output('placeholderChartStudio', 'children'),
    Input('boutonChartStudio', 'n_clicks'),
    State("prefixeChartStudio", "value"),
    prevent_initial_call=True
)
def update_output(n_clicks, prefixe):
    for i in range(len(listeFigures)):
        graph = listeFigures[i]
        py.plot(graph.fig, filename=str(prefixe)+graph.filename, auto_open=False)
    return None

if __name__ == '__main__':
    app.run(debug=True)
