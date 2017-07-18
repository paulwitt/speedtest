from dateutil.rrule import rrule, MINUTELY
import calendar
import datetime
import bisect
import matplotlib
import matplotlib.pyplot as plt
import json
import os
import pyspeedtest
import sys
import numpy as np
from collections import OrderedDict

## Get the current 15 minute interval and date info. We need
## this for storing in the json
##
times = list(rrule(MINUTELY,interval=15,dtstart=datetime.date.today(),count=96))
rounded_time = times[bisect.bisect(times,datetime.datetime.now())]

day_of_week = calendar.day_abbr[datetime.datetime.today().weekday()]
this_hour = rounded_time.hour
this_fifteen = rounded_time.minute
this_interval = day_of_week + "-" + str(this_hour) + ":" + str(this_fifteen)

## Load the json file if it exists. Create an empty structure
## if it doesn't.
##
folder_name = "C:/DevGitHub/speedtest"
data_file = os.path.join(folder_name, "data/weekly.json")

if os.path.isfile(data_file):
    with open (data_file, "r") as text_file:
        data_file_string = text_file.read()
        data = json.loads(data_file_string, object_pairs_hook=OrderedDict)
else:
    data = {}

## At the very least we now have an empty data file. Time to
## test our speed and store it.
st = pyspeedtest.SpeedTest(host='atl.speedtest.sbcglobal.net', http_debug=0, runs=5)
ping = st.ping()
download = st.download()
upload = st.upload()

try:
    test_interval = data[this_interval]
except:
    data[this_interval] = {}

data[this_interval]['ping'] = ping
data[this_interval]['download'] = download
data[this_interval]['upload'] = upload

## Write out the data to file.
##
data_output = json.dumps(data, indent=4, sort_keys=True)
print "Writing out data file"
with open(data_file, "w") as text_file:
    text_file.write(data_output)

## Calculate averages for each value.
##
divide_by = len(data)
total_ping = 0
total_download = 0
total_upload = 0
for data_interval in data:
    total_ping += data[data_interval]['ping']
    total_download += data[data_interval]['download']
    total_upload += data[data_interval]['upload']

average_ping = total_ping / divide_by
average_download = (total_download / divide_by) / (1024 * 1024)
average_upload = (total_upload / divide_by) / (1024 * 1024)
    
avg_download_msg = "Average download: %.2f MB/s" % (average_download)
avg_upload_msg = "Average upload: %.2f MB/s" % (average_upload)

## Let's try to graph this.
##
labels = []
downloads = []
uploads = []
point_counter = 0
points = []
for data_interval in data:
    if day_of_week in data_interval:
        if ':00' in data_interval:
            labels.append(data_interval)
        else:
            labels.append('')
        downloads.append(data[data_interval]['download'] / (1024 * 1024))
        uploads.append(data[data_interval]['upload'] / (1024 * 1024))
        points.append(point_counter)
        point_counter += 1

plot_count = len(labels)
ind = np.arange(plot_count)

ax0 = plt.subplot(2, 1, 1)
plt.ylabel('Download (MB/s)', fontdict={'fontsize':'8'})
plt.xticks(ind, [])
plt.yticks(fontsize=6)
ax0.spines['top'].set_visible(False)
ax0.spines['right'].set_visible(False)
ax0.yaxis.grid(True)
ax0.set_xmargin(0)
plt.plot(points, downloads)
plt.title(avg_download_msg, loc='left', fontdict={'fontsize':'10'})
plt.subplots_adjust(left=0.1, right=1.9, top=0.9, bottom=0.1)

ax1 = plt.subplot(2, 1, 2)
plt.ylabel('Upload (MB/s)', fontdict={'fontsize':'8'})
plt.xticks(rotation=70, horizontalalignment='right', fontsize=6)
plt.yticks(fontsize=6)
plt.xticks(ind, labels)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.yaxis.grid(True)
ax1.set_xmargin(0)
plt.plot(points, uploads)
plt.title(avg_upload_msg, loc='left', fontdict={'fontsize':'10'})
plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

plt.tight_layout()

plt.show()
