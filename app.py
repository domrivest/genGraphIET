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
import os
from repro_zipfile import ReproducibleZipFile

# Setting dash credentials for the server
chart_studio.tools.set_credentials_file(username=os.environ.get("username"), api_key=os.environ.get("api_key"))

try:
    df_colors = pd.read_excel('assets/colors.xlsx')
    df_colors['variable'] = df_colors['variable'].astype('str')
except:
    print("Il y a un problème avec le fichier colors.xlsx")
    
# try:
#     df_colors = pd.read_csv('assets/colors.csv', sep=";", encoding='latin-1')
#     if len(df_colors.columns) <= 3: df_colors = pd.read_csv('assets/colors.csv')
# except:
#     try:
#         df_colors = pd.read_csv('assets/colors.csv')
#     except:
#         print("Il y a un problème avec le fichier colors.csv")

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
            label='Produire les figures en Français',
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
        html.Div([
            html.Label("Taille de police"),
            dcc.Dropdown([8,9,10,11,12,13,14,15,16,17,18,19,20], value=14, id='fontSizedd', style={'width': '340px'})]),
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'padding': 10}),
        html.Div([
            html.Button("Télélécharger en lot", id='download-button'),
            *[
                dcc.Download(id={"type": 'download', "index": 0}) #for i in range(nbDccDownload) # 100 figures à télécharger maximum
            ],
            dcc.Dropdown(['svg', 'pdf'], value='pdf', id='downloadFormatdd', style={'width': '340px'}), # PNG quand kaleido fonctionnera sur serveur
            #html.I("Renseignez à droite le préfixe pour l'export dans ChartStudio."),
            dcc.Input(id="prefixeChartStudio", type="text", placeholder="Préfixe pour Chart-Studio", style={'marginRight':'10px'}, value=str()),
            dbc.Button("Publier dans Chart-Studio", id='boutonChartStudio', color="primary", n_clicks=0),
            dbc.Button("Effacer les figures", id='boutonEffacer', color="primary", n_clicks=0),
        ], style={'display': 'flex', 'justifyContent': 'space-around', 'padding': 10}),
        dbc.Row([
            html.Div([html.P('Largeur des figures'),
            dcc.Input(id="dimL", type="number", min=1, max=10000, step=1, value=1000)]),
            html.Div([html.P('Hauteur des figures'),
            dcc.Input(id="dimH", type="number", min=1, max=10000, step=1, value=400)]),
            html.Div([html.P('Multiplicateur de la résolution des figures'),
            dcc.Input(id="dimR", type="number", min=1, max=20, step=1, value=10)]),
        ], style={'textAlign': 'center', 'display': 'flex', 'justifyContent': 'space-around', 'padding': 10}),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Glisser-déplacer ou ',
            html.A('Sélectionner des fichiers')
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

def parse_contents(contents, filename, date, isFrench, dimDict, isSource, showTitle, fontSize): #, downloadFormat, downloadAll):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'txt' in filename:
            graph = figureIET(decoded, colordict, frDict, enDict, isFrench, dimDict, isSource, showTitle, fontSize)
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
    configOptions = {'toImageButtonOptions':{'format':'png', 'scale':dimDict['R'], 'filename':filename.replace('.txt', '')}, 'locale':langue}

    return dcc.Graph(id=str([filename, date]), figure=graph.fig, config=configOptions, className="figure")

# Callback du téléversement
@callback(Output('output-data-upload', 'children', allow_duplicate=True),
              Output('upload-data', 'contents'),
              Output('upload-data', 'filename'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'),
              State('isFrenchToggle', 'value'),
              State('dimL', 'value'),
              State('dimH', 'value'),
              State('dimR', 'value'),
              State('sourceToggle', 'value'),
              State('showTitle', 'value'),
              State('fontSizedd', 'value'),
              prevent_initial_call = True)
def update_output(list_of_contents, list_of_names, list_of_dates, isFrench, dimL, dimH, dimR, isSource, showTitle, fontSize):#, downloadFormat, downloadAll):
    global listeFigures
    listeFigures = []
    dimDict = {'L': dimL, 'H': dimH, 'R': dimR}
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d, isFrench, dimDict, isSource, showTitle, fontSize) for c, n, d in   #, downloadFormat, downloadAll) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children, None, None

# Effacement des figures
@callback(
    Output('output-data-upload', 'children'),
    Input('boutonEffacer', 'n_clicks'),
    prevent_initial_call=True
)
def update_output(n_clicks):
    global listeFigures
    listeFigures = []
    return None

# Téléchargement en lot des figures
@callback(
    Output({"type": "download", "index": 0}, "data"),
    Input("download-button", "n_clicks"),
    State("downloadFormatdd", "value"),
    prevent_initial_call=True
)
def download_figure(n_clicks, formatDownload):
    zipBuffer = io.BytesIO() # Contient le zip 
    with ReproducibleZipFile(zipBuffer, "w") as zp:
        for fig in listeFigures:
            buffer = io.BytesIO()
            # Sélection du format et application du facteur d'échelle aux png
            fig.fig.write_image(buffer, format=formatDownload, scale=10) if formatDownload == 'png' else fig.fig.write_image(buffer, format=formatDownload)
            zp.writestr(fig.filename+'.'+formatDownload, data=buffer.getvalue())

    encoded = base64.b64encode(zipBuffer.getvalue())
    return {
    "content": encoded.decode(),
    "filename": "figures.zip",
    "base64": True}

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
