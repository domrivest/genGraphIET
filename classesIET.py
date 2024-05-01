import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import numpy as np
from io import StringIO  
import chardet

class figureIET:
  def __init__(self, decoded, colordict, frDict, enDict, isFrench, isDim, isSource, showTitle, fontSize):

   # Plotly default theme
   pio.templates.default = "plotly_white"
      
   the_encoding = chardet.detect(decoded)['encoding']
   try:   
      file = decoded.decode(the_encoding.lower())   
   except:
      print("Le décodage ne fonctionne pas")

   header_dict = {}
   header_height = 0
   # Split the header into individual lines
   for line in file.splitlines():
      # Split each line into components and remove \n
      line = line.replace('\n', '')
      components = line.split(';')
      
      if components[0] == 'metadata':
         header_height = header_height + 1

      # Remove empty components
      components = list(filter(None, components))

      if len(components) == 3 and components[0] == 'metadata':
            key = components[1]
            value = components[2]

            # Add the key-value pair to the dictionary
            header_dict[key] = value
        
   df = pd.read_csv(StringIO(file), encoding=the_encoding.lower(), header=header_height, sep=';')
   df = df.drop(['data'], axis=1)

   # Ajouts des valeurs à la classe
   self.metadataDict = header_dict
   self.df = df

   match self.metadataDict['chart.type']:
      case 'area':
         self.fig=px.area(self.df, x=self.df.columns[0], y=self.df.columns, color_discrete_map=colordict)
         self.fig.for_each_trace(lambda trace: trace.update(fillcolor = trace.line.color))
         self.fig.update_annotations()
         #self.fig.update_xaxes(type='category')

      case 'bar.grouped.horizontal':
         self.df[self.df.columns[1]] = self.df[self.df.columns[1]].astype('str')
         self.fig = px.bar(self.df, y=self.df.columns[0], x=self.df.columns, color=df.columns[1], color_discrete_map=colordict, barmode='group', orientation='h')
         self.fig.update_layout(yaxis=dict(autorange="reversed"))

      case 'bar.grouped.stacked':
      #   if self.df.iloc[0 ,1] == '-':
      #     # Création de subplots
      #     subplotsIndex = df[df.columns[0]].unique().tolist()
      #     self.fig = make_subplots(rows = 1, cols = len(subplotsIndex), subplot_titles=subplotsIndex)
      #     self.fig.update_layout(barmode = "stack")
      #     self.fig.update_xaxes(type='category')
      #     for i in subplotsIndex:
      #        dfr = df[df[df.columns[0]] == i].transpose()
      #        self.fig.add_trace(
      #           go.Bar(
      #             x = dfr.iloc[1, :], y=dfr.iloc[2:, :]
      #           ),
      #        row = 1, col = subplotsIndex.index(i)+1)
      #   else:
         self.fig = px.bar(self.df, x=self.df.columns[1], y=self.df.columns, facet_col=self.df.columns[0], color_discrete_map=colordict, barmode='stack')
         self.fig.update_layout(legend_traceorder="reversed")
         self.fig.update_xaxes(type='category')
         self.fig.update_xaxes(matches=None)
         self.fig.for_each_annotation(lambda a: a.update(text="")) #a.text.split("=")[-1])) Empty title text
         self.fig.update_layout(xaxis_title=self.df[self.df.columns[0]].unique().tolist()[0])
         for axis in self.fig.layout:
            if type(self.fig.layout[axis]) == go.layout.XAxis:
               if axis.split("s")[-1] == '':
                     self.fig.layout[axis].title.text = self.df[self.df.columns[0]].unique().tolist()[0]
               elif int(axis.split("s")[-1]) <= (len(self.df[self.df.columns[0]].unique().tolist())):
                  self.fig.layout[axis].title.text = self.df[self.df.columns[0]].unique().tolist()[int(axis.split("s")[-1])-1]


      case 'bar.stacked':
         self.fig = px.bar(self.df, x=self.df.columns[0], y=self.df.columns, color_discrete_map=colordict, barmode='stack')
         self.fig.update_xaxes(type='category')
         
      case 'bar.grouped':
         self.df[self.df.columns[1]] = self.df[self.df.columns[1]].astype('str')
         self.fig = px.bar(self.df, x=self.df.columns[0], y=self.df.columns[2], color=self.df.columns[1], color_discrete_map=colordict, barmode='group')
         self.fig.update_xaxes(type='category')

      case 'line':
         self.fig = px.line(self.df, x=self.df.columns[1], y=self.df.columns[2], color=self.df.columns[0], color_discrete_map=colordict, markers=True)

      case 'scatter':
         self.fig = px.scatter(self.df, x=self.df.columns[1], y=self.df.columns[2], color=self.df.columns[0], color_discrete_map=colordict)

      case 'pie':
         #self.df[self.df.columns[1]] = self.df[self.df.columns[1]].apply(lambda x: x.replace(' ', '')) # Si espace 
         self.df[self.df.columns[1]] = self.df[self.df.columns[1]].astype('float')
         if isFrench:
            frList=[frDict[k] for k in df[df.columns[0]].tolist() if k in frDict]
            self.df['namesFr'] = frList
            self.fig = px.pie(self.df, values=self.df.columns[1], names='namesFr', color=self.df.columns[0], color_discrete_map=colordict)
            self.fig.update_layout(legend_title = 'Légende')
            self.fig.update_layout(separators='. ')
         else:
            enList=[enDict[k] for k in df[df.columns[0]].tolist() if k in enDict]
            self.df['namesEn'] = enList
            self.fig = px.pie(self.df, values=self.df.columns[1], names='namesEn', color=self.df.columns[0], color_discrete_map=colordict)
            self.fig.update_layout(legend_title = 'Legend')
         # Ajouts des hoverinfo et textinfo s'ils existent
         try:
            self.fig.update_traces(textinfo = self.metadataDict['chart.textinfo'])
         except: None
         try:
            self.fig.update_traces(hoverinfo = self.metadataDict['chart.hoverinfo'])
         except: None


      case _:
         print("Ce type de graphique n'est pas défini")

   # Changer le type d'axe si spécifié, ntcicks et ticks val
   # Axe X
   try: 
      self.fig.update_xaxes(type = self.metadataDict['xaxes.type']) # ( "-" | "linear" | "log" | "date" | "category" | "multicategory" ) 
   except: None
   try:
      self.fig.update_xaxes(nticks = self.metadataDict['xaxes.nticks']) 
   except: None
   try:
      self.fig.update_xaxes(tickmode = self.metadataDict['xaxes.tickmode'], tick0=int(self.metadataDict['xaxes.tick0']), dtick=int(self.metadataDict['xaxes.dtick'])) # int
   except: None
   try:
      self.fig.update_xaxes(tickvals = [int(ele) for ele in self.metadataDict['xaxes.tickvals'].split(',')]) # 2020, 2022
   except: None

   try: # Axe Y
      self.fig.update_yaxes(type = self.metadataDict['yaxes.type']) 
   except: None
   try:
      self.fig.update_yaxes(nticks = self.metadataDict['yaxes.nticks']) 
   except: None
   try:
      self.fig.update_yaxes(tickmode = self.metadataDict['yaxes.tickmode'], tick0=int(self.metadataDict['yaxes.tick0']), dtick=int(self.metadataDict['yaxes.dtick'])) # int
   except: None
   try:
      self.fig.update_yaxes(tickvals = [int(ele) for ele in self.metadataDict['yaxes.tickvals'].split(',')]) # 2020, 2022
   except: None

   # Changer l'angle de rotation des labels de l'axe si spécifié
   try: # axe x
      self.fig.update_xaxes(tickangle=int(self.metadataDict['xaxes.tickangle']))
   except: None
   try: # axe y
      self.fig.update_yaxes(tickangle=int(self.metadataDict['yaxes.tickangle']))
   except: None
   
   
   # Si français - Changer les noms de variables
   if isFrench and not self.metadataDict['chart.type'] == 'pie':
      self.fig.for_each_trace(lambda t: t.update(name = frDict[t.name],
                                      legendgroup = frDict[t.name],
                                      hovertemplate = t.hovertemplate.replace(t.name, frDict[t.name])
                                     )
         )
      self.fig.update_layout(legend_title = '')#'Légende')
      self.fig.update_layout(separators='. ') # Changer le séparateur de centaines
   elif not self.metadataDict['chart.type'] == 'pie':
      self.fig.for_each_trace(lambda t: t.update(name = enDict[t.name],
                                      legendgroup = enDict[t.name],
                                      hovertemplate = t.hovertemplate.replace(t.name, enDict[t.name])
                                     )
         )
      self.fig.update_layout(legend_title = '')#'Legend')
   else:
      #self.fig.update_layout(legend_title = '')#'Legend')
      None

   # Ajouts des noms d'axes s'ils existent
   try:
      self.fig.update_layout(yaxis_title = self.metadataDict['chart.yLabel'])
   except:
      self.fig.update_layout(yaxis_title = "")
   if not self.metadataDict['chart.type'] == 'bar.grouped.stacked': # Ne pas conserver pour bar.grouped.stacked (labels importants)
      try:
         self.fig.update_layout(xaxis_title = self.metadataDict['chart.xLabel'])
      except:
         self.fig.update_layout(xaxis_title = "")

   # Changer l'ordre de la légende si non pie et non bar.grouped et grouped.stacked
   if not self.metadataDict['chart.type'] in ['pie', 'bar.grouped', 'bar.grouped.stacked', 'bar.grouped.horizontal']:
      self.fig.update_layout(legend_traceorder="reversed")

   # Ajouter pad axe y
   self.fig.update_layout(margin_pad=5)

   # Modifier le format de l'axe des y (pas de k pour les milliers)
   if isFrench:
      self.fig.update_layout(yaxis_tickformat = ',')
   else:
      self.fig.update_layout(yaxis_tickformat = ',')

   # Contraindre les dimensions is isDim est vrai
   if isDim:
      self.fig.update_layout(
         width = 1000,
         height = 400
      )

   # Montrer le titre si il est renseigné
   if showTitle:
      try:
         self.fig.update_layout(title_text = self.metadataDict['chart.title'], title_x=0.5)
      except:
         print("Cette figure n'a pas de titre")

   # Montrer la source si elle est renseignée
   if isSource:
      try:
         self.fig.update_layout(title = self.metadataDict['chart.title'])
         # HOW TO ADD A FOOTNOTE TO BOTTOM LEFT OF PAGE
         self.fig.add_annotation(
            text = (f"Source: {self.metadataDict['chart.source']}")
            , showarrow=False
            , x = 0
            , y = -0.15
            , xref='paper'
            , yref='paper' 
            , xanchor='left'
            , yanchor='bottom'
            , xshift=-1
            , yshift=-5
            , font=dict(size=10, color="grey")
            , align="left"
            ,)
      except:
         print("Cette figure n'a pas de source")

   self.fig.update_layout(
   font_family="News Cycle",
   font_size=fontSize,
   font_color="black",
   title_font_family="News Cycle",
   title_font_color="black",
   legend_title_font_color="black"
   )
      



