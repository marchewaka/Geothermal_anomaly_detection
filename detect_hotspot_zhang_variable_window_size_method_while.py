import numpy as np
import os
import matplotlib.pyplot as plt
from glob import glob
import numpy.ma as ma
import rasterio
import rasterio.mask
from time import time
import datetime
from scipy import signal
import sys
from datetime import datetime
import re
from pytz import timezone
import copy

# path = '/mnt/hgfs/PostDoc/ECOSTRESS_data/NZ/'
# path = '/mnt/hgfs/PostDoc/ASTER/'
# path = '/mnt/hgfs/PostDoc/ECOSTRESS_data/Raw_download/Field_work_area/'
# path = '/mnt/hgfs/PostDoc/ECOSTRESS_data/Raw_download/Automated_geocorr/Crop/'
path = '/data/geohot/ECOSTRESS_data/Correct/Cleanup_version/Crop/'

# save_path = '/mnt/hgfs/PostDoc/ECOSTRESS_data/Raw_download/Detections/'
# save_path = '/mnt/hgfs/PostDoc/ECOSTRESS_data/Raw_download/Automated_geocorr/Detections/'
save_path = '/data/geohot/ECOSTRESS_data/Correct/Cleanup_version/Detections/'
os.chdir(path)
os.chdir(save_path)

img_list = glob('*masked.tif')
threshold = 2
threshold_window_correction = 1

for dt in img_list:

    img_name = dt
    outliers_name = dt[:-4] + '_detections_threshold' + str(threshold*10) + 'mK_zhang_adjustable_window.tif'
    
    name_pattern = r'^ECOSTRESS_L2_LSTE_(?P<orbit>[0-9]{5})_(?P<scene_id>[0-9]{3})_(?P<acq_timestamp>[0-9]{8}T[0-9]{6})*.'
    match = re.match(name_pattern, img_name)
    acq_timestamp_str = match.group('acq_timestamp')

    acq_timestamp = datetime.strptime(acq_timestamp_str, '%Y%m%dT%H%M%S')
    acq_timestamp_utc = acq_timestamp.replace(tzinfo = timezone('UTC'))
    acq_timestamp_tz = acq_timestamp_utc.astimezone(timezone('Africa/Nairobi'))

    acq_time = acq_timestamp_tz.hour + (acq_timestamp_tz.minute/60)

    img_raster = rasterio.open(img_name)
    out_meta = img_raster.meta
    img = img_raster.read(1)

    img_T_masked = ma.masked_equal(img,0)
    
    img_median = np.nanmedian(img_T_masked)

    window_x = 12
    window_y = 12
    

    outliers = np.zeros(img_T_masked.shape, dtype = np.int32)
    start = time()


    for i in range(img_T_masked.shape[0]-window_y):
        for j in range(img_T_masked.shape[1]-window_x):
            
            window = img_T_masked[i:i+window_y,j:j+window_x]
            masked_px = ma.count_masked(window)
            # if masked_px/(window_x*window_y) > 0.3:
                # continue
            # else:
            median_T_window = np.nanmedian(window)
            additional_window = 1
            while (median_T_window - img_median) > threshold_window_correction:
                y1 = i - window_y - additional_window
                y2 = i + window_y + additional_window
                
                x1 = j - window_x - additional_window
                x2 = j + window_x + additional_window
                
                if y1 < 0:
                    y1 = 0
                if x1 < 0:
                    x1 = 0
                if y2 > img_T_masked.shape[0]:
                    y2 = img_T_masked.shape[0]
                if x2 > img_T_masked.shape[1]:
                    x2 = img_T_masked.shape[1]

                window = img_T_masked[y1:y2,x1:x2]
                
                median_T_window = np.nanmedian(window)
                additional_window += 1
                
            if (img_T_masked[i,j]-(median_T_window+threshold)) > threshold:
                outliers[i,j] += 1

    outliers_reshape = np.int32(np.reshape(outliers, [1, outliers.shape[0], outliers.shape[1]]))
    
    out_meta['dtype'] = 'int32'
    with rasterio.open(save_path + outliers_name, "w", **out_meta) as dest:
        dest.write(outliers_reshape)
