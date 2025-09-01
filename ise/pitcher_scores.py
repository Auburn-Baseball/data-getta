import csv 
import numpy as np
from scipy import stats
import pandas as pd

csv_sec = 'UpdatedSEC.csv' 
csv_auburn = 'UpdatedAuburn.csv'


# define variables
changeup_splitter_IVB = 0.10
changeup_splitter_rel_speed = 0.20
changeup_splitter_rel_height = 0.15
changeup_splitter_residual = 0
changeup_splitter_extension = 0.05
changeup_splitter_hb = 0.05
changeup_splitter_relspeed_dev = 0.25
changeup_splitter_IVB_dev = 0.20

curveball_IVB = 0.35
curveball_rel_speed = 0.15
curveball_rel_height = 0.10
curveball_residual = 0
curveball_extension = 0.05
curveball_hb = 0.35
curveball_rel_speed_dev = 0
curveball_IVB_dev = 0

fastball_IVB = 0.30
fastball_rel_speed = 0.30
fastball_rel_height = 0.10
fastball_residual = 0.15
fastball_extension = 0.10
fastball_hb = 0.05
fastball_rel_speed_dev = 0
fastball_IVB_dev = 0

slider_cutter_IVB = 0.15
slider_cutter_rel_speed = 0.30
slider_cutter_rel_height = 0.10
slider_cutter_residual = 0
slider_cutter_extension = 0.05
slider_cutter_hb = 0.40
slider_cutter_rel_speed_dev = 0
slider_cutter_IVB_dev = 0

sinker_IVB = 0.20
sinker_rel_speed = 0.30
sinker_rel_height = 0.10
sinker_residual = 0
sinker_extension = 0.05
sinker_hb = 0.35
sinker_rel_speed_dev = 0
sinker_IVB_dev = 0

# create a dictionary for each pitch type and each key metric
slider_cutter_dict = {'Pitcher' : [], 'RelSpeed' : [], 'InducedVertBreak' : [], 'HorzBreak' : [], 'RelHeight' : [], 'Extension' : []} 
changeup_splitter_dict = {'Pitcher' : [], 'RelSpeed' : [], 'InducedVertBreak' : [], 'HorzBreak' : [], 'RelHeight' : [], 'Extension' : [], 'RelSpeedDev' : [], 'IVBDev' : []} 
fastball_dict = {'Pitcher' : [], 'RelSpeed' : [], 'InducedVertBreak' : [], 'HorzBreak' : [], 'RelHeight' : [], 'Extension' : [], 'Residual' : [], 'ExpectedIVB' : []} 
curveball_dict = {'Pitcher' : [], 'RelSpeed' : [], 'InducedVertBreak' : [], 'HorzBreak' : [], 'RelHeight' : [], 'Extension' : []} 
sinker_dict = {'Pitcher' : [], 'RelSpeed' : [], 'InducedVertBreak' : [], 'HorzBreak' : [], 'RelHeight' : [], 'Extension' : []} 

with open(csv_sec, mode = 'r') as csv_file: 
    csv_reader = csv.DictReader(csv_file) 
    for row in csv_reader: 
        pitch_type = row['TaggedPitchType'] 
        if pitch_type in ['Slider', 'Cutter']: 
            slider_cutter_dict['Pitcher'].append(row['Pitcher'])
            slider_cutter_dict['RelSpeed'].append(float(row['RelSpeed']))
            slider_cutter_dict['InducedVertBreak'].append(float(row['InducedVertBreak']))
            slider_cutter_dict['HorzBreak'].append(abs(float(row['HorzBreak'])))
            slider_cutter_dict['RelHeight'].append(float(row['RelHeight']))
            slider_cutter_dict['Extension'].append(float(row['Extension']))
        elif pitch_type in ['ChangeUp', 'Splitter']: 
            changeup_splitter_dict['Pitcher'].append(row['Pitcher'])
            changeup_splitter_dict['RelSpeed'].append(float(row['RelSpeed']))
            changeup_splitter_dict['InducedVertBreak'].append(float(row['InducedVertBreak']))
            changeup_splitter_dict['HorzBreak'].append(abs(float(row['HorzBreak'])))
            changeup_splitter_dict['RelHeight'].append(float(row['RelHeight']))
            changeup_splitter_dict['Extension'].append(float(row['Extension']))
            changeup_splitter_dict['RelSpeedDev'].append(float(row['RelSpeedDev']))
            changeup_splitter_dict['IVBDev'].append(float(row['IVBDev']))
        elif pitch_type in ['Fastball', 'FourSeamFastball', 'TwoSeamFastball']: 
            fastball_dict['Pitcher'].append(row['Pitcher'])
            fastball_dict['RelSpeed'].append(float(row['RelSpeed']))
            fastball_dict['InducedVertBreak'].append(float(row['InducedVertBreak']))
            fastball_dict['HorzBreak'].append(abs(float(row['HorzBreak'])))
            fastball_dict['RelHeight'].append(float(row['RelHeight']))
            fastball_dict['Extension'].append(float(row['Extension']))
            fastball_dict['Residual'].append(float(row['Residual']))
        elif pitch_type in ['Curveball']: 
            curveball_dict['Pitcher'].append(row['Pitcher'])
            curveball_dict['RelSpeed'].append(float(row['RelSpeed']))
            curveball_dict['InducedVertBreak'].append(float(row['InducedVertBreak']))
            curveball_dict['HorzBreak'].append(abs(float(row['HorzBreak'])))
            curveball_dict['RelHeight'].append(float(row['RelHeight']))
            curveball_dict['Extension'].append(float(row['Extension']))
        elif pitch_type in ['Sinker']: 
            sinker_dict['Pitcher'].append(row['Pitcher'])
            sinker_dict['RelSpeed'].append(float(row['RelSpeed']))
            sinker_dict['InducedVertBreak'].append(float(row['InducedVertBreak']))
            sinker_dict['HorzBreak'].append(abs(float(row['HorzBreak'])))
            sinker_dict['RelHeight'].append(float(row['RelHeight']))
            sinker_dict['Extension'].append(float(row['Extension']))
            
            
with open(csv_auburn, mode = 'r') as csv_file: 
    csv_reader = csv.DictReader(csv_file) 
    for row in csv_reader: 
        pitch_type = row['TaggedPitchType'] 
        if pitch_type in ['Slider', 'Cutter']: 
            slider_cutter_dict['Pitcher'].append(row['Pitcher'])
            slider_cutter_dict['RelSpeed'].append(float(row['RelSpeed']))
            slider_cutter_dict['InducedVertBreak'].append(float(row['InducedVertBreak']))
            slider_cutter_dict['HorzBreak'].append(abs(float(row['HorzBreak'])))
            slider_cutter_dict['RelHeight'].append(float(row['RelHeight']))
            slider_cutter_dict['Extension'].append(float(row['Extension']))
        elif pitch_type in ['ChangeUp', 'Splitter']: 
            changeup_splitter_dict['Pitcher'].append(row['Pitcher'])
            changeup_splitter_dict['RelSpeed'].append(float(row['RelSpeed']))
            changeup_splitter_dict['InducedVertBreak'].append(float(row['InducedVertBreak']))
            changeup_splitter_dict['HorzBreak'].append(abs(float(row['HorzBreak'])))
            changeup_splitter_dict['RelHeight'].append(float(row['RelHeight']))
            changeup_splitter_dict['Extension'].append(float(row['Extension']))
            changeup_splitter_dict['RelSpeedDev'].append(float(row['RelSpeedDev']))
            changeup_splitter_dict['IVBDev'].append(float(row['IVBDev']))
        elif pitch_type in ['Fastball', 'FourSeamFastball', 'TwoSeamFastball']: 
            fastball_dict['Pitcher'].append(row['Pitcher'])
            fastball_dict['RelSpeed'].append(float(row['RelSpeed']))
            fastball_dict['InducedVertBreak'].append(float(row['InducedVertBreak']))
            fastball_dict['HorzBreak'].append(abs(float(row['HorzBreak'])))
            fastball_dict['RelHeight'].append(float(row['RelHeight']))
            fastball_dict['Extension'].append(float(row['Extension']))
            fastball_dict['Residual'].append(float(row['Residual']))
        elif pitch_type in ['Curveball']: 
            curveball_dict['Pitcher'].append(row['Pitcher'])
            curveball_dict['RelSpeed'].append(float(row['RelSpeed']))
            curveball_dict['InducedVertBreak'].append(float(row['InducedVertBreak']))
            curveball_dict['HorzBreak'].append(abs(float(row['HorzBreak'])))
            curveball_dict['RelHeight'].append(float(row['RelHeight']))
            curveball_dict['Extension'].append(float(row['Extension']))
        elif pitch_type in ['Sinker']: 
            sinker_dict['Pitcher'].append(row['Pitcher'])
            sinker_dict['RelSpeed'].append(float(row['RelSpeed']))
            sinker_dict['InducedVertBreak'].append(float(row['InducedVertBreak']))
            sinker_dict['HorzBreak'].append(abs(float(row['HorzBreak'])))
            sinker_dict['RelHeight'].append(float(row['RelHeight']))
            sinker_dict['Extension'].append(float(row['Extension']))
column_name = 'Pitcher' 
roster = []
with open(csv_auburn, mode = 'r') as csv_file: 
    reader = csv.DictReader(csv_file)
    for row in reader:
        roster.append(row[column_name])
new_roster = list(set(roster))

# slider/cutter mean and std            
slider_cutter_rel_speed_mean = np.mean(slider_cutter_dict['RelSpeed'])
slider_cutter_rel_speed_std = np.std(slider_cutter_dict['RelSpeed'])
slider_cutter_IVB_mean = np.mean(slider_cutter_dict['InducedVertBreak'])
slider_cutter_IVB_std = np.std(slider_cutter_dict['InducedVertBreak'])
slider_cutter_HB_mean = np.mean(slider_cutter_dict['HorzBreak'])
slider_cutter_HB_std = np.std(slider_cutter_dict['HorzBreak'])
slider_cutter_rel_height_mean = np.mean(slider_cutter_dict['RelHeight'])
slider_cutter_rel_height_std = np.std(slider_cutter_dict['RelHeight'])
slider_cutter_extension_mean = np.mean(slider_cutter_dict['Extension'])
slider_cutter_extension_std = np.std(slider_cutter_dict['Extension'])

# slider/cutter percentiles
z_scores_rel_speed_slider_cutter = [(value - slider_cutter_rel_speed_mean) / slider_cutter_rel_speed_std for value in slider_cutter_dict['RelSpeed']]
percentiles_rel_speed_slider_cutter = [stats.norm.cdf(z) * 100 for z in z_scores_rel_speed_slider_cutter]
#print(percentiles_rel_speed_slider_cutter[:10])
z_scores_IVB_slider_cutter = [(value - slider_cutter_IVB_mean) / slider_cutter_IVB_std for value in slider_cutter_dict['InducedVertBreak']]
percentiles_IVB_slider_cutter = [stats.norm.cdf(z) * 100 for z in z_scores_IVB_slider_cutter]
#print(percentiles_IVB_slider_cutter[:10])
z_scores_HB_slider_cutter = [(value - slider_cutter_HB_mean) / slider_cutter_HB_std for value in slider_cutter_dict['HorzBreak']]
percentiles_HB_slider_cutter = [stats.norm.cdf(z) * 100 for z in z_scores_HB_slider_cutter]
#print(percentiles_HB_slider_cutter[:10])
z_scores_rel_height_slider_cutter = [(value - slider_cutter_rel_height_mean) / slider_cutter_rel_height_std for value in slider_cutter_dict['RelHeight']]
percentiles_rel_height_slider_cutter = [stats.norm.cdf(z) * 100 for z in z_scores_rel_height_slider_cutter]
#print(percentiles_rel_height_slider_cutter[:10])
z_scores_extension_slider_cutter = [(value - slider_cutter_extension_mean) / slider_cutter_extension_std for value in slider_cutter_dict['Extension']]
percentiles_extension_slider_cutter = [stats.norm.cdf(z) * 100 for z in z_scores_extension_slider_cutter]
#print(percentiles_extension_slider_cutter[:10])

# calculate expected IVB for fb
def calculate_expected_ivb(rel_height):
    return 4.7162 * rel_height - 11.491
expected_fastball_IVB = [calculate_expected_ivb(rel_height) for rel_height in fastball_dict['RelHeight']]
fastball_dict['ExpectedIVB'] = expected_fastball_IVB
# calculate residual for fastball
residual = []
for i in range(len(fastball_dict['Pitcher'])):
    ivb_diff = fastball_dict['InducedVertBreak'][i] - fastball_dict['ExpectedIVB'][i]
    residual.append(ivb_diff)
    fastball_dict['Residual'] = residual
# check residual values are correct
#for pitcher, residual in zip(fastball_dict['Pitcher'], fastball_dict['Residual']):
 #   print(f"{pitcher}\t{residual:.3f}")

# fastball mean and std            
fastball_rel_speed_mean = np.mean(fastball_dict['RelSpeed'])
fastball_rel_speed_std = np.std(fastball_dict['RelSpeed'])
fastball_IVB_mean = np.mean(fastball_dict['InducedVertBreak'])
fastball_IVB_std = np.std(fastball_dict['InducedVertBreak'])
fastball_HB_mean = np.mean(fastball_dict['HorzBreak'])
fastball_HB_std = np.std(fastball_dict['HorzBreak'])
fastball_rel_height_mean = np.mean(fastball_dict['RelHeight'])
fastball_rel_height_std = np.std(fastball_dict['RelHeight'])
fastball_extension_mean = np.mean(fastball_dict['Extension'])
fastball_extension_std = np.std(fastball_dict['Extension'])
fastball_residual_mean = np.mean(fastball_dict['Residual'])
fastball_residual_std = np.std(fastball_dict['Residual'])

# fastball percentiles
z_scores_rel_speed_fb = [(value - fastball_rel_speed_mean) / fastball_rel_speed_std for value in fastball_dict['RelSpeed']]
percentiles_rel_speed_fb = [stats.norm.cdf(z) * 100 for z in z_scores_rel_speed_fb]
#print(percentiles_rel_speed_fb[:10])
z_scores_IVB_fb = [(value - fastball_IVB_mean) / fastball_IVB_std for value in fastball_dict['InducedVertBreak']]
percentiles_IVB_fb = [stats.norm.cdf(z) * 100 for z in z_scores_IVB_fb]
#print(percentiles_IVB_fb[:10])
z_scores_HB_fb = [(value - fastball_HB_mean) / fastball_HB_std for value in fastball_dict['HorzBreak']]
percentiles_HB_fb = [stats.norm.cdf(z) * 100 for z in z_scores_HB_fb]
#print(percentiles_HB_fb[:10])
z_scores_rel_height_fb = [(value - fastball_rel_height_mean) / fastball_rel_height_std for value in fastball_dict['RelHeight']]
percentiles_rel_height_fb = [stats.norm.cdf(z) * 100 for z in z_scores_rel_height_fb]
#print(percentiles_rel_height_fb[:10])
z_scores_extension_fb = [(value - fastball_extension_mean) / fastball_extension_std for value in fastball_dict['Extension']]
percentiles_extension_fb = [stats.norm.cdf(z) * 100 for z in z_scores_extension_fb]
#print(percentiles_extension_fb[:10])
z_scores_residual_fb = [(value - fastball_residual_mean) / fastball_residual_std for value in fastball_dict['Residual']]
percentiles_residual_fb = [stats.norm.cdf(z) * 100 for z in z_scores_residual_fb] 

# calculate ivb dev from fastball
changeup_splitter_ivb_dev = []
for i in range(len(changeup_splitter_dict['Pitcher'])):
    ivb_dev = changeup_splitter_dict['InducedVertBreak'][i] - fastball_IVB_mean
    abs_ivb_dev = abs(ivb_dev)
    changeup_splitter_ivb_dev.append(abs_ivb_dev)
changeup_splitter_dict['IVBDev'] = changeup_splitter_ivb_dev
# check IVBs are correct
#print("\nChangeup/Splitter IVBDev:")
#for pitcher, ivb_dev in zip(changeup_splitter_dict['Pitcher'], changeup_splitter_dict['IVBDev']):
 #   print(f"{pitcher}: {ivb_dev}")

# calculate rel speed dev from fastball
changeup_splitter_rel_speed_dev = []
for i in range(len(changeup_splitter_dict['Pitcher'])):
    rel_speed_dev = changeup_splitter_dict['RelSpeed'][i] - fastball_rel_speed_mean
    abs_rel_speed_dev = abs(rel_speed_dev)
    changeup_splitter_rel_speed_dev.append(abs_rel_speed_dev)
changeup_splitter_dict['RelSpeedDev'] = changeup_splitter_rel_speed_dev
# check rel speed devs are correct
#print("\nChangeup/Splitter RelSpeedDev:")
#for pitcher, rel_speed_dev in zip(changeup_splitter_dict['Pitcher'], changeup_splitter_dict['RelSpeedDev']):
 #   print(f"{pitcher}: {rel_speed_dev}") 
 

# changeup/splitter mean and std            
changeup_splitter_rel_speed_mean = np.mean(changeup_splitter_dict['RelSpeed'])
changeup_splitter_rel_speed_std = np.std(changeup_splitter_dict['RelSpeed'])
changeup_splitter_IVB_mean = np.mean(changeup_splitter_dict['InducedVertBreak'])
changeup_splitter_IVB_std = np.std(changeup_splitter_dict['InducedVertBreak'])
changeup_splitter_HB_mean = np.mean(changeup_splitter_dict['HorzBreak'])
changeup_splitter_HB_std = np.std(changeup_splitter_dict['HorzBreak'])
changeup_splitter_rel_height_mean = np.mean(changeup_splitter_dict['RelHeight'])
changeup_splitter_rel_height_std = np.std(changeup_splitter_dict['RelHeight'])
changeup_splitter_extension_mean = np.mean(changeup_splitter_dict['Extension'])
changeup_splitter_extension_std = np.std(changeup_splitter_dict['Extension'])
changeup_splitter_ivbdev_mean = np.mean(changeup_splitter_dict['IVBDev'])
changeup_splitter_ivbdev_std = np.std(changeup_splitter_dict['IVBDev'])
changeup_splitter_rel_speed_dev_mean = np.mean(changeup_splitter_dict['RelSpeedDev'])
changeup_splitter_rel_speed_dev_std = np.std(changeup_splitter_dict['RelSpeedDev'])

# changeup/splitter percentiles
z_scores_rel_speed_changeup_splitter = [(value - changeup_splitter_rel_speed_mean) / changeup_splitter_rel_speed_std for value in changeup_splitter_dict['RelSpeed']]
percentiles_rel_speed_changeup_splitter = [stats.norm.cdf(z) * 100 for z in z_scores_rel_speed_changeup_splitter]
#print(percentiles_rel_speed_changeup_splitter[:10])
z_scores_IVB_changeup_splitter = [(value - changeup_splitter_IVB_mean) / changeup_splitter_IVB_std for value in changeup_splitter_dict['InducedVertBreak']]
percentiles_IVB_changeup_splitter = [stats.norm.cdf(z) * 100 for z in z_scores_IVB_changeup_splitter]
#print(percentiles_IVB_changeup_splitter[:10])
z_scores_HB_changeup_splitter = [(value - changeup_splitter_HB_mean) / changeup_splitter_HB_std for value in changeup_splitter_dict['HorzBreak']]
percentiles_HB_changeup_splitter = [stats.norm.cdf(z) * 100 for z in z_scores_HB_changeup_splitter]
#print(percentiles_HB_changeup_splitter[:10])
z_scores_rel_height_changeup_splitter = [(value - changeup_splitter_rel_height_mean) / changeup_splitter_rel_height_std for value in changeup_splitter_dict['RelHeight']]
percentiles_rel_height_changeup_splitter = [stats.norm.cdf(z) * 100 for z in z_scores_rel_height_changeup_splitter]
#print(percentiles_rel_height_changeup_splitter[:10])
z_scores_extension_changeup_splitter = [(value - changeup_splitter_extension_mean) / changeup_splitter_extension_std for value in changeup_splitter_dict['Extension']]
percentiles_extension_changeup_splitter = [stats.norm.cdf(z) * 100 for z in z_scores_extension_changeup_splitter]
#print(percentiles_extension_changeup_splitter[:10])
z_scores_ivbdev_changeup_splitter = [(value - changeup_splitter_ivbdev_mean) / changeup_splitter_ivbdev_std for value in changeup_splitter_dict['IVBDev']]
percentiles_ivbdev_changeup_splitter = [stats.norm.cdf(z) * 100 for z in z_scores_ivbdev_changeup_splitter]
z_scores_rel_speed_dev_changeup_splitter = [(value - changeup_splitter_rel_speed_dev_mean) / changeup_splitter_rel_speed_dev_std for value in changeup_splitter_dict['RelSpeedDev']]
percentiles_rel_speed_dev_changeup_splitter = [stats.norm.cdf(z) * 100 for z in z_scores_rel_speed_dev_changeup_splitter]

# curveball mean and std            
curveball_rel_speed_mean = np.mean(curveball_dict['RelSpeed'])
curveball_rel_speed_std = np.std(curveball_dict['RelSpeed'])
curveball_IVB_mean = np.mean(curveball_dict['InducedVertBreak'])
curveball_IVB_std = np.std(curveball_dict['InducedVertBreak'])
curveball_HB_mean = np.mean(curveball_dict['HorzBreak'])
curveball_HB_std = np.std(curveball_dict['HorzBreak'])
curveball_rel_height_mean = np.mean(curveball_dict['RelHeight'])
curveball_rel_height_std = np.std(curveball_dict['RelHeight'])
curveball_extension_mean = np.mean(curveball_dict['Extension'])
curveball_extension_std = np.std(curveball_dict['Extension'])

# curveball percentiles
z_scores_rel_speed_cb = [(value - curveball_rel_speed_mean) / curveball_rel_speed_std for value in curveball_dict['RelSpeed']]
percentiles_rel_speed_cb = [stats.norm.cdf(z) * 100 for z in z_scores_rel_speed_cb]
#print(percentiles_rel_speed_cb[:10])
z_scores_IVB_cb = [(value - curveball_IVB_mean) / curveball_IVB_std for value in curveball_dict['InducedVertBreak']]
percentiles_IVB_cb = [stats.norm.cdf(z) * 100 for z in z_scores_IVB_cb]
#print(percentiles_IVB_cb[:10])
z_scores_HB_cb = [(value - curveball_HB_mean) / curveball_HB_std for value in curveball_dict['HorzBreak']]
percentiles_HB_cb = [stats.norm.cdf(z) * 100 for z in z_scores_HB_cb]
#print(percentiles_HB_cb[:10])
z_scores_rel_height_cb = [(value - curveball_rel_height_mean) / curveball_rel_height_std for value in curveball_dict['RelHeight']]
percentiles_rel_height_cb = [stats.norm.cdf(z) * 100 for z in z_scores_rel_height_cb]
#print(percentiles_rel_height_cb[:10])
z_scores_extension_cb = [(value - curveball_extension_mean) / curveball_extension_std for value in curveball_dict['Extension']]
percentiles_extension_cb = [stats.norm.cdf(z) * 100 for z in z_scores_extension_cb]
#print(percentiles_extension_cb[:10])

# sinker mean and std            
sinker_rel_speed_mean = np.mean(sinker_dict['RelSpeed'])
sinker_rel_speed_std = np.std(sinker_dict['RelSpeed'])
sinker_IVB_mean = np.mean(sinker_dict['InducedVertBreak'])
sinker_IVB_std = np.std(sinker_dict['InducedVertBreak'])
sinker_HB_mean = np.mean(sinker_dict['HorzBreak'])
sinker_HB_std = np.std(sinker_dict['HorzBreak'])
sinker_rel_height_mean = np.mean(sinker_dict['RelHeight'])
sinker_rel_height_std = np.std(sinker_dict['RelHeight'])
sinker_extension_mean = np.mean(sinker_dict['Extension'])
sinker_extension_std = np.std(sinker_dict['Extension'])

# sinker percentiles
z_scores_rel_speed_sinker = [(value - sinker_rel_speed_mean) / sinker_rel_speed_std for value in sinker_dict['RelSpeed']]
percentiles_rel_speed_sinker = [stats.norm.cdf(z) * 100 for z in z_scores_rel_speed_sinker]
#print(percentiles_rel_speed_sinker[:10])
z_scores_IVB_sinker = [(value - sinker_IVB_mean) / sinker_IVB_std for value in sinker_dict['InducedVertBreak']]
percentiles_IVB_sinker = [stats.norm.cdf(z) * 100 for z in z_scores_IVB_sinker]
#print(percentiles_IVB_sinker[:10])
z_scores_HB_sinker = [(value - sinker_HB_mean) / sinker_HB_std for value in sinker_dict['HorzBreak']]
percentiles_HB_sinker = [stats.norm.cdf(z) * 100 for z in z_scores_HB_sinker]
#print(percentiles_HB_sinker[:10])
z_scores_rel_height_sinker = [(value - sinker_rel_height_mean) / sinker_rel_height_std for value in sinker_dict['RelHeight']]
percentiles_rel_height_sinker = [stats.norm.cdf(z) * 100 for z in z_scores_rel_height_sinker]
#print(percentiles_rel_height_sinker[:10])
z_scores_extension_sinker = [(value - sinker_extension_mean) / sinker_extension_std for value in sinker_dict['Extension']]
percentiles_extension_sinker = [stats.norm.cdf(z) * 100 for z in z_scores_extension_sinker]
#print(percentiles_extension_sinker[:10])

# calculate scores
scores_slider_cutter = (slider_cutter_IVB * np.array(percentiles_IVB_slider_cutter) + slider_cutter_rel_speed * np.array(percentiles_rel_speed_slider_cutter) + slider_cutter_rel_height * np.array(percentiles_rel_height_slider_cutter) + slider_cutter_extension * np.array(percentiles_extension_slider_cutter) + slider_cutter_hb * np.array(percentiles_HB_slider_cutter))
scores_curveball = (curveball_IVB * np.array(percentiles_IVB_cb) + curveball_rel_speed * np.array(percentiles_rel_speed_cb) + curveball_rel_height * np.array(percentiles_rel_height_cb) + curveball_extension * np.array(percentiles_extension_cb) + curveball_hb * np.array(percentiles_HB_cb))
scores_sinker = (sinker_IVB * np.array(percentiles_IVB_sinker) + sinker_rel_speed * np.array(percentiles_rel_speed_sinker) + sinker_rel_height * np.array(percentiles_rel_height_sinker) + sinker_extension * np.array(percentiles_extension_sinker) + sinker_hb * np.array(percentiles_HB_sinker))
scores_fastball = (fastball_IVB * np.array(percentiles_IVB_fb) + fastball_rel_speed * np.array(percentiles_rel_speed_fb) + fastball_rel_height * np.array(percentiles_rel_height_fb) + fastball_extension * np.array(percentiles_extension_fb) + fastball_hb * np.array(percentiles_HB_fb) + fastball_residual * np.array(percentiles_residual_fb))
scores_changeup_splitter = (changeup_splitter_IVB * np.array(percentiles_IVB_changeup_splitter) + changeup_splitter_rel_speed * np.array(percentiles_rel_speed_changeup_splitter) + changeup_splitter_rel_height * np.array(percentiles_rel_height_changeup_splitter) + changeup_splitter_extension * np.array(percentiles_extension_changeup_splitter) + changeup_splitter_hb * np.array(percentiles_HB_changeup_splitter) + changeup_splitter_IVB_dev * np.array(percentiles_ivbdev_changeup_splitter) + changeup_splitter_relspeed_dev * np.array(percentiles_rel_speed_dev_changeup_splitter))

print(new_roster)
print("Slider/Cutter Scores:")
for pitcher, score in zip(slider_cutter_dict['Pitcher'], scores_slider_cutter):
    if pitcher in new_roster: 
        print(f"{pitcher}: {score:.2f}")

print("\nCurveball Scores:")
for pitcher, score in zip(curveball_dict['Pitcher'], scores_curveball):
    if pitcher in new_roster: 
        print(f"{pitcher}: {score:.2f}")

print("\nSinker Scores:")
for pitcher, score in zip(sinker_dict['Pitcher'], scores_sinker):
    if pitcher in new_roster: 
        print(f"{pitcher}: {score:.2f}")

print("\nFastball Scores:")
for pitcher, score in zip(fastball_dict['Pitcher'], scores_fastball):
    if pitcher in new_roster: 
        print(f"{pitcher}: {score:.2f}")

print("\nChangeup/Splitter Scores:")
for pitcher, score in zip(changeup_splitter_dict['Pitcher'], scores_changeup_splitter):
    if pitcher in new_roster: 
        print(f"{pitcher}: {score:.2f}")


# Create a list of dictionaries for each pitch type
pitch_types = ['Slider/Cutter', 'Curveball', 'Sinker', 'Fastball', 'Changeup/Splitter']
pitch_dicts = [
    {'Pitch Type': pitch_type, 'Pitcher': pitcher, 'Score': score}
    for pitch_type, pitchers, scores in zip(
        pitch_types,
        [slider_cutter_dict['Pitcher'], curveball_dict['Pitcher'], sinker_dict['Pitcher'], fastball_dict['Pitcher'], changeup_splitter_dict['Pitcher']],
        [scores_slider_cutter, scores_curveball, scores_sinker, scores_fastball, scores_changeup_splitter]
    )
    for pitcher, score in zip(pitchers, scores)
    if pitcher in new_roster
]

# Define the CSV file path
csv_file = 'pitch_scores.csv'

# Define fieldnames for the CSV
fieldnames = ['Pitch Type', 'Pitcher', 'Score']

# Write data to the CSV file
with open(csv_file, mode='w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    
    # Write the header
    writer.writeheader()
    
    # Write each row with scores formatted to 2 decimal places
    for pitch_dict in pitch_dicts:
        pitch_dict['Score'] = '{:.2f}'.format(pitch_dict['Score'])  # Format score to 2 decimal places
        writer.writerow(pitch_dict)