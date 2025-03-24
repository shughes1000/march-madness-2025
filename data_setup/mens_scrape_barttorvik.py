import os
import json
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
from tqdm.autonotebook import trange
import time

pd.options.mode.copy_on_write = True

# Set the working directory to the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# get metadata
with open(f'../data/meta/mens/metadata.json', "r") as file:
    json_data = json.load(file)

SEASON = json_data['SEASON']
INCLUDE_CURRENT_SEASON = json_data['INCLUDE_CURRENT_SEASON']

def get_url(season):
    cutoff_dates = {
        2012: datetime(2012, 3, 14),
        2013: datetime(2013, 3, 20),
        2014: datetime(2014, 3, 19),
        2015: datetime(2015, 3, 18),
        2016: datetime(2016, 3, 16),
        2017: datetime(2017, 3, 15),
        2018: datetime(2018, 3, 14),
        2019: datetime(2019, 3, 20),
        2021: datetime(2021, 3, 18),
        2022: datetime(2022, 3, 16),
        2023: datetime(2023, 3, 15),
        2024: datetime(2024, 3, 20),
        2025: datetime(2025, 3, 19),
    }

    return (
        f'https://barttorvik.com/'
        f'team-tables_each.php?'
        f'year={season}&begin={season-1}1101&end={cutoff_dates[season].strftime(r"%Y%m%d")}'
    )
    # return f'https://barttorvik.com/team-tables_each.php?tvalue=All&year={season}&sort=&t2value=None&oppType=All&conlimit=All&begin=20111101&end={cutoff_dates[season].strftime(r"%Y%m%d")}&top=0&quad=4&mingames=0&toprk=0&venue=All&type=All&yax=3'

def get_html(url):    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        html = page.inner_html('//*[@id="tble"]/div/div/table')

    return html

def build_dataframe(html):
    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Extract column headers (from <th> tags inside <thead>)
    headers = [th.get_text(strip=True) for th in soup.find_all('th')]

    # Extract rows of data (from <tr> tags inside <tbody>)
    rows = soup.find_all('tr')[1:]  # Skip the header row

    # Prepare an empty list to store the data
    data = []

    # Loop through each row to extract columns
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]  # Extract text from each column
        data.append(cols)

    # Convert the data into a pandas DataFrame
    return pd.DataFrame(data, columns=headers)

def load_data(season):
    url = get_url(season)
    html = get_html(url)
    d = build_dataframe(html)

    d.columns = d.columns.str.upper()

    # prevent timeouts
    time.sleep(1)

    return d

def process_dataframe(df):
    # fix any issues with empty columns or duplicated columns
    df = df.loc[:, ~((df.columns.isin(['', ' '])) | (df.columns.duplicated()))]

    # fix dtypes
    for col in df.columns:
        # remove commas because they are typically thousands separators
        df[col] = df[col].replace({',': ''}, regex=True)
        try:
            df[col] = pd.to_numeric(df[col])
        except ValueError as e:
            pass

    df.insert(0, 'Season', df.pop('YEAR'))

    # create new columns
    df.insert(df.columns.get_loc('WINS'), 'WIN%', df['WINS']/(df['GAMES']))
    df.insert(df.columns.get_loc('ADJ DE') + 1, 'ADJ EM', df['ADJ OE'] - df['ADJ DE'])

    # remove some columns
    df = df.loc[
        : , 
        ~(
            (
                df.columns.isin([
                    ' ', 
                    'TEAM.1', 
                    'RECORD', 
                    'AVG HGT.', 
                    'OP. FT%', 
                    'PPP OFF.', 
                    'PPP DEF.',
                    '2P %',
                    '2P % D',
                    '3P %',
                    '3P % D',
                    'PAKE',  # DO NOT USE PAKE OR PASE; they are calculated post tourney despite being in earlier data
                    'PASE',  # DO NOT USE PAKE OR PASE; they are calculated post tourney despite being in earlier data
                    'WINS',
                    'GAMES',
                ])
            ) | 
            (
                df.columns.str.contains('UNNAMED')
            )
        )
    ]

    return df

def main():
    df = pd.concat(
        [
            load_data(season)
            for season in trange(2012, SEASON + INCLUDE_CURRENT_SEASON)
            if season != 2020  # cancelled
        ],
        ignore_index=True,
    )

    df = process_dataframe(df)

    df.to_parquet(f'../data/preprocessed/mens_barttorvik/barttorvik.parquet')

if __name__ == "__main__":
    main()