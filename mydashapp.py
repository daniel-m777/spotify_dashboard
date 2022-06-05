import re
import pandas as pd
import plotly.express as px

import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html

from dash.dependencies import Input, Output

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}]
                )
# Set page title
app.title = 'Visualizing Spotify Data'

# Set server for deployment
server = app.server

# ------------------------------------------------------
# Import and clean data
music = pd.read_csv("data_o.csv/data_o.csv")
music.drop_duplicates(inplace=True)
music['explicit_label'] = ['yes' if label == 1 else 'no' for label in music['explicit']]
music['artist_names'] = [re.sub('[\[\]\']', '', str(artist)) for artist in music['artists']]  # clean labels

# SETUP TIME-BASED DATA
year_df = music.groupby(['year']).mean()

# SETUP INDIVIDUAL ARTIST GRAPH DATA
artists_df = music.groupby('artist_names').mean()

# ------------------------------------------------------
# Static Line Chart
static_fig = px.line(year_df,
                     x=year_df.index,
                     y=['valence', 'danceability', 'acousticness', 'energy'],
                     color_discrete_sequence=["#1DB954", "red", '#191414', 'blue'],
                     labels={'variable': 'Song Feature',
                             'valence': 'Valence',
                             'danceability': 'Danceability',
                             'acousticness': 'Acousticness',
                             'energy': 'Energy'}
                     )

# Edit the layout
static_fig.update_xaxes(showspikes=True,
                        spikemode='across',
                        spikesnap='cursor',
                        showline=True,
                        showgrid=True)
static_fig.update_traces(hovertemplate=None)
static_fig.update_layout(title='Average Features Per Year',
                         xaxis_title='Year',
                         yaxis_title='Average',
                         hovermode='x unified',
                         spikedistance=-1
                         )
# ------------------------------------------------------
# App Layout
app.layout = html.Div([

    # First Row - Title
    dbc.Row(
        dbc.Col(html.H1("Spotify Dashboard",
                        className='text-center mb-4',
                        style={'color': 'white',
                               'background': '#1DB954',
                               'padding': '50px 0px 50px 0px'}),
                width=12
                )
    ),
    # 2nd Row - Line Chart
    dbc.Row([

        dbc.Col(
            dcc.Graph(id='my_spotify_linechart', figure=static_fig, style={'margin': 'auto 20px auto 20px'})
            , xs=12, sm=12, md=12, lg=12, xl=12
        )], justify='center'
    ),

    dbc.Row(html.Br()),

    # 3rd row - Bar chart & Scatter Chart
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='most_common_bar_chart',
                      style={'margin': 'auto auto auto 20px'}
                      )
        ], xs=12, sm=12, md=6, lg=6, xl=6
        ),
        dbc.Col([
            dcc.Graph(id='scatter-with-slider',
                      style={'margin': 'auto 20px auto auto'}
                      ),
        ], xs=12, sm=12, md=6, lg=6, xl=6
        )
    ], justify='center'),

    # Add Break
    dbc.Row(html.Br()),

    # SLIDER
    dbc.Row([
        dcc.RangeSlider(
            min=music['year'].min(),
            max=music['year'].max(),
            step=1,
            value=[music['year'].min(), music['year'].max() + 1],
            marks={str(year): str(year) for year in music['year'].unique() if year % 5 == 0},
            id='range-year-slider'
        )
    ]),

    # COMPARING ARTISTS
    dbc.Row(
        dbc.Col(html.H1("Compare Two Artists",
                        className='text-center mb-4',
                        style={'color': 'white',
                               'background': '#1DB954',
                               'padding': '50px 0px 50px 0px'}),
                width=12)
    ),

    # Radar Chart
    dbc.Row([
        # LEFT RADAR
        dbc.Col([

            dcc.Dropdown(id='artist_chosen', options=artists_df.index,
                         value='Pink Floyd',
                         style={'color': 'black'
                                }
                         ),
            dcc.Graph(id='my_radar_chart',
                      figure={},
                      )
        ], xs=12, sm=12, md=5, lg=5, xl=5),

        # RIGHT RADAR
        dbc.Col([

            dcc.Dropdown(id='artist_chosen_2', options=artists_df.index,
                         value='Metallica',
                         style={'color': 'black'}
                         ),
            dcc.Graph(id='my_radar_chart_2',
                      figure={},
                      )
        ], xs=12, sm=12, md=5, lg=5, xl=5)

    ], justify='center'),

    dbc.Row(html.Br(style={'background': '#191414'}))

], style={'background': '#191414',
          'margin': '0px 0px 0px 0px',
          'padding': '0px 0px 0px 0px',
          'overflow-x': 'hidden'})


# ------------------------------------------------------
# Connect the Plotly graphs with Dash Components
# UPDATING SCATTER CHART AND BAR CHART
@app.callback(
    [Output('most_common_bar_chart', 'figure'),
     Output('scatter-with-slider', 'figure')],
    Input(component_id='range-year-slider', component_property='value')
)
def scatter_and_bar(interval):
    years = list(range(interval[0], interval[1] + 1, 1))
    music_filtered = music[music.year.isin(years)]

    scatter = px.scatter(music_filtered,
                         x="valence",
                         y="danceability",
                         size="popularity",
                         size_max=25,
                         color="explicit_label",
                         hover_name="artist_names",
                         log_x=False,
                         color_discrete_sequence=["#1DB954", "red"],
                         title=f'Valence vs Danceability ({min(interval)} to {max(interval)}'
                               f' Total Songs: {len(music_filtered)})',
                         labels={'valence': 'Valence',
                                 'danceability': 'Danceability',
                                 'explicit_label': 'Explicit'
                                 }
                         )

    scatter.update_layout(transition_duration=100,
                          )

    # Select top ten artist
    most_common_10 = music_filtered['artist_names'].value_counts().index[:10]
    # Average data by artists
    artists_average_features = music_filtered.groupby('artist_names').mean()
    # Select target artists
    target_artists = artists_average_features.loc[most_common_10]
    # list features
    list_of_features = ['acousticness', 'danceability', 'liveness']

    bar = px.bar(
        data_frame=target_artists,
        x=most_common_10,
        y=list_of_features,
        range_y=[0, 1],
        barmode='group',
        title=f'Average Features from 10 most common Artists {interval[0], interval[1]}',
        color_discrete_sequence=['#1DB954', '#191414', 'red'],
        labels={'x': 'Artist',
                'value': 'Average',
                'variable': 'Song Feature'}
    )
    bar.update_xaxes(tickangle=20)
    bar.update_layout(autosize=False,
                      margin=dict(l=10, r=10, t=100, b=100))

    return bar, scatter


@app.callback(
    [Output(component_id='my_radar_chart', component_property='figure'),
     Output(component_id='my_radar_chart_2', component_property='figure')
     ],
    [Input(component_id='artist_chosen', component_property='value'),
     Input(component_id='artist_chosen_2', component_property='value')
     ]
)
def update_radarcharts(artist_chosen, artist_chosen_2):
    # Radar Chart
    # Radar Chart 1
    if artist_chosen is None:
        artist_chosen = 'Pink Floyd'
    if artist_chosen_2 is None:
        artist_chosen_2 = 'Metallica'

    fig1 = px.line_polar(artists_df,
                         r=artists_df.loc[artist_chosen][['valence',
                                                          'acousticness',
                                                          'liveness',
                                                          'danceability',
                                                          'energy']],
                         theta=['valence',
                                'acousticness',
                                'liveness',
                                'danceability',
                                'energy'],
                         line_close=True,
                         markers=True,
                         title=f'{artist_chosen} Average Features',
                         range_r=[0, 1],
                         )

    fig1.update_traces(fill='toself',
                       line_color='#1DB954')

    # Radar Chart 2
    fig2 = px.line_polar(artists_df,
                         r=artists_df.loc[artist_chosen_2][['valence',
                                                            'acousticness',
                                                            'liveness',
                                                            'danceability',
                                                            'energy']],
                         theta=['valence',
                                'acousticness',
                                'liveness',
                                'danceability',
                                'energy'],
                         line_close=True,
                         markers=True,
                         title=f'{artist_chosen_2} Average Features',
                         range_r=[0, 1]
                         )

    fig2.update_traces(fill='toself',
                       line_color='#1DB954')

    return fig1, fig2


if __name__ == '__main__':
    app.run_server(debug=True)
