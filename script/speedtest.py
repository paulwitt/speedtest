from collections import OrderedDict
from dateutil.rrule import rrule, MINUTELY
import bisect
import calendar
import datetime
import json
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import os
import pyspeedtest
import sys

## We need this mess to handle dates in json
##
def date_handler(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

def datetime_parser(dct):
    for k, v in dct.items():
        if isinstance(v, basestring):
            try:
                dct[k] = datetime.datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
            except:
                pass
    return dct

## Folder setup
##
#folder_name = "D:/Development/speedtest"
folder_name = "C:/DevGitHub/speedtest"
data_file = os.path.join(folder_name, "data/weekly.json")
image_file = os.path.join(folder_name, "images/image.png")

## Get the current 15 minute interval and date info. We need
## this for storing in the json
##
times = list(rrule(MINUTELY,interval=15,dtstart=datetime.date.today(),count=96))
this_interval = times[bisect.bisect(times,datetime.datetime.now())]
date_cutoff = this_interval - datetime.timedelta(days=7)
twenty_four_ago = this_interval - datetime.timedelta(days=1)

## Load the json file if it exists. Create an empty structure
## if it doesn't.
##
if os.path.isfile(data_file):
    with open (data_file, "r") as text_file:
        data_file_string = text_file.read()
        data = json.loads(data_file_string, object_hook=datetime_parser)
else:
    data = []

## At the very least we now have an empty data file. Time to
## test our speed and store it.
st = pyspeedtest.SpeedTest(host='atl.speedtest.sbcglobal.net', http_debug=0, runs=5)
download = st.download()
upload = st.upload()

## Loop through the existing data and do two things:
## a) If this interval has already been created update the values
## b) Delete any rows that are more than 7 days old
##
found = False
new_data = []
for row in data:
    if this_interval == row['date']:
        found = True
        row['download'] = download
        row['upload'] = upload
        new_data.append(row)
    elif row['date'] <= date_cutoff:
        print "deleting row"
    else:
        new_data.append(row)

if found == False:
    this_obj = {}
    this_obj['date'] = this_interval
    this_obj['download'] = download
    this_obj['upload'] = upload

    new_data.append(this_obj)

## Sort this thing in date order.  We'll need this later when
## we're trying to graph it.
##
new_data.sort(key=lambda x: x['date'])

## Write out the data to file.
##
data_output = json.dumps(new_data, default=date_handler, indent=4, sort_keys=True)
print "Writing out data file"
with open(data_file, "w") as text_file:
    text_file.write(data_output)

## Calculate averages for each value.
##
divide_by = len(new_data)
total_download = 0
total_upload = 0
for row in new_data:
    total_download += row['download']
    total_upload += row['upload']

average_download = (total_download / divide_by) / (1024 * 1024)
average_upload = (total_upload / divide_by) / (1024 * 1024)
    
avg_download_msg = "Average download (last 7 days): %.2f MB/s" % (average_download)
avg_upload_msg = "Average upload (last 7 days): %.2f MB/s" % (average_upload)

print avg_download_msg
print avg_upload_msg

## Let's try to graph this.
##
labels = []
downloads = []
uploads = []
point_counter = 0
points = []
for row in new_data:
    if row['date'] >= twenty_four_ago:
        if row['date'].minute == 0:
            labels.append(row['date'])
        else:
            labels.append('')
        downloads.append(row['download'] / (1024 * 1024))
        uploads.append(row['upload'] / (1024 * 1024))
        points.append(point_counter)
        point_counter += 1

plot_count = len(labels)
ind = np.arange(plot_count)

ax0 = plt.subplot(2, 1, 1)
plt.ylabel('Download (MB/s)\n(last 24 hours)', fontdict={'fontsize':'8'})
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
plt.ylabel('Upload (MB/s)\n(last 24 hours)', fontdict={'fontsize':'8'})
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

plt.savefig(image_file)

sys.exit(0)

