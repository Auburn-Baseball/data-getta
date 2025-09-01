# -*- coding: utf-8 -*-
"""
Senior Design Auburn Baseball
Batter Scores

"""
#jpm0092@auburn.edu 

import csv
from scipy.stats import percentileofscore



filename = "TrackMan_NoStuff_Master.csv"



# Define function to calculate outcome score
# All the outcomes with their associated weighted value for a batter.
def calculate_outcome_score(row):

    pitch_call = row['PitchCall']
    tagged_hit_type = row['TaggedHitType']
    play_result = row['PlayResult']
    strikes = int(row['Strikes'])
    balls = int(row['Balls'])
    kor_bb = row['KorBB']

    if pitch_call == "FoulBall":
        if strikes == 0:
            return 48
        elif strikes == 1:
            return 46
        elif strikes == 2:
            return 50

    elif pitch_call == "StrikeCalled":
        if kor_bb == "Strikeout":
            return 5
        elif strikes == 1:
            return 37
        elif strikes == 0:
            return 42
    
    elif pitch_call == "Strikeswinging":
        if kor_bb == "Strikeout":
            return 0
        elif strikes == 1:
            return 30
        elif strikes == 0:
            return 40
    
    # Results for any ball hit in play.
    elif pitch_call == "InPlay":
        if tagged_hit_type == "PopUp":
            if play_result == "Out":
                return 5
            elif play_result == "Single":
                return 60
            elif play_result == "Double":
                return 70
            elif play_result == "Triple":
                return 80
        elif tagged_hit_type == "GroundBall":
            if play_result == "Out" or play_result == "FieldersChoice":
                return 10
            elif play_result == "Sacrifice":
                return 50
            elif play_result == "Single":
                return 65
            elif play_result == "Double":
                return 75
            elif play_result == "Triple":
                return 85
        elif tagged_hit_type == "FlyBall":
            if play_result == "Out":
                return 30
            elif play_result == "Sacrifice":
                return 70
            elif play_result == "Single":
                return 75
            elif play_result == "Double":
                return 85
            elif play_result == "Triple":
                return 95
            elif play_result == "HomeRun":
                return 100
        elif tagged_hit_type == "Bunt":
            if play_result == "FieldersChoice" or play_result == "Out":
                return 15
            elif play_result == "Sacrifice":
                return 70
            elif play_result == "Single":
                return 90
        elif tagged_hit_type == "LineDrive":
            if play_result == "Out":
                return 42
            elif play_result == "Sacrifice":
                return 75
            elif play_result == "Single":
                return 80
            elif play_result == "Double":
                return 95
            elif play_result == "Triple":
                return 97
            elif play_result == "HomeRun":
                return 100
    
    elif pitch_call == "BallCalled":
        if balls == 0:
            return 53
        elif balls == 1:
            return 58
        elif balls == 2:
            return 65
        elif kor_bb == "Walk":
            return 75

    return 0



# pitch type groupings
# I guess Teaford wants this?
def group_pitch_type(pitch_type, pitcher_throws):
    if pitch_type in ["FourSeamFastBall", "Fastball", "TwoSeamFastBall"]:
        simplified_pitch_type = "Fastball"
    elif pitch_type in ["ChangeUp", "Splitter"]:
        simplified_pitch_type = "ChangeUp/Splitter"
    elif pitch_type in ["Slider", "Cutter"]:
        simplified_pitch_type = "Slider/Cutter"
    else:
        simplified_pitch_type = pitch_type
    return f"VS {pitcher_throws} {simplified_pitch_type}"

player_batter_scores = {}
all_scores = {}
player_batter_sides = {}
player_school = {}

with open(filename, 'r') as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        player = row['Batter']
        batter_side = row['BatterSide']
        school = row['BatterTeam']
        throw = row['PitcherThrows']
        pitch_type_grouped = group_pitch_type(row['TaggedPitchType'], row['PitcherThrows'])
        score = calculate_outcome_score(row)

        if pitch_type_grouped not in all_scores:
            all_scores[pitch_type_grouped] = []
        all_scores[pitch_type_grouped].append(score)

        if player not in player_batter_scores:
            player_batter_scores[player] = {}
        if pitch_type_grouped not in player_batter_scores[player]:
            player_batter_scores[player][pitch_type_grouped] = []
        player_batter_scores[player][pitch_type_grouped].append(score)
        
        if player not in player_batter_sides:
            player_batter_sides[player] = batter_side
            
        if player not in player_school:
            player_school[player] = school
            
            
# Calculate percentiles for each player and pitch type
player_percentiles = {}


for player, scores_by_pitch in player_batter_scores.items():
    player_percentiles[player] = {}
    for pitch_type_grouped, scores in scores_by_pitch.items():
        all_pitch_scores = all_scores[pitch_type_grouped]
        percentiles = [percentileofscore(all_pitch_scores, score, kind='rank') for score in scores]
        player_percentiles[player][pitch_type_grouped] = sum(percentiles) / len(percentiles)

# Print player percentiles for each pitch type, including # of pitches
for player, percentiles_by_pitch in player_percentiles.items():
    school = player_school[player]
    print(f"\n{player} ({batter_side}):")
    for pitch_type_grouped, scores in player_batter_scores[player].items(): 
        new_score = percentiles_by_pitch[pitch_type_grouped]  
        count = len(scores)
        print(f"{pitch_type_grouped}: {new_score:.2f} ({count})")

output_filename = "./output/batter_scores.csv"

with open(output_filename, 'w', newline='') as csvfile:
    fieldnames = ['BatterTeam', 'Batter', 'BatterSide', 'TaggedPitchType', 'PitcherThrows', 'BatterScore', '#ofPitches']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    
    for player, percentiles_by_pitch in player_percentiles.items():
        for pitch_type_grouped, percentile in percentiles_by_pitch.items():
            count = len(player_batter_scores[player][pitch_type_grouped])
            school = player_school[player]
            
            writer.writerow({
                'BatterTeam': school,
                'Batter': player,
                'BatterSide': player_batter_sides[player],  
                'TaggedPitchType': pitch_type_grouped,
                'BatterScore': round(percentile, 2),
                '#ofPitches': count
            })
