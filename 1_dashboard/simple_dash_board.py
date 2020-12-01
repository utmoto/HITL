import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_table

import plotly.graph_objs as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots

import numpy as np
import pandas as pd
import pickle
import requests

import lightgbm as lgb
from sklearn.neighbors import KNeighborsClassifier

#データ取得
#注：実運用時は対象ファイルを動的に更新し、callback部分で処理する必要がある
df = pd.read_csv('test_credit_card_fraud.csv')

#学習済モデルの読み込みと出力
clf = pickle.load(open('trained_model.pkl', 'rb'))
knn = pickle.load(open('trained_model_knn.pkl', 'rb'))

res=clf.predict_proba(df[['V4','V14']])
dist, ind = knn.kneighbors(df[['V4','V14']])

#教師無学習モデルに関しては閾値を設定し、未知データについて-1、それ以外を0で判定
ano_score=np.max(dist,axis=1)
ano_score_list=[]
for ano_score_ in ano_score:
    score_=int(ano_score_)
    if score_ > 1:
        score_ = -1
    else:
        score_ = 0
    ano_score_list.append(score_)


#app実行
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

#レイアウト
app.layout = dbc.Container(
    [   dbc.Row(
            [
                dbc.Col(
                    html.H1("Simple Dashboard"),
                    style={"background-color": "#eeeeee"}#背景色を灰色に
                    )
            ],
            className="h-10",
            no_gutters=True
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(id='live-update-graph-chart',style={'width':'100%'}) ,
                    width=12,
                    style={"height": "50%", "background-color": "White"},#背景色を白に
                ),
            ],
            className="h-40",
            no_gutters=True
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(id='live-update-graph-pie',style={'width':'100%'}),
                    width=3,
                    style={"height": "100%", "background-color": "White"},
                ),
                dbc.Col(
                    dcc.Graph(id='live-update-graph-dist',style={'width':'100%'}),
                    width=3,
                    style={"height": "100%", "background-color": "White"},
                ),
                dbc.Col(
                    dcc.Graph(id='live-update-graph-bar',style={'width':'100%'}),
                    width=3,
                    style={"height": "100%", "background-color": "White"},
                ),
                dbc.Col(
                    html.Div([
                    html.Br(style={'line-height':1}),
                    html.H1("Data table",style={'font-size':27}),
                    dcc.Tabs(id="tabs", value='tab-1', 
                             style={
                                'width': '45%',
                                'font-size': '100%',
                                'height':'2.3vh'
                                ,"background-color": 'White'
                             }
                            ,children=[
                        dcc.Tab(label='Latest', value='tab-1',style={'borderBottom': '1px solid #d6d6d6','padding': '2px'},selected_style = {'borderBottom': '1px solid #d6d6d6','padding': '2px'}),
                        dcc.Tab(label='past', value='tab-2',style={'borderBottom': '1px solid #d6d6d6','padding': '2px'},selected_style = {'borderBottom': '1px solid #d6d6d6','padding': '2px'}),
                    ]),html.Div(id='tabs-content',style={'width':'100%','height':'100%','font-size':15,"background-color": 'White','textAlign': 'center'})]),
                    width=3,
                    style={"height": "100%", "background-color": 'White'},
                ),
            ],
            className="h-48",
            no_gutters=True
        ),
        dbc.Row(
            [
                dbc.Col(
                    html.Pre(
                    id='counter_text',
                    children='Active flights worldwide:'
                    ),
                    style={"background-color": "White"}
                    )
            ],
            className="h-10",
            no_gutters=True
        ),
        #intervalで更新させる
        dcc.Interval(
            id='interval-component',
            interval=3000, 
            n_intervals=0
        ) 
    ],
    style={"height": "140vh",'backgroundColor': '#eeeeee'},
    fluid=True#横幅を100％にする
)


V4_data_list = list(df['V4'])
V14_data_list = list(df['V14'])
Class_data_list = list(df['Class'])


#インターバルごとにtime-stampsを更新（左下に表示）
@app.callback(Output('counter_text', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_layout(n):
    return 'time-stamps: {}'.format(n)


#Chart
@app.callback(Output('live-update-graph-chart','figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_chart(n):

    #初めのローディングが挙動が安定しないため2回以降で更新
    if n < 2:
        raise dash.exceptions.PreventUpdate
    
    res=clf.predict_proba(df[['V4','V14']][:n])

    #実データとモデルスコアを並べて表示
    fig = make_subplots(rows=2, cols=1, 
                    shared_xaxes=True, 
                    vertical_spacing=0.02)

    fig.add_trace(go.Scatter(
        x = list(range(len(V4_data_list[:n]))),
        y = V4_data_list[:n],
        mode='lines+markers',name='raw: V04'),
        row=1, col=1)

    fig.add_trace(go.Scatter(
        x = list(range(len(V14_data_list[:n]))),
        y = V14_data_list[:n],
        mode='lines+markers',name='raw: V14'),
        row=1, col=1)

    fig.update_layout(legend_title='time-series-raw-data')

    fig.add_trace(go.Scatter(
        x = list(range(len(res[:,1]))),
        y = res[:,1],
        mode='lines+markers',name='Score: supervised'),
        row=2, col=1)

    fig.add_trace(go.Scatter(
        x = list(range(len(ano_score_list[:n]))),
        y = ano_score_list[:n],
        mode='lines+markers',name='Score: unsupervised'),
        row=2, col=1)

    fig.add_trace(go.Scatter(
        x = list(range(len(Class_data_list[:n]))),
        y = Class_data_list[:n],
        mode='lines+markers',name='Score: real_Class'),
        row=2, col=1)

    fig.update_layout(legend_title='■ raw_value & Score')
    fig.update_yaxes(title_text="raw_value", row=1, col=1)
    fig.update_yaxes(title_text="Score", row=2, col=1)

    fig.update_xaxes(title_text="Time(s)", row=2, col=1)

    fig.update_layout(title_text="Chart",
        title_font_size=28,
        font=dict(size=20),
        height = 600,
        plot_bgcolor='rgba(245, 246, 249, 1)')
    
    return fig

#Pie_Chart
@app.callback(Output('live-update-graph-pie','figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_pie(n):
        
    fig = go.Figure(
        data = [go.Pie(
        labels=['V4','V14'],
        values=[df['V4'].iloc[n],df['V14'].iloc[n]],
        hoverinfo="label+percent+name",
        hole=.4,
        name='Value Rate'
        ),
        ],
        
        layout=go.Layout(
            title = 'Pie Chart',
            font=dict(size=18),
            annotations= [{
            "font": {
                "size": 20
            },
            "showarrow": False,
            "text": "V4&V14",
            "x": 0.5,
            "y": 0.5
            },
            ],
            plot_bgcolor='rgba(245, 246, 249, 1)',
    )
    )

    return fig


#Distplot
@app.callback(Output('live-update-graph-dist','figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_dist(n):

    #初めのローディングが挙動が安定しないため6回以降で更新
    if n <6:
        raise dash.exceptions.PreventUpdate

    data_V4=df['V4'][:n]
    data_V14=df['V14'][:n]

    hist_data = [data_V4,data_V14]
    group_labels = ['V4','V14']

    fig = ff.create_distplot(hist_data, group_labels, bin_size=[1,1])
    fig['layout'].update(title='Distplot')
    fig['layout'].update(font=dict(size=18))

    return fig


#Bar_plot
@app.callback(Output('live-update-graph-bar','figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_bar(n):
    
    #教師有学習部分の閾値の設定
    ath_super_low=0.1
    ath_super_high=0.6
    ath_unsuper_high=-0.2
    ath_unsuper_low=-1

    trace1 = go.Bar(
        x=['supervised'],
        y=[len([i for i in Class_data_list[:n] if i > ath_super_low])],
        name = 'supervised_ath_0.1',
        marker=dict(color='#FFD700') 
    )
    trace2 = go.Bar(
        x=['supervised'],
        y=[len([i for i in Class_data_list[:n] if i > ath_super_high])],
        name='supervised_ath_0.6',
        marker=dict(color='#9EA0A1') 
    )

    trace3 = go.Bar(
        x=['unsupervised'],
        y=[len([i for i in ano_score_list[:n] if i < ath_unsuper_high])],
        name='unsupervised_ath_-0.2',
    )

    trace4 = go.Bar(
        x=['unsupervised'],
        y=[len([i for i in ano_score_list[:n] if i < ath_unsuper_low])],
        name='unsupervised_ath_-1',
    )

    data = [trace1, trace2,trace3,trace4]
    layout = go.Layout(
        title='Bar plot',
        font=dict(size=18),
        barmode='group'
    )

    fig = go.Figure(data=data, layout=layout)
    
    return fig




#Table_data
@app.callback(Output('tabs-content', 'children'),
              [Input('tabs', 'value'),Input('interval-component', 'n_intervals')])
def update_table(tab,n):

    #直近10行のみを更新
    if n <= 10:
        first=0
    else:
        first=n-11

    if tab == 'tab-1':
        table1=html.Div(dash_table.DataTable(
                            id='table-sorting-filtering',
                            columns=[
                                {'name': i, 'id': i, 'deletable': True} for i in df.columns
                            ],
                            data=df[first:n].to_dict("rows"),
                            fixed_rows={'headers': True},
                            style_header={'backgroundColor': 'white'},
                            style_cell={
                                'height': '9',
                                'minWidth': 90, 'maxWidth': 90, 'width': 90
                            },
                            style_table={'height': 353},
                            style_cell_conditional=[
                                {'if': {'column_id': 'Class'},
                                'width': '20%','textAlign': 'center'},
                                {'if': {'column_id': 'Time'},
                                'width': '15%'}
                                ]
                        )
                        ,style={'width':'97%','height':'95%','font-size':13,"background-color": 'White','textAlign': 'center'}
                        ) 

        return table1

    elif tab == 'tab-2':
        table2=html.Div(dash_table.DataTable(
                            id='table-sorting-filtering-all',
                            columns=[
                                {'name': i, 'id': i, 'deletable': True} for i in df.columns
                            ],
                            data=df[:n].to_dict("rows"),
                            fixed_rows={'headers': True},
                            style_header={'backgroundColor': 'white'},

                            style_cell={
                                    'height': '9',
                                    'minWidth': 90, 'maxWidth': 90, 'width': 90
                            },
                            style_table={'height': 353},
                            style_cell_conditional=[
                                {'if': {'column_id': 'Class'},
                                'width': '20%','textAlign': 'center'},
                                {'if': {'column_id': 'Time'},
                                'width': '15%'}
                                ]
                        )
                        ,style={'width':'97%','height':'95%','font-size':13,"background-color": 'White','textAlign': 'center'}
                        ) 

        return table2


if __name__ == "__main__":
    app.run_server(debug=True)
