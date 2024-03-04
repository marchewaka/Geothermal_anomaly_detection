import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import mapping
import geopandas as gpd
import earthpy as et
import earthpy.spatial as es
import rasterio
import os
import sys
import fiona
from glob import glob
import re
### export GDAL_DATA=/usr/share/gdal

path = '/data/geohot/ECOSTRESS_data/Correct/Cleanup_version/' ### To-be-cropped-data location
save_path = '/data/geohot/ECOSTRESS_data/Correct/Cleanup_version/Crop/' ### Save location

shapefile_name = '/mnt/hgfs/PostDoc/Olkaria_groud_information/Field_research_bounderies.shp' ### Polygon used for cropping

return_Kelvin = True ### Save data as floats with unit as Kelvin, or keep them in DN (original data format)
dst_crs = 'EPSG:4326' ### Destination EPSG code
cropped_name_suffix = '_field_work_area.tif' ### This will be added at the end of the file name after cropping
input_file_suffix = 'first_scan_corr.tif' ### This is the ending of the files that will be cropped


os.chdir(path)
lste_list = glob('*' + input_file_suffix)
lste_list_to_do = []

os.chdir(save_path)
already_georeferenced_file_list = glob('*' + input_file_suffix[:-4] + cropped_name_suffix)
already_georeferenced_file_names = []

for a in range(len(already_georeferenced_file_list)):
    already_georeferenced_file_names = np.append(already_georeferenced_file_names, already_georeferenced_file_list[a][:-9])

for l in range(len(lste_list)):
    lste_name = lste_list[l][:-4]
    
    if (lste_name in already_georeferenced_file_names) == False:
        lste_list_to_do = np.append(lste_list_to_do, lste_list[l])

os.chdir(path)

for lste_file in lste_list_to_do:
    ### names for image file and geo file
    
    name_pattern = r'^ECOSTRESS_L2_LSTE_(?P<orbit>[0-9]{5})_(?P<scene_id>[0-9]{3})_(?P<acq_timestamp>[0-9]{8}T[0-9]{6})*.'
    match = re.match(name_pattern, lste_file)
    acq_timestamp = match.group('acq_timestamp')
    orig_x_coord_file = glob('ECOSTRESS_*' + acq_timestamp + '*px_coord_x*.tif' )[0]
    orig_y_coord_file = glob('ECOSTRESS_*' + acq_timestamp + '*px_coord_y*.tif' )[0]

    with fiona.open(shapefile_name, 'r') as shapefile:
        extent = [feature['geometry'] for feature in shapefile]
    
    dst_name = lste_file[:-4] + cropped_name_suffix
    dst_name_orig_px_coord_x = orig_x_coord_file[:-4] + cropped_name_suffix
    dst_name_orig_px_coord_y = orig_y_coord_file[:-4] + cropped_name_suffix
    # read imagery file
    with rasterio.open(lste_file) as src:
        out_image, out_transform = rasterio.mask.mask(src, extent, crop=True)
        out_meta = src.meta

    if return_Kelvin == True:
        if np.mean(out_image) > 500:
            out_image = out_image * 0.02

    with rasterio.open(orig_x_coord_file) as src:
        out_image_orig_x_coord, out_transform = rasterio.mask.mask(src, extent, crop=True)
        out_meta_orig_x_coord = src.meta

    with rasterio.open(orig_y_coord_file) as src:
        out_image_orig_y_coord, out_transform = rasterio.mask.mask(src, extent, crop=True)
        out_meta_orig_y_coord = src.meta


    # Save clipped imagery
    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})

    with rasterio.open(save_path + dst_name, "w", **out_meta) as dest:
        dest.write(out_image)

    with rasterio.open(save_path + dst_name_orig_px_coord_x, "w", **out_meta) as dest:
        dest.write(out_image_orig_x_coord)
    with rasterio.open(save_path + dst_name_orig_px_coord_y, "w", **out_meta) as dest:
        dest.write(out_image_orig_y_coord)
    print('Saved file ', dst_name)