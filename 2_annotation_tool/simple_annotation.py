
import base64
import io
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table

import pandas as pd
import numpy as np
import plotly.graph_objs as go

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# アップロード部分のスタイル
upload_style={
    'width': '100%',
    'height': '60px',
    'lineHeight': '60px',
    'borderWidth': '1px',
    'borderStyle': 'dashed',
    'textAlign': 'center',
    'font-size':'20px'
    }

app.layout = html.Div([

    #表示場所
    html.H1('simple annotate tool ver1.0',style={'font-size':'40px'}),
    # 空白を加える
    html.Br(),
    # ファイルアップロードの部分を作る
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style=upload_style,
        multiple=True
    ),
    html.Br(),

    # アップロードしたファイルをデータテーブルとして表示させるところ
    html.Div(
        dcc.Loading(
            id='loading-1',
            children=[
                dash_table.DataTable(
                    id='output-data-upload',
                    column_selectable='multi',
                    fixed_rows={'headers': True, 'data': 0},
                    style_table={
                        'overflowX': 'scroll',
                        'overflowY': 'scroll',
                        'maxHeight': '500px'
                    },
                    style_header={
                        'fontWeight': 'bold',
                        'textAlign': 'center'},

                    editable=True,
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                )
            ],
            type='cube'
        ),
        style={
            'height': '500px',
            'font-size':25,
        }),

    html.Div([
    html.Div([
        html.H1("ID",style={'font-size' : '25px','margin':'1px'}),
        dcc.Input(
            id='my-id', 
            type='text',
            size=10,
            style={'height':'48px'}
        )],style={'line-height': '1px'}),
    html.Div([
        html.H1("annotation",style={'font-size' : '25px','margin':'1px'}),
        dcc.Input(
            id='my-id2',  
            type='text',
            size=50,
            style={'height':'48px'}
        )],style={'line-height': '1px'}),
    html.Div([
        html.H1("submit",style={'font-size' : '25px','margin':'1px','color':'#FFFFFF'}),
        html.Button(id="submit-button", n_clicks=0, children="Submit",style={'height':'48px','font-size': '20px',"background-color":"#D3D3D3"}),
        ],style={'line-height': '1px'})
    ],style={'display': 'flex','font-size' : '24px'}),

    # アノテーション後をデータテーブルとして表示させるところ
    html.Div(
        dcc.Loading(
            id='loading-2',
            children=[
                dash_table.DataTable(
                    id='output-data-upload2',
                    column_selectable='multi',
                    fixed_rows={'headers': True, 'data': 0},
                    style_table={
                        'overflowX': 'scroll',
                        'overflowY': 'scroll',
                        'maxHeight': '250px'
                    },
                    style_header={
                        'fontWeight': 'bold',
                        'textAlign': 'center'},
                    export_format='csv',
                    export_headers='display',
                    merge_duplicate_headers=True
                )
            ],
            type='cube'
        ),
        style={
            'height': '300px',
            'font-size':25,
        }),
])

# アップロードしたファイルをデータフレームとして読み込むための関数
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    data_ = df.to_dict('records')
    columns_ = [{'name': i, 'id': i} for i in df.columns]

    return [data_, columns_]


# アップロードしたファイルをデータテーブルとして出力
@app.callback([Output('output-data-upload', 'data'),
               Output('output-data-upload', 'columns')],
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])
def update_output(list_of_contents, list_of_names):
    # ファイルがない時の自動コールバックを防ぐ
    if list_of_contents is None:
        raise dash.exceptions.PreventUpdate

    contents = [parse_contents(c, n) for c, n in zip(list_of_contents, list_of_names)]

    return [contents[0][0], contents[0][1]]

# アノテーション後を出力
@app.callback(
    [Output('output-data-upload2', 'data'),
     Output('output-data-upload2', 'columns')],
    [Input("submit-button", "n_clicks"),
    Input('output-data-upload', 'data'),Input('output-data-upload', 'columns')],
    [State("my-id", "value"),
     State("my-id2", "value")]
)
def update_output(n_clicks, dict_data,dict_col, input1, input2):
    # ファイルがない時の自動コールバックを防ぐ
    if dict_data is None:
        raise dash.exceptions.PreventUpdate

    if (input1 is None)|(input2 is None):
        raise dash.exceptions.PreventUpdate

    output_file_name='./output/output.csv'

    # 一つ目のテキストボックスにIDを入力し、
    # 二つ目のテキストボックスに①delを入力すると削除②resetを入力すると初期化
    if input2 == 'del':
        df_last=pd.read_csv(output_file_name)
        df_last=df_last[df_last['ID']!=int(input1)]
        df_last.to_csv(output_file_name,index=None)
        dict_data_res = df_last.to_dict('records')
        dict_col_res = [{'name': i, 'id': i} for i in df_last.columns]
        return [dict_data_res,dict_col_res]
    
    if input2 == 'reset':
        df_last=pd.read_csv(output_file_name)
        df_last=pd.DataFrame(columns=df_last.columns)
        df_last.to_csv(output_file_name,index=None)
        dict_data_res = df_last.to_dict('records')
        dict_col_res = [{'name': i, 'id': i} for i in df_last.columns]
        return [dict_data_res,dict_col_res]
    
    #ブラウザ上でのIDの複数入力に対応
    if ' ' in str(input1):
        test_=input1.split()
        df_last=pd.read_csv(output_file_name)
        df = pd.DataFrame(data=dict_data)

        for i in test_:
            
            df_= df[df['ID']==int(i)]
            df_['annotate']=[str(input2)]
            df_=df_[['ID','DATA1','DATA2','DATA3','DATA4','annotate']]

            df_last=pd.concat([df_last,df_])
            df_last=df_last[~df_last['ID'].duplicated(keep='last')]

        df_last=df_last[['ID','DATA1','DATA2','DATA3','DATA4','annotate']]
        df_last.to_csv(output_file_name,index=None)
        
        dict_data_res = df_last.to_dict('records')
        dict_col_res = [{'name': i, 'id': i} for i in df_last.columns]

        return [dict_data_res,dict_col_res]


    df_last=pd.read_csv(output_file_name)

    df = pd.DataFrame(data=dict_data)
    df_= df[df['ID']==int(input1)]
    df_['annotate']=[str(input2)]
    df_=df_[['ID','DATA1','DATA2','DATA3','DATA4','annotate']]

    df_last=pd.concat([df_last,df_])
    df_last=df_last[~df_last['ID'].duplicated(keep='last')]
    df_last=df_last[['ID','DATA1','DATA2','DATA3','DATA4','annotate']]
    df_last.to_csv(output_file_name,index=None)
    
    dict_data_res = df_last.to_dict('records')
    dict_col_res = [{'name': i, 'id': i} for i in df_last.columns]

    return [dict_data_res,dict_col_res]

if __name__ == '__main__':
    app.run_server()

