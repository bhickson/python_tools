import pandas as pd
import rasterio as rio
import geopandas as gpd
from glob import glob
import os
import rasterio.features as features
import numpy as np
from shapely.geometry import shape, Point, Polygon
import pyproj
from shapely.ops import transform
from functools import partial

def getFootprintsDF(directory, overwrite=False):
    ras_files = []
    for root,dirs,files in os.walk(directory):
        ras_files += [os.path.join(root,f) for f in files if f.endswith(".tif")]

    footprints = []
    count = 0

    out_file = os.path.join(directory, os.path.basename(directory) + ".shp")
    if os.path.exists(out_file) and not overwrite:
        print("Shapefile index {} found".format(out_file))
        geo_df = gpd.read_file(out_file)
        return geo_df
    else:
        print("Shapefile index not found. Creating at {}".format(out_file))

    for file in ras_files:
        count += 1
        print(count, file)
        with rio.open(file) as dataset:
            # Read the dataset's valid data mask as a ndarray.
            """raster_crs = dataset.crs.to_string()
            epsg_code = raster_crs.split(":")[-1]

            mask = dataset.dataset_mask()
            # Extract feature shapes and values from the array.
            for geom, val in rio.features.shapes(mask, transform=dataset.transform):

                # Transform shapes from the dataset's own coordinate reference system to UTM12
                utm12_geom = rio.warp.transform_geom(dataset.crs, 'EPSG:26912', geom, precision=6)

                #footprints[file] = shape(utm12_geom)
                feature_props = (file, epsg_code, shape(utm12_geom))
                footprints.append(feature_props)
            #print("\n{}\n\tBBOX: {}\n\tBOUNDS: {}".format(file, utm12_geom, dataset.bounds))"""
            bounds = dataset.bounds
            minx = bounds.left
            maxx = bounds.right
            miny = bounds.bottom
            maxy = bounds.top
            pointList = [Point(minx, maxy), Point(maxx, maxy), Point(maxx, miny), Point(minx,miny)]
            bbox = Polygon([[p.x, p.y] for p in pointList])
            #            print(bbox.wkt)
            #print("\n{}\n\tBBOX: {}\n\tBOUNDS: {}".format(file, shape(utm12_geom).wkt, bbox.wkt))
            footprints.append((file.split(directory + "/")[-1], bbox))
	


    df = pd.DataFrame(footprints, columns=['location', 'geometry'])

    geo_df = gpd.GeoDataFrame(df,crs={'init': 'EPSG:26912'},geometry="geometry")
    geo_df.to_file(out_file)#, driver = 'ESRI Shapefile')
    return geo_df

in_dir = "./Arizona_NAIPImagery_2005"
for dir in os.listdir(in_dir):
    dir_path = os.path.join(in_dir, dir)
    if os.path.isdir(dir_path):
        print("Starting Directory: {}".format(dir_path))
        getFootprintsDF(dir_path, overwrite=True)
