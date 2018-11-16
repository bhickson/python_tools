import pandas as pd
import geopandas as gpd
import os, shutil
import gdal
import rasterio as rio
import rasterio.features as features
import numpy as np
from shapely.geometry import shape, Point, Polygon
import pyproj
from shapely.ops import transform
from functools import partial

def getFullNAIPPath(naip_file, naipdir):
    for root, dirs, files in os.walk(naipdir):
        for file in files:
            if naip_file in file:
                return os.path.join(root, file)

    return False

	
def getFootprintsDF(directory):
    ras_files = []
    for root,dirs,files in os.walk(base_dir):
        ras_files += [os.path.join(root,f) for f in files if f.endswith(".tif")]

    footprints = []
    count = 0

    out_file = os.path.join(base_dir, "NAIP_Footprints_" + os.path.basename(base_dir) + ".shp")
    if os.path.exists(out_file):
        print("Shapefile index {} found".format(out_file))
        geo_df = gpd.read_file(out_file)
        return geo_df
    else:
        print("Shapefile index not found. Creating at {}".format(out_file))

    for file in ras_files:
        count += 1
        #print(count, file)
        with rio.open(file) as dataset:
            # Read the dataset's valid data mask as a ndarray.
            raster_crs = dataset.crs.to_string()
            epsg_code = raster_crs.split(":")[-1]

            bounds = dataset.bounds
            minx = bounds.left
            maxx = bounds.right
            miny = bounds.bottom
            maxy = bounds.top
            pointList = [Point(minx, maxy), Point(maxx, maxy), Point(maxx, miny), Point(minx,miny)]
            bbox = Polygon([[p.x, p.y] for p in pointList])

            #utm12_geom = rio.warp.transform_geom(dataset.crs, 'EPSG:26912', bbox, precision=6)
            utm12_geom = project(dataset.crs.to_string().split(":")[-1], "26912", bbox)

            feature_props = (file, epsg_code, shape(utm12_geom))
            footprints.append(feature_props)

            #mask = dataset.dataset_mask()
            """
            # Extract feature shapes and values from the array.
            for geom, val in rio.features.shapes(mask, transform=dataset.transform):

                # Transform shapes from the dataset's own coordinate reference system to UTM12
                utm12_geom = rio.warp.transform_geom(dataset.crs, 'EPSG:26912', geom, precision=6)

                #footprints[file] = shape(utm12_geom)
                feature_props = (file, epsg_code, shape(utm12_geom))
                footprints.append(feature_props)
            """
        
    df = pd.DataFrame(footprints, columns=['File', 'EPSG_Code', 'geometry'])

    geo_df = gpd.GeoDataFrame(df,crs={'init': 'EPSG:26912'},geometry="geometry")
    geo_df['area'] =  geo_df.area 
    geo_df.to_file(out_file)#, driver = 'ESRI Shapefile')
    return geo_df

	
def project(in_epsg, out_epsg, in_geom):
    project =  partial(
        pyproj.transform,
        pyproj.Proj(init='epsg:' + in_epsg), # source coordinate system
        pyproj.Proj(init='epsg:' + out_epsg)) # destination coordinate system
 
    return transform(project, in_geom) 


targets = ["3411414_sw"]	
for dir in os.listdir("./"):
	if dir.startswith("original_2015"):
		print("STARTING DIR: {}".format(dir))
		base_dir = os.path.join("./", dir)

		temp_dir = os.path.join(base_dir, "temp")
		if not os.path.exists(temp_dir):
			os.mkdir(temp_dir)
		out_dir = os.path.join(base_dir, "0")
		if not os.path.exists(out_dir):
			os.mkdir(out_dir)

		qquads_df = getFootprintsDF(base_dir)
		#print(qquads_df)
		count = 0
		cleanup = True


		for index, qquad in qquads_df.iterrows():

			epsg_code = qquad["EPSG_Code"]
			fpath = qquad["File"]
			fname = os.path.basename(fpath)
			quad = fname[2:12]
			if quad not in targets:
				continue	
			#quad = fname.split("_")[1][:5]
			#opath = os.path.join(base_dir, quad)
			ofile = os.path.join(out_dir, fname)
			#print("OFILE: ", ofile)
			#print("QQUAD", qquad)

			if epsg_code != '26912' and not os.path.exists(ofile):
				#if not os.path.exists(opath):
				#	os.mkdir(opath)
				count += 1
				print(count, qquad["File"])
				#fname = os.path.basename(fpath)

				print(fpath)
				#internal_buffer_meters = 480
				with rio.open(fpath) as ras:
					res = ras.transform[0]

				# get 'not disjoint' QQUADS
				neighbors = qquads_df[~qquads_df.geometry.disjoint(qquad.geometry)]#.location.tolist()
				#print("NEIGHBORS: ", neighbors)

				utm12_paths= []
				utm11_paths = []
				
				for i, neighbor in neighbors.iterrows():
					if neighbor.EPSG_Code == "26911":
						utm11_paths.append(neighbor["File"])
					elif neighbor.EPSG_Code == "26912":
						utm12_paths.append(neighbor["File"])

				bbox_geom = qquads_df.at[index, "geometry"]
				xmin_utm12, ymin_utm12, xmax_utm12, ymax_utm12 = bbox_geom.bounds    
				xmin_utm11, ymin_utm11, xmax_utm11, ymax_utm11 = project('26912', epsg_code, bbox_geom).buffer(500).bounds       

				#merge neighbors together
				utm11_merge =  os.path.join(temp_dir, fname[:-4] + "_wneighbors.tif")
			
				gdal_merge = """gdal_merge.py -co "GDAL_TIFF_INTERNAL_MASK=NO" -co "ALPHA=NO" -o {} -ul_lr {} {} {} {} {}""".format(utm11_merge, xmin_utm11, ymax_utm11, xmax_utm11, ymin_utm11, " ".join(utm11_paths))
				#if not os.path.exists(utm11_merge):
				os.system(gdal_merge)

				warpfile_name = utm11_merge[:-4] + "_26912.tif"
				gdalwarp = """gdalwarp -nosrcalpha -co "GDAL_TIFF_INTERNAL_MASK=NO" -co "ALPHA=NO" -r bilinear -tap -ot Byte -t_srs "EPSG:26912" -tr {} {} -te {} {} {} {} {} {}""".format(res, res, xmin_utm12, ymin_utm12, xmax_utm12, ymax_utm12, utm11_merge, warpfile_name)
				#if not os.path.exists(warpfile_name):
				os.system(gdalwarp)
				if cleanup: os.remove(utm11_merge)

				if len(utm12_paths) > 0:
					print("UTM12 NEIGHBORS")
					utm12_merge =  os.path.join(temp_dir, fname[:-4] + "_wneighbors_12.tif")
					utm12_paths.insert(0, warpfile_name)  # gdal_merge just adds value from the last in raster passed. Since warpfile name may contain bad values, put it first

					gdal_merge = """gdal_merge.py -co "GDAL_TIFF_INTERNAL_MASK=NO" -co "ALPHA=NO" -o {} -ul_lr {} {} {} {} {}""".format(utm12_merge, xmin_utm12, ymax_utm12, xmax_utm12, ymin_utm12, " ".join(utm12_paths))
					os.system(gdal_merge)
					if cleanup: os.remove(warpfile_name)

					warpfile_name = utm12_merge[:-4] + "_26912_all.tif"
					gdalwarp = """gdalwarp -overwrite -nosrcalpha -co "GDAL_TIFF_INTERNAL_MASK=NO" -co "ALPHA=NO" -r bilinear -tap -ot Byte -t_srs "EPSG:26912" -tr {} {} -te {} {} {} {} {} {}""".format(res, res, xmin_utm12, ymin_utm12, xmax_utm12, ymax_utm12, utm12_merge, warpfile_name)
					os.system(gdalwarp)
					if cleanup: os.remove(utm12_merge)
					
				print("\tFinal out file: {}".format(ofile))
				# gdal_merge.py automatically treats band 4 as an alpha band and uses it to mask the other bands (1-3). can't remove in gdalwarp, so remove here
				gdal_translate = """gdal_translate -co "TILED=YES" -co "BLOCKXSIZE=512" -co "BLOCKYSIZE=512" -co "ALPHA=NO" {} {}""".format(warpfile_name, ofile)
				os.system(gdal_translate)

				if cleanup: os.remove(warpfile_name)

			#elif epsg_code == "26912" and not os.path.exists(ofile):
			#	fname = os.path.basename(fpath)
			#	ofile = os.path.join(out_dir, fname)
			#	gdal_translate = """gdal_translate -co "TILED=YES" -co "BLOCKXSIZE=512" -co "BLOCKYSIZE=512" -co "ALPHA=NO" {} {}""".format(fpath, ofile)
			#	os.system(gdal_translate)

		if cleanup:
			os.rmdir(temp_dir)
