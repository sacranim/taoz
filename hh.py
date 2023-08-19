import pandas as pd


def parse_datetime(date_str):
    # Function to parse the date-time string into separate date and time columns
    try:
        dt_obj = pd.to_datetime(date_str, format='%d/%m/%Y %H:%M')
    except:
        dt_obj = pd.to_datetime('14/11/2022 09:15', format='%d/%m/%Y %H:%M')
    return dt_obj, dt_obj.month, dt_obj.hour, dt_obj.weekday()


# Path to your CSV file
# csv_file_path = '/content/meter_22001772_LP_06-08-2023.csv'


csv_file_path = r"C:\Users\sacra\Downloads\meter_22001772_LP_06-08-2023.csv"


def main():
    # Read the CSV file starting from row 13
    df = pd.read_csv(csv_file_path, skiprows=range(1, 13), header=None, names=['DateTime', 'Kwh']).iloc[1:]
    df['Kwh'] = df['Kwh'].astype(float)

    # Split the 'DateTime' column into 'Date' and 'Time' columns
    df['DateTime'] = df['DateTime'].apply(parse_datetime)
    df[['DateTime', 'Month', 'Hour', 'Weekday']] = df['DateTime'].apply(pd.Series)

    # Drop the original 'DateTime' column
    # df.drop(columns=['DateTime'], inplace=True)

    print(df)


if __name__ == '__main__':
    main()
