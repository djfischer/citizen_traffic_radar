import requests
from bs4 import BeautifulSoup
import string
import json, ast
import dateutil.parser as dparser
from datetime import datetime, timezone, timedelta
from dateutil import relativedelta
import dateutil.parser
import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from csv import writer
import scipy.stats
import ast
import math
from tabulate import tabulate
import plotly.graph_objects as go
import scipy.stats as stats
import io
import pylab
from itertools import groupby
from matplotlib.backends.backend_pdf import PdfPages
import random
import calendar

def groupSequence(x):
    it = iter(x)
    prev, res = next(it), []
  
    while prev is not None:
        start = next(it, None)
  
        if prev + 1 == start:
            res.append(prev)
        elif res:
            yield list(res + [prev])
            res = []
        prev = start
        
# Get today's date info
cur_Day = datetime.now().day
cur_Mo = datetime.now().month
cur_Yr = datetime.now().year

# Set speed units (mph or m/s)
spd_units = input("Enter speed units in mps or mph: ")
if spd_units == "mps" or spd_units == "MPS":
    spd_convert = 2.237
if spd_units == "mph" or spd_units == "MPH":
    spd_convert = 1.0

# Setup loop to get number of days to process....

# Get input from user on input data and traffic direction
fileNum = input("Enter number of days of Cherry speed data to process: ")

# Build file name list

dateStart = input("Enter date of starting file e.g. mm/dd/yyyy: ")

dateS = datetime.strptime(dateStart, "%m/%d/%Y").strftime("%Y-%m-%d")
print(dateS)
day = datetime.strptime(dateS, "%Y-%m-%d").strftime("%d")
month = datetime.strptime(dateS, "%Y-%m-%d").strftime("%m")
year = datetime.strptime(dateS, "%Y-%m-%d").strftime("%Y")
print(day,month,year)

print(calendar.monthrange(int(year), int(month)))
monthEnd = calendar.monthrange(int(year), int(month))
print(monthEnd[1])

dateS = datetime.strptime(dateStart, "%m/%d/%Y")
for i in range(0,int(fileNum)):
    loopDate = dateS + timedelta(days=i)
    newDate = loopDate.strftime("%-m-%-d")
    newDate_Yr = loopDate.strftime("%-Y-%-m-%-d")
    print(newDate,newDate_Yr)
    ifileN = '/Users/djfi/python/radar/cherry/'+newDate_Yr+'/'+newDate+'n.csv'
    ifileS = '/Users/djfi/python/radar/cherry/'+newDate_Yr+'/'+newDate+'s.csv'
    print(ifileN)
    print(ifileS)
    
# Loop to process North & South directions
    for j in range(0,2):  
# First fix-up input file to strip out extra header lines
        if j== 0:
            ifile = ifileN
            v_dir = 'n'
            direction_txt = "Northbound"
        if j== 1:
            ifile = ifileS
            v_dir = 's'
            direction_txt = "Southbound"
        counter = 0
        with open(ifile, "r+") as f:
            # First read the file line by line
            lines = f.readlines()
            # Go back at the start of the file
            f.seek(0)
            # Go back at the start of the file
            f.truncate()
            # Truncate file size
            for line in lines:
                if counter == 0:
                    f.write(line)
                if 'date,' not in line and counter > 0:
                    f.write(line)
                counter = counter + 1
        f.close()

# Read in, index and sort dataframe

        speed = pd.read_csv(ifile)
        print(speed)
        speed['date']=pd.to_datetime(speed['date'], format='%m/%d/%Y %H:%M:%S.%f')
        speed.index = speed['date']
        speed.sort_index(inplace=True)
        speed['speed']=abs(speed['speed'])

#Eliminate duplicates
# dropping duplicate values
        speed.drop_duplicates(subset=None, inplace=True)

        print('speed before rows2skip is: ',speed)
        print('')

# Convert speed
        speed['speed']=(spd_convert*speed['speed'])
        print('speed after conversion is: ',speed)

# Check for spurious max speed values

        mu = 0.0
        sigma = 2.75
        rand = np.random.normal(mu, sigma, 100)
        for idx, row in speed.iterrows():
            if  speed.loc[idx,'speed'] >52.0:
                vary = random.choice(rand)
                speed.loc[idx,'speed'] = vary + 52.0

        avg_speed = speed['speed'].mean()
        cnt_list = speed['vehicle_cnt'].tolist()
        spd_list = speed['speed'].tolist()
        date_list = speed['date'].tolist()

        acquisition_time = speed.index[0]
        acq_yr = acquisition_time.strftime("%Y")
        acq_mo = acquisition_time.strftime("%m")
        acq_day = acquisition_time.strftime("%d")


# Eliminate data noise spike at 0 reading  (for ops241 only 41.4 to 41.7)
        rows2skip=[]
#rows2skip = [idx for idx, val in enumerate (spd_list) if abs(val) >= 41.4 and abs(val) <= 41.8]
        rows2skip = [idx for idx, val in enumerate (spd_list) if abs(val) == 0.0]

        counter = 0
        for element in rows2skip:
            rows2skip[counter] = rows2skip[counter]+1
            counter = counter +1
# print('rows2skip after spike filtering is: ',rows2skip[counter-1])
        print(rows2skip)
        print('')

        print('/Users/djfi/python/radar/cherry/summaries/speed_rows_skip1'+'_'+str(acq_mo)+'-'+str(acq_day)+'-'+str(acq_yr)+'.csv')

#Write out noise-corrected data
        speed.to_csv('/Users/djfi/python/radar/cherry/summaries/speed_rows_skip1'+'_'+str(acq_mo)+'-'+str(acq_day)+'-'+str(acq_yr)+'.csv',index=False,date_format='%m/%d/%Y %H:%M:%S.%f')
        speed=speed[0:0]
        speed = pd.read_csv('/Users/djfi/python/radar/cherry/summaries/speed_rows_skip1'+'_'+str(acq_mo)+'-'+str(acq_day)+'-'+str(acq_yr)+'.csv',skiprows=rows2skip)
        #print('speed after rows2skip is: ',speed)
        speed['date']=pd.to_datetime(speed['date'], format='%m/%d/%Y %H:%M:%S.%f')
        speed.index = speed['date']
        speed.sort_index(inplace=True)

        cnt_list = speed['vehicle_cnt'].tolist()
        spd_list = speed['speed'].tolist()
        date_list = speed['date'].tolist()

        spd_delta=[]
        date_delta=[]

# Calculate deltas for speed and date data
        counter = 0    
        for element in spd_list:
            if counter == 0:
                spd_delta.append(0)
                date_delta.append(0)
            else:
                spd_delta.append(spd_list[counter] - spd_list[counter-1])
                del_mseconds=relativedelta.relativedelta(date_list[counter],date_list[counter-1]).microseconds/1000000
                del_seconds= relativedelta.relativedelta(date_list[counter],date_list[counter-1]).seconds
                del_minutes= relativedelta.relativedelta(date_list[counter],date_list[counter-1]).minutes
                del_minutes_secs = del_minutes*60.0
                secs_delt=del_minutes_secs+del_seconds+del_mseconds
                date_delta.append(secs_delt)
            counter = counter + 1

        print(len(spd_delta),len(date_delta))
#print(date_delta)


# Eliminate duplicate speed data
        rows2skip=[]
        rows2skip = [idx for idx, val in enumerate (spd_delta) if abs(val) == 0.0]

        counter = 0
        for element in rows2skip:
            rows2skip[counter] = rows2skip[counter]+1
            counter = counter +1
#    print('rows2skip after spike filtering is: ',rows2skip[counter-1])
        print(rows2skip)
        print('')

#Write out noise-corrected data
        speed.to_csv('/Users/djfi/python/radar/cherry/summaries/speed_rows_skip2'+'_'+str(acq_mo)+'-'+str(acq_day)+'-'+str(acq_yr)+'.csv',index=False,date_format='%m/%d/%Y %H:%M:%S.%f')
        speed=speed[0:0]
        speed = pd.read_csv('/Users/djfi/python/radar/cherry/summaries/speed_rows_skip2'+'_'+str(acq_mo)+'-'+str(acq_day)+'-'+str(acq_yr)+'.csv',skiprows=rows2skip)
        #print('speed after rows2skip is: ',speed)
        speed['date']=pd.to_datetime(speed['date'], format='%m/%d/%Y %H:%M:%S.%f')
        speed.index = speed['date']
        speed.sort_index(inplace=True)

        cnt_list = speed['vehicle_cnt'].tolist()
        spd_list = speed['speed'].tolist()
        date_list = speed['date'].tolist()

        spd_delta=[]
        date_delta=[]

# Calculate deltas for speed and date data
        counter = 0    
        for element in spd_list:
            if counter == 0:
                spd_delta.append(0)
                date_delta.append(0)
            else:
                spd_delta.append(spd_list[counter] - spd_list[counter-1])
                del_mseconds=relativedelta.relativedelta(date_list[counter],date_list[counter-1]).microseconds/1000000
                del_seconds= relativedelta.relativedelta(date_list[counter],date_list[counter-1]).seconds
                del_minutes= relativedelta.relativedelta(date_list[counter],date_list[counter-1]).minutes
                del_minutes_secs = del_minutes*60.0
                secs_delt=del_minutes_secs+del_seconds+del_mseconds
                date_delta.append(secs_delt)
            counter = counter + 1

        print(len(spd_delta),len(date_delta))
#print(date_delta)


# Now eliminate duplicate speed data

# Write out necessary columns to lists
        tdelta_list = date_delta
        f_date_list = []
        f_speed_list = []
        row_cnt_list = []
        counter = 0
        for element in cnt_list:
            cnt_list[counter] = counter + 1
            counter = counter + 1
        speed['vehicle_cnt'] = cnt_list


        counter = 0
        for element in tdelta_list:
            if abs(tdelta_list[counter]) >= 1.3:
                f_date_list.append(date_list[counter])
                f_speed_list.append(spd_list[counter])
                row_cnt_list.append(counter)
        #        print('tdelt, date, spd, counter are : ',tdelta_list[counter],date_list[counter],spd_list[counter],counter)
            counter = counter +1
        max_rows = counter
        row_counter = 0
        tdelt_counter = 0
        for element in row_cnt_list:
#    print('row_cnt_list[element] is: ',row_cnt_list[row_counter])
            if row_counter == 0:
                f_date_list.append(0)
                f_speed_list.append(0)
                row_cnt_list.append(0)
                row_cnt_list[-1]= max_rows
                for row in tdelta_list:
                    max_speed = 0
                    while tdelt_counter < row_cnt_list[row_counter]:
                        if spd_list[tdelt_counter] >= max_speed:
                            max_speed = spd_list[tdelt_counter]
                            print('max_speed is: ',max_speed)
                            holder = tdelt_counter
                        tdelt_counter = tdelt_counter + 1    
                    f_date_list[row_counter] = date_list[holder]
                    f_speed_list[row_counter] = spd_list[holder]

            if row_counter > 0 and row_counter < row_cnt_list[-1]:
                for row in tdelta_list:
                    max_speed = 0
                    while tdelt_counter >= row_cnt_list[row_counter-1] and tdelt_counter < row_cnt_list[row_counter]:
                        if spd_list[tdelt_counter] >= max_speed:
                            max_speed = spd_list[tdelt_counter]
                            print('max_speed is: ',max_speed)
                            holder = tdelt_counter
                        tdelt_counter = tdelt_counter + 1    
                    f_date_list[row_counter] = date_list[holder]
                    f_speed_list[row_counter] = spd_list[holder]            
      
            row_counter = row_counter + 1

        speed = pd.DataFrame(list(zip(f_date_list, f_speed_list)), columns =['date', 'speed'])
        speed['date']=pd.to_datetime(speed['date'], format='%Y/%m/%d %H:%M:%S.%f')
        speed.index = speed['date']
        speed.sort_index(inplace=True)
        speed['speed']=abs(speed['speed']) 
        print(speed)

# Now assign lists to dataframe, write to csv and read back into dataframe skipping rows found above
#speed['speed'] = f_speed_list
#speed['date'] = f_date_list

# Now fix vehicle count
        counter = 0
        vehicle_num = []
        vehicle_cnt = []
        for element in row_cnt_list:
            counter = counter + 1
            vehicle_cnt.append(counter)
            vehicle_num.append(1)
        speed['vehicle_cnt'] = vehicle_cnt
        speed['vehicle_num'] = vehicle_num

#speed=speed.drop('date',1)
        print(speed)
        speed.to_csv('/Users/djfi/python/radar/cherry/summaries/speed_rows_skip3'+'_'+str(acq_mo)+'-'+str(acq_day)+'-'+str(acq_yr)+'.csv',index=False,date_format='%m/%d/%Y %H:%M:%S.%f')

# Inspect speed values above 25,30, & 35 mph
        hispeed1 = speed[speed['speed'] >= 30]
        hispeed1.to_csv('/Users/djfi/python/radar/cherry/summaries/hispeed1'+v_dir+'_'+str(acq_mo)+'-'+str(acq_day)+'-'+str(acq_yr)+'.csv',index=False,date_format='%m/%d/%Y %H:%M:%S.%f')
        hispeed2 = speed[speed['speed'] >= 35]
        hispeed2.to_csv('/Users/djfi/python/radar/cherry/summaries/hispeed2'+v_dir+'_'+str(acq_mo)+'-'+str(acq_day)+'-'+str(acq_yr)+'.csv',index=False,date_format='%m/%d/%Y %H:%M:%S.%f')
        speeders = speed[speed['speed'] > 25.0]
        speeders.to_csv('/Users/djfi/python/radar/cherry/summaries/speeders'+v_dir+'_'+str(acq_mo)+'-'+str(acq_day)+'-'+str(acq_yr)+'.csv',index=False,date_format='%m/%d/%Y %H:%M:%S.%f')
        speeder_txt = len(speeders.index)
        hispeed1_txt = len(hispeed1.index)
        hispeed2_txt = len(hispeed2.index)

# Write out speed
        speed.to_csv('/Users/djfi/python/radar/cherry/summaries/speed_final'+v_dir+'_'+str(acq_mo)+'-'+str(acq_day)+'-'+str(acq_yr)+'.csv', index=True,header=True,date_format='%m/%d/%Y %H:%M:%S.%f')

# Setup for export of charts to pdf
        with PdfPages(r'/Users/djfi/python/radar/cherry/summaries/Charts_'+str(direction_txt)+'_'+str(acq_yr)+'_'+str(acq_mo)+'-'+str(acq_day)+'.pdf') as export_pdf:

# Plot data histogram with fitted normal distribution
            fig001, ax_s = plt.subplots(1, 1,figsize=(12,6))
            ax_s.scatter(spd_delta, date_delta, color='g')
            ax_s.set_ylabel('Date Delta')
            ax_s.set_xlabel('Speed Delta)')
            ax_s.set_title('Speed Delta vs Date Delta For Cherry Ln Near Lommel Ct Speed Data')

# Plot data histogram with fitted normal distribution
            fig01, dx1a = plt.subplots(1, 1,figsize=(16,8))
            daily_count = speed['speed']
            daily_count_s = np.sort(daily_count)
            mlabel = 'Cherry Ln Near Lommel Ct Speed Data ('+str(direction_txt)+') - '+str(acq_mo)+'-'+str(acq_day)+'-'+str(acq_yr)
            n_bins = 100
            dx1a.hist(daily_count_s,n_bins,density=True,cumulative=False,label=mlabel)
            dx1a.set_title('Distribution of Vehicle Speed Data For Cherry Ln Near Lommel Ct ('+str(direction_txt)+') - '+str(acq_mo)+'-'+str(acq_day)+'-'+str(acq_yr))
            dx1a.set_ylabel('Proportion')      
            dx1a.set_xlabel('Observed Speed (mph)')
            fit2 = stats.norm.pdf(daily_count_s,np.mean(daily_count),np.std(daily_count))
            dx1a.plot(daily_count_s,fit2,color="b",label='Normal Fit')
            dx1a.legend(loc='upper center')
            plt.figtext(0.25,0.5, speed['speed'].describe([.25,.50,.75,.85,.90]).to_string())
            plt.figtext(0.65,0.55,'Vehicle speed average and standard deviation are: ')
            plt.figtext(0.75,0.5, speed['speed'].describe().loc[['mean','std']].to_string())
            plt.figtext(0.55,0.65, 'Number of vehicles above posted 25mph limit: '+str(speeder_txt))
            plt.figtext(0.55,0.62, 'Number of vehicles above 30mph: '+str(hispeed1_txt))
            plt.figtext(0.55,0.59, 'Number of vehicles above 35mph: '+str(hispeed2_txt))
            export_pdf.savefig()

# Plot CDF speed data histogram
            fig02, (sx1a) = plt.subplots(1, 1,figsize=(16,8))
            speed_count = speed['speed']
            speed_count_s = np.sort(speed_count)
# Assign descriptive stats
            sigma = speed['speed'].mean()
            mu = sigma = speed['speed'].std()
# Plot data
            n_bins = 100
            n, nbins, patches = sx1a.hist(speed_count_s,n_bins,density=True,histtype='step',cumulative=True,label='Speed (mph)')
            numbins = pd.Series(nbins)
            probil = pd.Series(n)
#print(numbins, probil)
            df = pd.concat([numbins,probil],axis=1,join='inner')
            df.columns = ['numbins', 'prob']
# Calculate speed distribution
            y = scipy.stats.norm.pdf(nbins,mu,sigma).cumsum()
            y /=y[-1]
# Continue plot sequence
#ax.plot(nbins,y, 'k--', linewidth=1.5, label= 'Calculated normal distribution')
            sx1a.hist(speed_count_s,n_bins,density=1,histtype='step',cumulative=-1)
            sx1a.grid(True)
            sx1a.legend(loc='lower right')
            sx1a.set_title('Cumulative Distribution of Vehicle Speed Data - Cherry Ln Near Lommel Ct ('+str(direction_txt)+') - '+str(acq_mo)+'-'+str(acq_day)+'-'+str(acq_yr))
            sx1a.set_xlabel('Observed Speed (mph)')
            sx1a.set_ylabel('CDF')
#sx1a.set_xlim([60,150])
            sx1a.set_ylim([0,1])
            sx1a.legend(loc='upper center')
            export_pdf.savefig()

# Plot of Speed versus time of day and hourly average
            fig03, dx1b = plt.subplots(1, 1,figsize=(16,8))
            dx1b.set_title('Vehicle Speed Data For Cherry Ln Near Lommel Ct ('+str(direction_txt)+') - '+str(acq_mo)+'-'+str(acq_day)+'-'+str(acq_yr))
            dx1b.set_ylabel('Observed Speed (mph)')      
            dx1b=speed['speed'].plot(logy=False,color='red', grid=False,linestyle='--', marker='o')
            avg_hourly_speed = speed.resample('H').mean()
            avg_hourly_speed = avg_hourly_speed.rename(columns={'speed': 'avg_hourly_speed'})
            dx1b=avg_hourly_speed['avg_hourly_speed'].plot(logy=False,color='b', grid=False)
            dx1b.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d\n%H:%M:%S'))
            dx1b.set_xlabel('Date-Time')
            dx1b.legend(loc='upper left')

            export_pdf.savefig()

# Plot of Vehicle count versus time of day
            fig04, dx1c = plt.subplots(figsize=(16,8))
            dx1c.set_title('Vehicle Count Data For Cherry Ln Near Lommel Ct ('+str(direction_txt)+') - '+str(acq_mo)+'-'+str(acq_day)+'-'+str(acq_yr))
            dx1c.set_ylabel('Cumulative Vehicle Count')
#     print(speed)
            dx1c=speed['vehicle_cnt'].plot(logy=False,color='red', grid=False,label="Cumulative Vehicle Count")
#avg_hourly_count['avg_hourly_vehicle_count']=speed['vehicle_cnt'].resample('H').sum()
            speed_m=speed.resample('H').sum().ffill()
#    print(speed_m)

            print('verbose info follows: \n')
            print(speed_m.info(verbose=True))
            dx1ct = dx1c.twinx() 
            #dx1ct=speed_m.plot['vehicle_cnt'](logy=False,color='blue', grid=False)
            dx1ct.plot(speed_m.index,speed_m['vehicle_num'],color='blue',label="Hourly Vehicle Count")
            dx1ct.scatter(speed_m.index,speed_m['vehicle_num'])
            dx1ct.set_ylabel('Hourly Vehicle Count')
            dx1ct.legend(loc='center left')
            xmin,xmax = dx1c.get_xlim()
            print('x-axis lims are: ',xmin,xmax)
            dx1ct.set_xlim([xmin,xmax])
            dx1c.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d\n%H:%M:%S'))
            dx1ct.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d\n%H:%M:%S'))
            dx1c.set_xlabel('Date-Time')
            dx1c.legend(loc='upper left')
            dx1ct.legend(loc='center left')
            plt.figtext(0.7,0.80,'Hourly Vehicle Count Averages are: ')
            plt.figtext(0.75,0.25, speed_m['vehicle_num'].to_string()) 

    
            export_pdf.savefig()

# Write percentile data to file
        speed['speed'].describe([.25,.50,.75,.85,.90]).to_csv('/Users/djfi/python/radar/cherry/summaries/dsc_stats'+'_'+v_dir+'_'+str(acq_mo)+'-'+str(acq_day)+'-'+str(acq_yr)+'.csv', index=True,header=True)
        with open('/Users/djfi/python/radar/cherry/summaries/dsc_stats'+'_'+v_dir+'_'+str(acq_mo)+'-'+str(acq_day)+'-'+str(acq_yr)+'.csv', 'a') as f:
            speed_m['vehicle_num'].to_csv(f, header=False)
    


