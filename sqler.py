import os
import geopandas as gpd
import pandas as pd
from sqlalchemy import *
from geoalchemy2 import Geometry, WKTElement
from getpass import getpass

pw = getpass()
def sendIndexToPostGIS(folder):
	year = folder[-4:]
	print("Reading in shapefiles...")
	zero_dir = os.path.join(folder, "0")
	index_df = gpd.read_file(os.path.join(zero_dir,"0.shp"))
	fishnet_df = gpd.read_file("/toucana/staging/DOQQ_Fishnet_AZ.shp")
	index_df.to_crs({'init': 'epsg:3857'}, inplace=True)
	fishnet_df.to_crs({'init': 'epsg:3857'}, inplace=True)

	#  Create attributes conforming to OpenIndexMaps schema
	#  https://openindexmaps.org/
	index_df["available"] = "True"

	index_df["recordIdentifier"] = index_df.apply(lambda row: row["location"].split(".")[0], axis=1)

	url_base = "http://sequoia.library.arizona.edu/geospatial/public/tiledDatasets/Arizona_NAIPImagery/{}/{}?ticket=AZNAIP{}"
	index_df["downloadUrl"] = index_df.apply(lambda row: url_base.format(year,row["location"],year),axis=1)

	website_base = "https://geo.library.arizona.edu/?ogpids=uarizona-arizona-naipimagery-{}"
	index_df["websiteUrl"] = website_base.format(year)

	index_df["label"] = index_df.apply(lambda row: row["location"][2:12], axis=1)
	index_df["note"] = index_df.apply(lambda row: str(int(os.path.getsize(os.path.join(zero_dir, row["location"]))/1024**2))+ " MB", axis=1)

	out_df = gpd.sjoin(fishnet_df,index_df, op="within", how="inner")


	print("writing to postgres...")

	engine = create_engine('postgresql://manager:' + pw + '@geo.library.arizona.edu:5440/UAL_geoData')

	#out_df["geom"] = out_df["geometry"].astype(str)
	out_df['geom'] = out_df['geometry'].apply(lambda x: WKTElement(x.wkt, srid=3857))

	out_df.drop("geometry", 1 , inplace=True)
	out_df.drop("Shape_Area", 1, inplace=True)
	out_df.drop("Shape_Leng", 1, inplace=True)
	out_df.drop("index_right", 1, inplace=True)
	#out_df.set_geometry("geom")

	#print("\n COLUMNS \n", out_df.columns)


	out_df.to_sql("arizona_naipimagery_{}".format(year), engine, schema="tile_indices", if_exists='replace', index=True, dtype={"geom": Geometry("POLYGON", srid=3857)})

for dir in os.listdir(os.path.abspath("./")):
        if dir.startswith("Arizona_NAIPImagery_"):
                print("STARTING DIR: {}".format(dir))
                base_dir = os.path.join("./", dir)
                sendIndexToPostGIS(base_dir)






