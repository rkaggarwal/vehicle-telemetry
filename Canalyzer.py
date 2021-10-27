# -*- coding: utf-8 -*-
"""
Created on Sat Sep 18 20:30:30 2021

@author: raggarwal
"""

"""
This script takes in a raw LOG.TXT file from the SD card, which is in a 
time/CAN Address/message format, and translates the CAN codes using a VW
.dbc file.  Some interesting variables are plotted, and all of the
vars are stored as a dict-of-dicts (that have different sampling rates).
TODO: zero or first-order hold vars to have a common sampling rate
      cantools also doesn't seem to be decoding correctly, so doing manual bit
      decodes for now.
"""



import tkinter
from tkinter.filedialog import askopenfilename
import pandas as pd
import numpy as np
from scipy import interpolate
import matplotlib.pyplot as plt
import os
import scipy as sp
import scipy.io as sio
import cantools


G = 9.81; # m/s^2
KM_TO_MI = 1.60934; # kilometers per mile
RPM_TO_RADPS = 1/60*2*np.pi;

plt.close('all');



# Ask the user for the file (should be a .txt file from the SD card)
tkinter.Tk().withdraw()
filename = askopenfilename()
print(filename)

base = os.path.basename(filename);
name = os.path.splitext(base)[0];


# Load the .csv contents into a dataframe for analysis
raw_df = pd.read_csv(filename, delimiter = ", ");

# https://www.csselectronics.com/pages/can-dbc-file-database-intro
# (scale, offset)

# Bit start|length (bits) @1+ means little endian (LSB -> MSB)
# so the start/end bits are in order from left to right,
# but each bit means more the further to the right it is.

# when doing LSB/MSB reversal, it's byte-by-byte.  NOT bit-by-bit.
# so, take the bytes and reverse their order on an inter-byte basis

# the shortened file loads successfully, just removed some misc vars that 
# were incorrectly formatted
db = cantools.database.load_file('vw_golf_mk4_shortened.dbc', strict = True)

# db_motor1 = db.get_message_by_name('Motor_1');
# db_motor2 = db.get_message_by_name('Motor_2');
# db_motor3 = db.get_message_by_name('Motor_3');
# db_kombi1 = db.get_message_by_name('Kombi_1');






## Motor flexia
# SG_ Max_Drehmoment m0 : 32|8@1+ (10,0) [0|2550] "Nm" XXX

flexia = raw_df[(raw_df['ID [HEX]'] == "580")]

flexia_size = len(flexia);
flexia_dict = {};
flexia_dict['time_s'] = np.zeros(flexia_size);
flexia_dict['max_moment_nm'] = np.zeros(flexia_size);
flexia_dict['db_max_moment_nm'] = np.zeros(flexia_size);

counter = 0;
for index, row in flexia.iterrows():
    flexia_dict['time_s'][counter] = row['Time [ms]']/1000;
    temp = db.decode_message('Motor_Flexia', bytes(flexia.iloc[counter]['Message [HEX]'], encoding = 'utf-8'), scaling = True)

    flexia_dict['max_moment_nm'][counter] =  int(flexia.iloc[counter]['Message [HEX]'][8:10], 16)*10;
    flexia_dict['db_max_moment_nm'][counter] =  temp['Max_Drehmoment'];
    counter = counter + 1;

max_motor_moment_nm = 280; # hard coded at 280 Nm, otherwise flexia_dict['db_max_moment_nm'][0]; # these all should be the same...
#max_motor_moment_interp_fcn = interpolate.interp1d(flexia_dict['time_s'], flexia_dict['max_moment_nm'], kind = 'nearest', fill_value = "extrapolate");









## Motor 1 Data
# SG_ Motordrehzahl : 16|16@1+ (0.25,0) [0|16256] "U/min" XXX
# SG_ Fahrpedalwert_oder_Drosselklapp : 40|8@1+ (0.4,0) [0|101.6] "%" XXX
# SG_ Fahrerwunschmoment : 56|8@1+ (0.39,0) [0|99] "MDI" XXX
# SG_ inneres_Motor_Moment : 8|8@1+ (0.39,0) [0|99] "MDI" XXX

motor1 = raw_df[(raw_df['ID [HEX]'] == "280")]

m1_size = len(motor1);
motor1_dict = {};

# my manual decoding of variables
motor1_dict['time_s'] = np.zeros(m1_size);
motor1_dict['engineSpeed_rpm'] = np.zeros(m1_size);
motor1_dict['throttlePedalOrBody_pct'] = np.zeros(m1_size);
motor1_dict['driverReqTorque_Nm'] = np.zeros(m1_size);
motor1_dict['innerMotorTorque_Nm'] = np.zeros(m1_size);

# cantools database parsed variables
motor1_dict['db_engineSpeed_rpm'] = np.zeros(m1_size);
motor1_dict['db_throttlePedalOrBody_pct'] = np.zeros(m1_size);
motor1_dict['db_driverReqTorque_Nm'] = np.zeros(m1_size);
motor1_dict['db_innerMotorTorque_Nm'] = np.zeros(m1_size);

counter = 0;
for index, row in motor1.iterrows():
    motor1_dict['time_s'][counter] = row['Time [ms]']/1000;
    motor1_dict['engineSpeed_rpm'][counter] = (int(motor1.iloc[counter]['Message [HEX]'][6:8], 16)*256 + int(motor1.iloc[counter]['Message [HEX]'][4:6], 16))/4;
    motor1_dict['throttlePedalOrBody_pct'][counter] = int(motor1.iloc[counter]['Message [HEX]'][10:12], 16)*.4;
    motor1_dict['driverReqTorque_Nm'][counter] = int(motor1.iloc[counter]['Message [HEX]'][14:16], 16)*.39/100*280; #max_motor_moment_interp_fcn(row['Time [ms]']/1000);
    motor1_dict['innerMotorTorque_Nm'][counter] = int(motor1.iloc[counter]['Message [HEX]'][2:4], 16)*.39/100*280; #max_motor_moment_interp_fcn(row['Time [ms]']/1000);
    
    #db.refresh();
    bytedata = bytes(motor1.iloc[counter]['Message [HEX]'], encoding = 'utf-8')
    temp = db.decode_message('Motor_1', bytedata, scaling = True)
    motor1_dict['db_engineSpeed_rpm'][counter] = temp['Motordrehzahl'];
    motor1_dict['db_throttlePedalOrBody_pct'][counter] = temp['Fahrpedalwert_oder_Drosselklapp'];
    motor1_dict['db_driverReqTorque_Nm'][counter] = temp['inneres_Motor_Moment']/100*max_motor_moment_nm;
    motor1_dict['db_innerMotorTorque_Nm'][counter] = temp['Fahrerwunschmoment']/100*max_motor_moment_nm;

    counter = counter + 1;






## Motor 2 Data
# SG_ Fahrzeuggeschwindigkeit : 24|8@1+ (1.28,0) [0|325] "km/h" XXX
motor2 = raw_df[(raw_df['ID [HEX]'] == "288")]

m2_size = len(motor2);
motor2_dict = {};
motor2_dict['time_s'] = np.zeros(m2_size);
motor2_dict['speed_kmph'] = np.zeros(m2_size);

counter = 0;
for index, row in motor2.iterrows():
    motor2_dict['time_s'][counter] = row['Time [ms]']/1000;
    motor2_dict['speed_kmph'][counter] =  int(motor2.iloc[counter]['Message [HEX]'][6:8], 16)*1.28;
    counter = counter + 1;

motor2_dict['speed_mph'] = motor2_dict['speed_kmph']/KM_TO_MI;









## Motor 3 Data
motor3 = raw_df[(raw_df['ID [HEX]'] == "380")]

# SG_ Drosselklappenpoti : 56|8@1+ (0.4,0) [0|101.6] "%" XXX
# SG_ Fahrpedal_Rohsignal : 16|8@1+ (0.4,0) [0|101.6] "%" XXX

m3_size = len(motor3);
motor3_dict = {};
motor3_dict['time_s'] = np.zeros(m3_size);
motor3_dict['throttleBody_pct'] = np.zeros(m3_size);
motor3_dict['throttlePedal_pct'] = np.zeros(m3_size);

counter = 0;
for index, row in motor3.iterrows():
    motor3_dict['time_s'][counter] = row['Time [ms]']/1000;
    motor3_dict['throttleBody_pct'][counter] =  int(motor3.iloc[counter]['Message [HEX]'][14:16], 16)*.4;
    motor3_dict['throttlePedal_pct'][counter] = int(motor3.iloc[counter]['Message [HEX]'][4:6], 16)*.4;
    counter = counter + 1;






## Kombi 1 Data
kombi1 = raw_df[(raw_df['ID [HEX]'] == "320")]
# SG_ Geschwindigkeit__Kombi_1_ : 25|15@1+ (0.01,0) [0|326] "km/h" XXX

k1_size = len(kombi1);
kombi1_dict = {};
kombi1_dict['time_s'] = np.zeros(k1_size);
kombi1_dict['speed_kmph'] = np.zeros(k1_size);

counter = 0;
for index, row in kombi1.iterrows():
    kombi1_dict['time_s'][counter] = row['Time [ms]']/1000;
    temp = bin(int(kombi1.iloc[counter]['Message [HEX]'], 16))[2:].zfill(8*8); # this is the full 64-bit binary string of data
    
    
    # temp = int(kombi1.iloc[counter]['Message [HEX]'][6:8], 16)*1.28;
    #     motor1_dict['engineSpeed_rpm'][counter] = (int(motor1.iloc[counter]['Message [HEX]'][6:8], 16)*256 + int(motor1.iloc[counter]['Message [HEX]'][4:6], 16))/4;


    kombi1_dict['speed_kmph'][counter] =  (int(temp[32:40], 2)*256 + int(temp[25:32], 2))*.01;

    # kombi1_dict['speed_kmph'][counter] =  (int(kombi1.iloc[counter]['Message [HEX]'][8:10], 16)*256 + int(kombi1.iloc[counter]['Message [HEX]'][6:8], 16))*.01;
    counter = counter + 1;

kombi1_dict['speed_mph'] = kombi1_dict['speed_kmph']/KM_TO_MI;



## Bremse (Brake) 1 Data
bremse1 = raw_df[(raw_df['ID [HEX]'] == "1A0")]
# SG_ Geschwindigkeit_neu__Bremse_1_ : 17|15@1+ (0.01,0) [0|326.39] "km/h" XXX

b1_size = len(bremse1);
bremse1_dict = {};
bremse1_dict['time_s'] = np.zeros(b1_size);
bremse1_dict['speed_kmph'] = np.zeros(b1_size);

counter = 0;
for index, row in bremse1.iterrows():
    bremse1_dict['time_s'][counter] = row['Time [ms]']/1000;
    temp = bin(int(bremse1.iloc[counter]['Message [HEX]'], 16))[2:].zfill(8*8); # this is the full 64-bit binary string of data
    
    bremse1_dict['speed_kmph'][counter] =  (int(temp[24:32], 2)*256 + int(temp[17:24], 2))/180; #.01; for some reason a 1/180 multiplier gives the correct speed, and not 1/100. 
    counter = counter + 1;

bremse1_dict['speed_mph'] = bremse1_dict['speed_kmph']/KM_TO_MI;







# fig0, ax0 = plt.subplots(6, 1);
# fig0.suptitle("Manual vs cantools decoding");

# ax0[0].plot(motor1_dict['time_s'], motor1_dict['engineSpeed_rpm'], color = 'b');
# ax0[1].plot(motor1_dict['time_s'], motor1_dict['driverReqTorque_Nm'], color = 'b');
# ax0[2].plot(motor1_dict['time_s'], motor1_dict['innerMotorTorque_Nm'], color = 'b');
# # ax0[3].plot(motor1_dict['time_s'], kombi1_dict['speed_mph'], color = 'b');
# # ax0[4].plot(motor1_dict['time_s'], motor3_dict['throttlePedal_pct'], color = 'b');
# # ax0[5].plot(motor1_dict['time_s'], motor3_dict['throttleBody_pct'], color = 'b');

# ax0[0].plot(motor1_dict['time_s'], motor1_dict['db_engineSpeed_rpm'], color = 'r');
# ax0[1].plot(motor1_dict['time_s'], motor1_dict['db_driverReqTorque_Nm'], color = 'r');
# ax0[2].plot(motor1_dict['time_s'], motor1_dict['db_innerMotorTorque_Nm'], color = 'r');
# # ax0[3].plot(motor1_dict['time_s'], kombi1_dict['db_speed_mph'], color = 'r');
# # ax0[4].plot(motor1_dict['time_s'], motor3_dict['db_throttlePedal_pct'], color = 'r');
# # ax0[5].plot(motor1_dict['time_s'], motor3_dict['db_throttleBody_pct'], color = 'r');




# Generate torque and power points only at wide open throttle
time_wot = np.zeros_like(motor1_dict['time_s']);
torque_wot = np.zeros_like(motor1_dict['innerMotorTorque_Nm']);
rpm_wot = np.zeros_like(motor1_dict['engineSpeed_rpm']);
throttlebody_interpfcn = interpolate.interp1d(motor3_dict['time_s'], motor3_dict['throttleBody_pct'], fill_value = "extrapolate");

for i in range(len(motor1_dict['time_s'])):
    if(throttlebody_interpfcn(motor1_dict['time_s'][i]) >= 99):
        # we're at ~wot
        time_wot[i] = motor1_dict['time_s'][i];
        torque_wot[i] = motor1_dict['innerMotorTorque_Nm'][i];
        rpm_wot[i] = motor1_dict['engineSpeed_rpm'][i];
        






## Plotting
fig1, ax1 = plt.subplots(2, 2, constrained_layout = True);
fig1.suptitle("Engine variables");


ax1[0, 0].plot(motor1_dict['time_s'], motor1_dict['engineSpeed_rpm'], color = 'b');
# ax1[0, 0].set_title("Engine speed [RPM] and Vehicle speed [mph]");
ax1[0, 0].set_xlabel("Time [s]");
ax1[0, 0].set_ylabel("RPM");
ax1[0, 0].yaxis.label.set_color('blue')
# ax1_00_twin = ax1[0, 0].twinx();
# ax1_00_twin.plot(bremse1_dict['time_s'], bremse1_dict['speed_mph'], color = 'red')
# ax1_00_twin.set_ylabel("Speed [mph]");
# ax1_00_twin.yaxis.label.set_color('red')


ax1[0, 1].plot(motor1_dict['time_s'], motor1_dict['driverReqTorque_Nm'], label = 'requested torque');
ax1[0, 1].plot(motor1_dict['time_s'], motor1_dict['innerMotorTorque_Nm'], label = 'ECU-estimated torque');
ax1[0, 1].legend(loc = 'lower right');
ax1[0, 1].set_xlabel("Time [s]");
ax1[0, 1].set_ylabel("Torque [Nm]");





# ax1[1, 0].scatter(motor1_dict['engineSpeed_rpm'], motor1_dict['innerMotorTorque_Nm'], s = 2, color = 'blue', label = "Torque [Nm]");
ax1[1, 0].scatter(rpm_wot, torque_wot, s = 2, color = 'blue', label = "Torque [Nm]");
ax1[1, 0].set_ylabel("Torque [Nm]");
ax1_10_twin = ax1[1, 0].twinx();
# ax1_10_twin.scatter(motor1_dict['engineSpeed_rpm'], (1/60*2*np.pi)*motor1_dict['engineSpeed_rpm']*motor1_dict['innerMotorTorque_Nm']/746, s = 2, color = 'red', label = "Power [hp]");
ax1_10_twin.scatter(rpm_wot, (1/60*2*np.pi)*rpm_wot*torque_wot/746, s = 2, color = 'red', label = "Power [hp]");
ax1_10_twin.set_ylabel("Power [hp]")
ax1[1, 0].set_xlabel("RPM")
ax1[1, 0].yaxis.label.set_color('blue')
ax1_10_twin.yaxis.label.set_color('red')



ax1[1, 1].plot(motor3_dict['time_s'], motor3_dict['throttlePedal_pct'], label = 'throttle pedal %');
ax1[1, 1].plot(motor3_dict['time_s'], motor3_dict['throttleBody_pct'], label = 'throttle body %');
ax1[1, 1].legend(loc = 'lower right');
ax1[1, 1].set_xlabel("Time [s]");
ax1[1, 1].set_ylabel("Percent");


# ax1[0, 0].set_xlim(25, 50);
# ax1[0, 1].set_xlim(25, 50);
# ax1[1, 1].set_xlim(25, 50);





# Plot the torque/power curve for only a certain time window (e.g. a single gear)
t_start = 28.5;
t_end = 31.5;


fig2, ax2 = plt.subplots();
fig2.suptitle("Time range: t = {} to {}".format(t_start, t_end));
start_index = (np.abs(time_wot - t_start)).argmin()
end_index = (np.abs(time_wot - t_end)).argmin()

ax2.scatter(rpm_wot[start_index:end_index], torque_wot[start_index:end_index], s = 2, color = 'blue', label = "Torque [Nm]");
ax2.set_ylabel("Torque [Nm]");
ax2_twin = ax2.twinx();
ax2_twin.scatter(rpm_wot[start_index:end_index], (1/60*2*np.pi)*rpm_wot[start_index:end_index]*torque_wot[start_index:end_index]/746, s = 2, color = 'red', label = "Power [hp]");
ax2_twin.set_ylabel("Power [hp]")
ax2.set_xlabel("RPM")
ax2.yaxis.label.set_color('blue')
ax2_twin.yaxis.label.set_color('red')

