#!/usr/bin/env python3
####################################################
#
# Description: Python code to acquire and output data
# Omnipresesence OPS-243A radar card. Code has borrowed
# elements from Github omnipresense python_utilities
# https://github.com/omnipresense/python_utilities
# amattas / speedtrap - https://github.com/amattas/speedtrap 
# and a simple radar sign:
# https://www.instructables.com/Low-Cost-Radar-Speed-Sign/
#####################################################


# Modifiable parameters
# Ops243 module settings:
Ops243_Speed_Report = 'OS'
Ops243_Range_Report_Off = 'Od'
Ops243_Speed_Output_Units = 'US'
Ops243_Direction_Control = 'R|'
Ops243_Sampling_Frequency = 'S2'
Ops243_Data_Precision = 'F2'
Ops243_Transmit_Power = 'PX'
Ops243_Data_Precision = 'F2'
Ops243_Blank_Data_Reporting = 'BZ'
Ops243_json_Reporting = 'OJ'
Ops243_Magnitude_Reporting = 'OM'
Ops243_Radar_Sign_Reporting = 'ON'


# Imports
import os
import sys
import time
import datetime
from decimal import *
import serial
import RPi.GPIO as GPIO
import re
import pandas as pd
import numpy as np
import json
from PIL import Image, ImageDraw, ImageFont
import subprocess

# Photo routine based off detected vehicle speed

def take_photo(name):
# Using raspistill legacy, but could shift to libcamera    
    cmd = "raspistill --width 3280 --height 2464 --exposure sports --ev 0.5 -n -t 600 --timelapse 500 -o "+name+"_%d.jpg"
    subprocess.run(cmd, shell = True)
    return(name)

def annotate_photo(name):
    print("annotate photo entered")
    font = ImageFont.truetype(r'/home/pi/python/camera/bebas/Bebas-Regular.ttf', 64)
    image = Image.open(name)
    basename = os.path.basename(name)
    print(basename)
    myfields = basename.split('_')
    pdate = myfields[0]
    ptime = myfields[1]
    ptime=ptime.replace('-',':')
#    print('ptime after replace: ',ptime)
    tempspeed = myfields[2].split('.')
    pspeed = tempspeed[0]+'.'+tempspeed[1]
    pic_string = 'Date:'+pdate+'  Time:'+ptime+'  Speed:'+pspeed
    print(pic_string)
# set image width
    width, height = image.size 
    draw = ImageDraw.Draw(image)
    text = pic_string
    textwidth, textheight = draw.textsize(text)
    ymargin = 100
    xmargin = 850
    x = width - textwidth - xmargin
    y = height - textheight - ymargin
    draw.text((x, y), text,(0,0,0),font=font)
    image.save(name)
    return(name)   

# Initialize the USB port to read from the OPS-243A module
ser=serial.Serial(
    port = '/dev/ttyACM0',
    baudrate = 9600,
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    bytesize = serial.EIGHTBITS,
    timeout = 1,
    writeTimeout = 2
)
ser.flushInput()
ser.flushOutput()

# sendSerialCommand: function for sending commands to the OPS-243A module
def sendSerCmd(descrStr, commandStr) :
    data_for_send_str = commandStr
    data_for_send_bytes = str.encode(data_for_send_str)
    print(descrStr, commandStr)
    ser.write(data_for_send_bytes)
    # Initialize message verify checking
    ser_message_start = '{'
    ser_write_verify = False
    # Print out module response to command string
    while not ser_write_verify :
        data_rx_bytes = ser.readline()
        data_rx_length = len(data_rx_bytes)
        if (data_rx_length != 0) :
            data_rx_str = str(data_rx_bytes)
            if data_rx_str.find(ser_message_start) :
                print(data_rx_str)
                ser_write_verify = True

# Initialize and query Ops243A Module
print("\nInitializing Ops243A Module")
sendSerCmd("\nSet Speed Speed Report: ", Ops243_Speed_Report)
time.sleep(1.2)
sendSerCmd("\nSet Speed Speed Report: ", Ops243_Range_Report_Off)
time.sleep(1.2) 
sendSerCmd("\nSet Speed Output Units: ", Ops243_Speed_Output_Units)
time.sleep(2)
sendSerCmd("\nSet Speed Speed Report: ", Ops243_Speed_Report)
time.sleep(1.2)
sendSerCmd("\nSet Direction Control: ", Ops243_Direction_Control)
time.sleep(1.2)
sendSerCmd("\nSet Sampling Frequency: ", Ops243_Sampling_Frequency)
time.sleep(1.2)
sendSerCmd("\nSet Transmit Power: ", Ops243_Transmit_Power)
time.sleep(1.2)
sendSerCmd("\nSet Data Precision: ", Ops243_Data_Precision)
time.sleep(1.2)
sendSerCmd("\nSet Blank Data Reporting: ", Ops243_Blank_Data_Reporting)
time.sleep(1.2)
sendSerCmd("\nSet Json_Reporting: ", Ops243_json_Reporting)
time.sleep(1.2)
sendSerCmd("\nSet Magnitude_Reporting: ", Ops243_Magnitude_Reporting)
time.sleep(1.2)

ser=serial.Serial(
    port = '/dev/ttyACM0',
    baudrate = 9600,
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    bytesize = serial.EIGHTBITS,
    timeout = 0.01,
    writeTimeout = 2
    )

# Speed limit display loop
done = False
# Flush serial buffers
ser.flushInput()
ser.flushOutput()
# Reset timers
start_time = time.time()
current_time = start_time
delta_time = 0.0
# Initial state 
speed_max = 0.0
speed_Limit = 25.0
speed_Lim_Offset = 5
speed_cut_low=8.0
daily_speed=[]
daily_mag=[]
daily_time=[]
daily_count=[]
lst_size = 180000
lst_speed = 0
spd_delta = 0
spd_counter = 0
df_north = pd.DataFrame()
df_south = pd.DataFrame()
now = datetime.datetime.now()

counter = 0


#last_date = None
cur_Hr = datetime.datetime.now().hour
cur_Min = datetime.datetime.now().minute
cur_Sec = datetime.datetime.now().second
cur_Day = datetime.datetime.now().day
cur_Mo = datetime.datetime.now().month
cur_Yr = datetime.datetime.now().year
last_date = datetime.datetime(year=cur_Yr,month=cur_Mo,day=cur_Day,hour=23,minute=59,second=59)

print('current hour is: ',cur_Hr)

while True:
    today=datetime.datetime.now()
#    today=datetime.datetime.now().minute
    cur_day = today.strftime("%Y-%m-%d %H:%M:%S")
    print('date is: ',cur_day)

    while not done:
        time.sleep(.10)
        # Check for speed info from OPS243-A
        speed_available = False
        spd=0
        mag=0
        Ops243_rx_float = 0.0
        try:
             Ops243_rx_bytes = ser.readline()
             Ops243_rx_bytes_length = len(Ops243_rx_bytes)
        except:
             pass

        if(Ops243_rx_bytes_length != 0) :
             try:
                 current_report_json = json.loads(Ops243_rx_bytes)
                 Ops243_rx_float = float(current_report_json['speed'])
                 mag = float(current_report_json['magnitude'])
                 speed_available = True
             except:
                 pass

             if speed_available == True :
                 now = datetime.datetime.now()
                 spd = Ops243_rx_float
                 if counter >= 1:
                    spd_delta = spd - lst_speed
                    lst_speed = spd
                 if abs(spd_delta) >= speed_cut_low:
                    spd_counter = spd_counter + 1
        if abs(spd) > speed_cut_low:
            print('time, speed, and magnitude  are: ', now, spd,mag)
            daily_speed.append(spd)
            daily_mag.append(mag)
            daily_time.append(now.strftime("%Y-%m-%d %H:%M:%S.%f"))
            daily_count.append(spd_counter)
            if spd > speed_max :
                speed_max = spd
                start_time = today=datetime.datetime.now()
                current_time = start_time
            else :
                current_time = datetime.datetime.now()
        else :
            current_time =datetime.datetime.now()
        if abs(spd) > speed_Limit+speed_Lim_Offset:
            cur_Day = datetime.datetime.now().day
            cur_Mo = datetime.datetime.now().month
            cur_Yr = datetime.datetime.now().year
            cur_Hr = datetime.datetime.now().hour
            cur_min = datetime.datetime.now().minute
            cur_sec = datetime.datetime.now().second
            cur=datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f')[:-4]
# Setup and take photo
            date_str = str(cur)+'_'+str(spd)
            file_name= '/opt/ramdisk/'+date_str
            take_photo(file_name)
            
        cur_Day = datetime.datetime.now().day
        cur_Mo = datetime.datetime.now().month
        cur_Yr = datetime.datetime.now().year
        cur_Hr = datetime.datetime.now().hour
        cur_min = datetime.datetime.now().minute
        cur_sec = datetime.datetime.now().second
        dayTripper = cur_Hr + cur_min/60 + cur_sec/3600
        if counter==12600 or dayTripper >= 23.96:
#        if last_date < today:
            last_date = datetime.datetime(year=cur_Yr,month=cur_Mo,day=cur_Day,hour=23,minute=59,second=59)
            df = pd.DataFrame(data =[daily_time,daily_speed,daily_mag,daily_count])
            df=df.transpose()
            df.columns=['date_sp','speed','magnitude','vehicle_cnt']
            df['date']=pd.to_datetime(df['date_sp'],format="%Y-%m-%d %H:%M:%S.%f")
            df.index=df['date']
            df['speed'] = pd.to_numeric(df['speed'])
            df['magnitude'] = pd.to_numeric(df['magnitude'])
            print(df.speed.describe())
            
            if not df.empty:
                df = df.drop('date',axis=1)
                df = df.drop('date_sp',axis=1)
                df_south=df.loc[(df['speed'] >= speed_cut_low) & (df['speed'] <= 80)]
                df_north=df.loc[(df['speed'] <= -speed_cut_low) & (df['speed'] >= -80)]      

#           write out speeds to csv file
            date_str = str(cur_Yr)+'-'+str(cur_Mo)+'-'+str(cur_Day)+'_'+str(cur_Hr)+'-'+str(cur_min)
            filename='/home/pi/python/radar/'+date_str+'.csv'
            filenamen='/home/pi/python/radar/'+date_str+'n'+'.csv'
            filenames='/home/pi/python/radar/'+date_str+'s'+'.csv'
            if not df.empty:
                df.to_csv(filename, index=True,header=True,date_format='%m/%d/%Y %H:%M:%S.%f')
            if not df_south.empty:
                df_south.to_csv(filenames, index=True,header=True,date_format='%m/%d/%Y %H:%M:%S.%f')
            if not df_north.empty:
                df_north.to_csv(filenamen, index=True,header=True,date_format='%m/%d/%Y %H:%M:%S.%f')

            del daily_speed
            del daily_time
            del daily_mag
            del daily_count
            df=df[0:0]
            df_south=df_south[0:0]
            df_north=df_north[0:0]
            daily_speed=[]
            daily_mag=[]
            daily_time=[]
            daily_count=[]
            lst_speed = 0
            spd_counter = 0
            counter = 0
            daily_speed.append(0)
            daily_mag.append(0)
            daily_count.append(0)
            daily_time.append(now.strftime("%Y-%m-%d %H:%M:%S.%f"))
        counter=counter + 1


