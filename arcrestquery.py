# Queries a ArcGIS Feature Service URL and returns features in block of value 'rq'. Get around for feature request limit.

import urllib.request
import os
import json
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("-s", "--service", help="specify arcgis service rest endpoint. e.g. https://myserver.com/arcgis/rest/services/folder/layers/0")
parser.add_argument("-rl", "--request_limit", help="specify number of features to request at one time. Defaults to 200", default = 200)

args = parser.parse_args()
rq = args.request_limit

# Variables
params = "query?where=1%3D1" \
           "&text=" \
           "&objectIds=" \
           "&time=" \
           "&geometry=" \
           "&geometryType=esriGeometryEnvelope" \
           "&inSR=&spatialRel=esriSpatialRelIntersects" \
           "&relationParam=" \
           "&outFields=*" \
           "&returnGeometry=true" \
           "&maxAllowableOffset=" \
           "&geometryPrecision=" \
           "&outSR=" \
           "&returnIdsOnly=true" \
           "&returnCountOnly=false" \
           "&orderByFields=" \
           "&groupByFieldsForStatistics=" \
           "&outStatistics=" \
           "&returnZ=false" \
           "&returnM=false" \
           "&gdbVersion=" \
           "&returnDistinctValues=false" \
           "&f=geojson"

myRequest = args.service + "/" + params
response = urllib.request.urlopen(myRequest)
string = response.read().decode('utf-8')
json_obj = json.loads(string)

# Get object ids
for k in json_obj.keys():
    if k == "objectIds":
        obj_ids = json_obj[k]

if "obj_ids" not in globals():
    print("UNABLE TO FIND OBJECT IDS")
    exit()


max = max(obj_ids)

last_len = len(obj_ids) % rq

rounded = len(obj_ids) - last_len + rq

end = rq
id_lists = []
for start in range(0,rounded,rq):
    end = start + rq
    if end > len(obj_ids):
        end = len(obj_ids)

    obj_id_list = obj_ids[start:end]

    obj_id_list = list(map(str, obj_id_list))
    id_lists.append(obj_id_list)

lcount = 0
for id_list in id_lists:
    lcount += 1
    print("Starting list", lcount, " of ", len(id_lists))
    ids = ",".join(id_list)

    query = myRequest
    query = query.replace("objectIds=", "objectIds=" + ids).replace("&returnIdsOnly=true", "&returnIdsOnly=false")

    feature_subset_response = urllib.request.urlopen(query)
    feature_json = json.load(feature_subset_response)
    if "all_features" in globals():
        subset_features = feature_json["features"]
        for feat in subset_features:
            all_features["features"].append(feat)
    else:
        all_features = feature_json


out_file = "jsonOutput.json"
print(s"Writing to file {out_file}")
with open(out_file, "w") as jsonfile:
    jsonString = json.dumps(all_features, indent=4, sort_keys=False)
    jsonfile.write(jsonString)
