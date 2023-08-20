# app.py

import pandas as pd
from dash import Dash, dcc, html, dash_table, Input, Output, State, callback

import base64
import datetime
import io
import plotly.express as px


month_names = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}

csv_file_path = r"C:\Users\sacra\Downloads\meter_22001772_LP_06-08-2023.csv"

# Format: (months, hours, weekdays/weekend)
TAOZ = [(([6, 7, 8, 9], range(17,23), True) , 165.33),
        (([6, 7, 8, 9], list(range(0,17)) + [23], True) , 48.15),
        (([6, 7, 8, 9], range(0,24), False) , 48.15),
        (([12, 1, 2], range(17,22), True) , 114.78),
        (([12, 1, 2], list(range(0,17)) + [22, 23], True) , 41.84),
        (([12, 1, 2], range(17,22), False) , 114.78),
        (([12, 1, 2], list(range(0,17)) + [22, 23], False) , 41.84),
        (([3, 4, 5, 10, 11], range(17,23), True) , 45.83),
        (([3, 4, 5, 10, 11], list(range(0,17)) + [23], True) , 40.84),
        (([3, 4, 5, 10, 11], range(0,24), False) , 40.84)]
# FIXED = [[(range(1,13), range(0,24), True) , 60.07], [(range(1,13), range(0,24), False) , 60.07]]
FIXED = 60.07


def parse_datetime(date_str):
    # Function to parse the date-time string into separate date and time columns
    try:
        dt_obj = pd.to_datetime(date_str, format='%d/%m/%Y %H:%M')
    except:
        dt_obj = pd.to_datetime('14/11/2022 09:15', format='%d/%m/%Y %H:%M')
    return dt_obj, dt_obj.month, dt_obj.hour, dt_obj.weekday()


def getprice(plan, month, hour, weekday):
    weekday = weekday < 6
    for k in plan:
        if month in k[0][0] and hour in k[0][1] and weekday == k[0][2]:
            return k[1]
    print('Error: no match in price plan')


def main(df):
    # Read the CSV file starting from row 13
    # df = pd.read_csv(csv_file_path, skiprows=range(1, 13), header=None, names=['DateTime', 'Kwh']).iloc[1:]
    df['Kwh'] = df['Kwh'].astype(float)

    # Split the 'DateTime' column into 'Date' and 'Time' columns
    df['DateTime'] = df['DateTime'].apply(parse_datetime)
    df[['DateTime', 'Month', 'Hour', 'Weekday']] = df['DateTime'].apply(pd.Series)

    # Drop the original 'DateTime' column
    # df.drop(columns=['DateTime'], inplace=True)

    df['TaozPrice'] = df.apply(lambda x: getprice(TAOZ, x.Month, x.Hour, x.Weekday), axis=1)
    df['Cost'] = df['Kwh'] * df['TaozPrice'] / 100
    df['FixedCost'] = df['Kwh'] * FIXED / 100

    return df


app = Dash(__name__)

app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select meter_####_XX_dd-mm-yyyy.csv File')
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
    dcc.Loading(id="loading",
                children=[html.Div([html.Div(id='output-data-upload')])],
                type="default",
                ),
    # html.Div(id='output-data-upload'),
])


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')),
                skiprows=range(1, 13), header=None, names=['DateTime', 'Kwh']).iloc[1:]
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    data = (
        main(df)
    )

    dfm = data.groupby('Month')[['FixedCost', "Cost"]].sum()
    dfm.rename(index=month_names, inplace=True)
    by_month = px.bar(dfm,
                      labels={"FixedCost": "Fixed price cost", "Cost": "TAOZ price cost"},
                      barmode='group')

    t = df[['FixedCost', "Cost"]].sum().to_dict()
    total = {'Fixed Price Cost': t['FixedCost'],
             'TAOZ Price Cost': t['Cost'],
             '% Difference': 100.0 * (t['FixedCost'] - t['Cost']) / t['FixedCost']}
    return html.Div([
        html.H5('File Name: %s' % filename),
        html.H6('File Date: %s' % datetime.datetime.fromtimestamp(date)),

        html.H1(children="TAOZ Analytics"),
        html.P(
            children=(
                "Analyze the electricity cost of TAOZ billing charges"
            ),
        ),
        html.H2(children="Total Cost"),
        dash_table.DataTable(id='total',
                             data=[total],
                             style_header={'text-align': 'center',}),
        html.H2(children="Cost By Month"),
        dcc.Graph(figure=by_month),
    ])


@callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children


if __name__ == '__main__':
    # main()
    app.run_server(debug=True)