# -*- coding: utf-8 -*-
"""
Created on Sat Nov 22 12:26:58 2025

@author: simmers
"""

## this file takes the co-ordinate points reported by spraying vans
# it then converts these into lines, but filters out points where data is
# missing/anomalous (these are customisable, time_threshold and dist_threshold)
# note: dist_threshold is in degrees, 0.005 deg = about 500m

# ----- OUTPUTS --------
# 1. tracks of where vans sprayed (gpkg)

# importing relevant packages
import geopandas as gpd
import pandas as pd
import fiona
from shapely.geometry import Point, LineString, shape
from io import StringIO
from pathlib import Path
import os
import numpy as np

# ============= IMPORT FILES & DEFINE DIRECTORY =============
# define folder variable & iterate through it
spray_dir = Path("../../Samos 2022-2024-20251120T120022Z-1-001/Samos 2022-2024/Spraying data")


# make a list from the files in this folder
list_xlsx = [
    file for file in os.listdir(spray_dir)]
print(list_xlsx)

# ============= DEFINE FUNCTION =============
# iterate through all the excel files
def transform_function(year):
    
    #for year in list_xlsx:
    print("running for", year)
    
    # initialise database from data
    spray_pts = pd.read_excel(year,
                       usecols=["latitude", "longitude", "date", "time", "vehicle_id"])
    
    # convert date and time to recognised formats
    spray_pts['time'] = pd.to_datetime(spray_pts['time'], format='%H:%M:%S')
    spray_pts['date'] = pd.to_datetime(spray_pts['date'], dayfirst=True)
    
    # define acceptable thresholds to filter out straight line 'flying'
    time_threshold = 1000000
    dist_threshold = 1000
    
    # sort by date, time & vehicle ID
    spray_pts = spray_pts.sort_values(
        ['date', 'vehicle_id', 'time']
        ).reset_index(drop=True)
    
    # group by key attributes to make into lines later
    grouped4sort = spray_pts.groupby(['date', 'vehicle_id']#, group_keys=False)
    ) 
    
    # calculate the time gap between different co-ordinate readings
    spray_pts['time_length'] = grouped4sort['time'].diff().dt.total_seconds()#.fillna(0)
    
    # calculate the distance between different co-ordinate readings, lon & lat
    spray_pts['lon_gap'] = grouped4sort['longitude'].diff()#.fillna(0)
    spray_pts['lat_gap'] = grouped4sort['latitude'].diff()#.fillna(0)
    
    # make breaks wherever the gap b/w two points is unrealistically high
    spray_pts['break'] = (
        (spray_pts['time_length'] > time_threshold) |
        (spray_pts['lon_gap'].abs() > dist_threshold) |
        (spray_pts['lat_gap'].abs() > dist_threshold)
        ).fillna(False)
    
    # assign this break value to segment number
    spray_pts['segment_no'] = (
        spray_pts
        .groupby(['date', 'vehicle_id'])['break']
        .cumsum()
        )
    
    # define the length of a segment
    segment_length = (
        spray_pts
        .groupby(['date', 'vehicle_id', 'segment_no'])
        .size()
        .reset_index(name='n_points')
        )
    
    # reject segments made up of only a single point
    accept_segments = segment_length[segment_length['n_points'] > 1]
    
    # merge back acceptable segments into the spray_pts dataframe
    spray_pts_fixed = spray_pts.merge(
        accept_segments[['date', 'vehicle_id', 'segment_no']],
        on=['date', 'vehicle_id', 'segment_no'],
        how='inner'
        )
    
    # make line strings from the co-ordinate data
    spray_pts_fixed = spray_pts_fixed.groupby(['date', 'vehicle_id', 'segment_no'],
              group_keys=False
              ).apply(lambda group: LineString(group.sort_values
              ('time')[['longitude', 'latitude']].to_numpy()))
                  
    
    # make new geoseries based on the above grouping
    geometries = gpd.GeoSeries(spray_pts_fixed, name='geometry')
    
    # make a geodataframe from the above (is that necessary? idk)
    paths = gpd.GeoDataFrame(
        geometries.reset_index(),
        geometry='geometry',
        crs='EPSG:4326')

    #spray_lines = gpd.GeoDataFrame(spray_lines, geometry='geometry', crs="EPSG:4326")
    print("still going ! :)")
    print(paths.columns)
    return paths

# ============= COMPILE THE DIFFERENT DATASETS =============

# compile the three years together    
compiled = [transform_function(os.path.join(spray_dir, year)) 
                               for year in list_xlsx
                               ]

# merge the three datasets into one dateframe
merged = gpd.GeoDataFrame(pd.concat(compiled, ignore_index=True))

# convert these to output files
merged.to_excel('./ttttttspray_tracks.xlsx')
merged.to_file('./testtesttetst.gpkg', layer='paths', driver='GPKG')
