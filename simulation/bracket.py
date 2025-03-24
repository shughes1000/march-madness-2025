import os
import json
import pickle
import pandas as pd
import numpy as np

# Set the working directory to the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# get metadata
with open(f'../data/meta/mens/metadata.json', "r") as file:
    json_data = json.load(file)

SEASON = json_data['SEASON']

playin_losers = json_data['season_data'][str(SEASON)]['playin_losers']

df_teams = df_teams = pd.read_csv(r'..\data\unprocessed\kaggle\MTeams.csv')

df_seeds = pd.read_csv(r'..\data\unprocessed\kaggle\MNCAATourneySeeds.csv')

df_seeds = df_seeds.loc[df_seeds['Season'] == SEASON, :].reset_index(drop=True)

df_seeds.insert(2, 'Play In', df_seeds['Seed'].str.endswith(('a', 'b')))
df_seeds.insert(2, 'Region', df_seeds['Seed'].str[0])
df_seeds['Seed'] = df_seeds['Seed'].str.extract(r'(\d+)').astype(int)

df_seeds = df_seeds.loc[~df_seeds['TeamID'].isin(playin_losers), :].reset_index(drop=True)

df_seeds.insert(1, 'Region Seed', df_seeds['Region'] + df_seeds['Seed'].astype(str).str.zfill(2))

id_to_team = dict(zip(df_teams['TeamID'], df_teams['TeamName']))
region_seed_to_team_seed = dict(zip(df_seeds['Region Seed'], df_seeds['TeamID'].map(id_to_team) + " (" + df_seeds['Seed'].astype(str) + ")"))


class Bracket:
    def __init__(self, picks: dict, classification: str = None):
        """
        _summary_

        Args:
            picks (dict): _description_
            classification (str, optional): _description_. Defaults to None.
        """

        self.picks = picks
        # self.simulation_scores = simulation_scores
        self.classification = classification

    # def save_simulation_scores(self, simulation_scores: np.ndarray):
    #     self.simulation_scores = simulation_scores

    def __str__(self):
        display_dict = {game: region_seed_to_team_seed[region_seed] for game, region_seed in self.picks.items()}

        printout = '-'*30 + '\n'
        printout += '\n'
        printout += 'ROUND OF 64 WINNERS\n'
        printout += '\n'

        for region in ('W', 'X', 'Y', 'Z'):
            printout += f'REGION {region}\n'
            for slot in (1, 8, 5, 4, 6, 3, 7, 2):
                key = f'R1{region}{slot}'
                printout += f'{key}: {display_dict[key]}\n'
            printout += '\n'
        printout += '-'*30 + '\n'
        printout += '\n'

        printout += 'ROUND OF 32 WINNERS\n'
        printout += '\n'
        for region in ('W', 'X', 'Y', 'Z'):
            printout += f'REGION {region}\n'
            for slot in (1, 4, 3, 2):
                key = f'R2{region}{slot}'
                printout += f'{key}: {display_dict[key]}\n'
            printout += '\n'
        printout += '-'*30 + '\n'
        printout += '\n'

        printout += 'ROUND OF 16 WINNERS\n'
        printout += '\n'
        for region in ('W', 'X', 'Y', 'Z'):
            printout += f'REGION {region}\n'
            for slot in (1, 2):
                key = f'R3{region}{slot}'
                printout += f'{key}: {display_dict[key]}\n'
            printout += '\n'
        printout += '-'*30 + '\n'
        printout += '\n'

        printout += 'ELITE EIGHT WINNERS\n'
        printout += '\n'
        for region in ('W', 'X', 'Y', 'Z'):
            printout += f'REGION {region}\n'
            for slot in (1, ):
                key = f'R4{region}{slot}'
                printout += f'{key}: {display_dict[key]}\n'
            printout += '\n'
        printout += '-'*30 + '\n'
        printout += '\n'

        printout += 'FINAL FOUR WINNERS\n'
        printout += '\n'
        for matchup in ('WX', 'YZ'):
            key = f'R5{matchup}'
            printout += f'{key}: {display_dict[key]}\n'
            printout += '\n'
        printout += '-'*30 + '\n'
        printout += '\n'

        printout += 'FINALS WINNER\n'
        printout += '\n'
        for matchup in ('CH', ):
            key = f'R6{matchup}'
            printout += f'{key}: {display_dict[key]}\n'
            printout += '\n'
        printout += '-'*30 + '\n'
        printout += '\n'

        return printout
    
    def __repr__(self):
        return self.__str__()


if __name__ == "__main__":
    with open(f'../data/simulations/mens/mens_simulation_2025_I_USED_THESE_ONES.pkl', 'rb') as f:
        simulation_data = pickle.load(f)

    candidates = simulation_data['candidates']

    del simulation_data

    a = Bracket(picks=candidates[0], classification='candidate')

    print(a)