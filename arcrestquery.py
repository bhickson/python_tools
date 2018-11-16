# Queries a ArcGIS Feature Service URL and returns features in block of value 'rq'. Get around for feature request limit.

import urllib.request, os, json

rq = 200  # request feature limit, varies by layer

# Variables
server_url = "https://mapservices.nps.gov/arcgis/rest/services"
service = "/WildlandFire/WildlandFire/MapServer"
layer = "/4/"
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
           "&f=pjson"


myRequest = server_url + service + layer + params
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

    query = server_url + service + layer + params
    query = query.replace("objectIds=", "objectIds=" + ids).replace("&returnIdsOnly=true", "&returnIdsOnly=false")

    feature_response = urllib.request.urlopen(query)
    feature_json = json.load(feature_response)
    if "features_json" in globals():
        features = feature_json["features"]
        for feat in features:
            features_json["features"].append(feat)
        features_json = feature_json

with open("jsonOutput.json", "w") as jsonfile:
    jsonString = json.dumps(features_json, indent=4, sort_keys=False)
    jsonfile.write(jsonString)
