import numpy as np
import rasterio
import os 
from glob import glob
import matplotlib.pyplot as plt
import sys
import h5py
from fun_read_qc import *
import re
from datetime import datetime
import copy
import matplotlib.animation as animation
from matplotlib.animation import FFMpegWriter



path = '/data/geohot/ECOSTRESS_data/Correct/Cleanup_version/Crop/' ### Where is ECOSTRESS imagery stored
raw_data_path = '/data/geohot/ECOSTRESS_data/Raw_data/Olkaria/' ### Where is ECOSTRESS raw data stored
save_path = '/data/geohot/ECOSTRESS_data/Correct/Cleanup_version/Crop/' ### Where to saved masked data
os.chdir(path)

input_imagery_suffix = 'scan_corr_field_work_area.tif'
output_imagery_suffix = '_masked.tif'

mask_level = 0 ### Pixels with quality lower than this value will be masked
### Value explanation: 0 pixel produced, best quality, 1 pixel produced nominal quality, 2 pixel produced but cloud detected, 3 pixel not produced 

lste_list = glob('*' + input_imagery_suffix)


for i in range(len(lste_list)):
    lste_name = lste_list[i]

    name_pattern = r'^ECOSTRESS_L2_LSTE_(?P<orbit>[0-9]{5})_(?P<scene_id>[0-9]{3})_(?P<acq_timestamp>[0-9]{8}T[0-9]{6})*.'
    match = re.match(name_pattern, lste_name)
    acq_timestamp = match.group('acq_timestamp')
    
    os.chdir(path)
    orig_x_coord_file = glob('ECOSTRESS_*' + acq_timestamp + '*px_coord_x*' )[0]
    orig_y_coord_file = glob('ECOSTRESS_*' + acq_timestamp + '*px_coord_y*' )[0]

    px_x_coords = rasterio.open(orig_x_coord_file).read(1).astype(np.int)
    px_y_coords = rasterio.open(orig_y_coord_file).read(1).astype(np.int)
    
    os.chdir(raw_data_path)
    raw_list = glob('ECOSTRESS_L2_LSTE_*' + acq_timestamp + '*.h5')

    if len(raw_list) == 1:
        h5_file = raw_list[0]
    else:
        print('No matching file found')
        print(acq_timestamp)
        continue
    f = h5py.File(h5_file, 'r')
    qc = f.get('SDS/QC')
    orig_img_qc = np.array(qc)
    
    qc_cropped = np.zeros(px_x_coords.shape)
    
    for y in range(qc_cropped.shape[0]):
        for x in range(qc_cropped.shape[1]):
            qc_cropped[y,x] = orig_img_qc[px_y_coords[y,x],px_x_coords[y,x]]
    
    qc_interpretation = read_qc(qc_cropped.astype(np.int))
    
    lste_accuracy = qc_interpretation[3]
    mandatory_flag =qc_interpretation[0]

    dst_name = lste_name[:-4] + output_imagery_suffix
    os.chdir(path)
    lste_file = rasterio.open(lste_name)
    lste_meta = lste_file.meta
    lste_img = lste_file.read(1)

    lste_img_masked = copy.deepcopy(lste_img)
    lste_img_masked[mandatory_flag > mask_level] = 0
    
    
    lste_img_masked_reshape = np.reshape(lste_img_masked, [1, lste_img_masked.shape[0], lste_img_masked.shape[1]])
    
    with rasterio.open(save_path + dst_name, "w", **lste_meta) as dest:
        dest.write(lste_img_masked_reshape)
