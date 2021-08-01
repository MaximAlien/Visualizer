import requests
import json
import os
import glob
import ujson
# from exif import Image
import csv
import math
import time

def get_activities(amount_per_page, access_token):
    url = "https://www.strava.com/api/v3/activities?access_token={}&per_page={}&page=1".format(access_token, amount_per_page)
    print(url)
    response = requests.get(url)

    return response.json()

def get_activity(id, access_token):
    url = "https://www.strava.com/api/v3/activities/{}?include_all_efforts=true&access_token={}".format(id, access_token)
    response = requests.get(url)

    return response.json()

def load_activities():
    access_token = ""

    with open('temp.json', 'w') as activities_file:
        json.dump(get_activities(1, access_token), activities_file)

    f = open('temp.json')

    data = json.load(f)
    
    for element in data:
        id = element["id"]
        print(id)

        response = get_activity(id, access_token)
        with open("activities/new/{}.json".format(id), "w") as json_file:
            json.dump(response, json_file)
    
    f.close()

# load_activities()

def create_file_activities():
    # x - create file
    # w - overwrite file
    # a - append to file
    activities_file = open("activities.js", "w")

    activities_file.write("var polylines = [")
    folder_path = 'activities'
    for json_file in glob.glob(os.path.join(folder_path, '*.json')):
        with open(json_file, 'r') as source_file:
            data = json.load(source_file)
            polyline = ujson.dumps(data["map"]["polyline"], escape_forward_slashes=False)
            activities_file.write("{},".format(polyline))

    activities_file.write("];")
    activities_file.close()

# create_file_activities()

def distance(origin, destination):
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371 # km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c

    return d * 1000

def decode(encoded):
    index, lat, lng = 0, 0, 0
    coordinates = []
    changes = {'latitude': 0, 'longitude': 0}
    factor = 100000.0

    while index < len(encoded):
        for unit in ['latitude', 'longitude']: 
            shift, result = 0, 0

            while True:
                byte = ord(encoded[index]) - 63
                index+=1
                result |= (byte & 0x1f) << shift
                shift += 5
                if not byte >= 0x20:
                    break

            if (result & 1):
                changes[unit] = ~(result >> 1)
            else:
                changes[unit] = (result >> 1)

        lat += changes['latitude']
        lng += changes['longitude']

        coordinates.append((lng / factor, lat / factor))

    return coordinates

# Get coordinates from activities
def coordinates():
    activity_coordinates = []

    folder_path = 'activities'
    with open('activities.js', 'w') as activities_file:
        activities_file.write("var polylines = [")

        index = 0
        for json_file in glob.glob(os.path.join(folder_path, '*.json')):
            with open(json_file, 'r') as source_file:
                data = json.load(source_file)
                id = data["id"]

                if len(data["segment_efforts"]) > 1:
                    city = data["segment_efforts"][0]["segment"]["city"]
                    expected_city = "San Francisco"

                    if city != expected_city:
                        print("Skipping {} ({}), as it's outside of {}.".format(city, id, expected_city))
                        continue
                else:
                    continue

                polyline_str = ujson.dumps(data["map"]["polyline"], escape_forward_slashes=False)

                current_activity_coordinates = decode(polyline_str.replace('\\\\','\\'))

                coordinates_threshold = 10000

                if len(current_activity_coordinates) > coordinates_threshold:
                    print("Skipping {}, as it contains too many coordinates {}.".format(id, len(current_activity_coordinates)))
                    continue

                print("{} will be used for map matching.".format(id))
                activity_coordinates.append(current_activity_coordinates)
                
                # Add only first two activities
                if index < 2:
                    activities_file.write("{},".format(ujson.dumps(data["map"]["polyline"], escape_forward_slashes=False)))
                
                index += 1
                # or add activity to show full list
                # activities_file.write("{},".format(ujson.dumps(data["map"]["polyline"], escape_forward_slashes=False)))

        activities_file.write("];")
        activities_file.close()

    return activity_coordinates

# coordinates()

# Get ways and nodes from OpenStreetMap
def ways_and_nodes():
    with open("san_francisco.json", 'r') as source_file:
        data = json.load(source_file)

        nodes = {}
        ways = {}

        for element in data["elements"]:
            if element["type"] == "way":
                nodes_in_way = []
                for node in element["nodes"]:
                    nodes_in_way.append(node)

                ways[element["id"]] = (nodes_in_way, element["tags"]["name"])
            elif element["type"] == "node":
                nodes[element["id"]] = (element["id"], element["lat"], element["lon"], 0)
    
    return (ways, nodes)

def create_streets():
    start_time = time.time()

    (ways, nodes) = ways_and_nodes()

    activities = coordinates()

    print("Total number of activities, which were started in San Francisco: {}".format(len(activities)))

    for activity_coordinates in activities[0:2]:
        print("Activity contains {} coordinates.".format(len(activity_coordinates)))

        index = 0
        for coordinate in activity_coordinates:
            print("Trying to match activity coordinate #{}: {}".format(index, coordinate))
            index += 1
            
            for way in ways:
                for node in ways[way][0]:
                    dist = distance(coordinate, (nodes[node][1], nodes[node][2]))

                    if dist < float(25.0):
                        list_from_tuple = list(nodes[node])
                        list_from_tuple[3] = 1

                        nodes[node] = tuple(list_from_tuple)

    streets = {}
    for way in ways:
        if ways[way][1] not in streets:
            
            street_nodes = []

            for node in ways[way][0]:
                street_nodes.append(nodes[node])

            street_info = {
                "nodes": street_nodes,
                "progress": 0.0
            }

            streets[ways[way][1]] = street_info
        else:
            arr = streets[ways[way][1]]["nodes"]

            street_nodes = []

            for node in ways[way][0]:
                street_nodes.append(nodes[node])

            arr += street_nodes

            street_info = {
                "nodes": arr,
                "progress": 0.0
            }

            streets[ways[way][1]] = street_info

    for street in streets:
        total_number_of_nodes = len(streets[street]["nodes"])
        total_number_of_visited_nodes = 0
        for nodes in streets[street]["nodes"]:
            if nodes[3] == 1:
                total_number_of_visited_nodes += 1
        
        percentage_of_visited_nodes = float("{:.2f}".format(total_number_of_visited_nodes * 100 / total_number_of_nodes))

        print("Total number of nodes: {}, total number of visited nodes: {}.".format(total_number_of_nodes, total_number_of_visited_nodes))

        if percentage_of_visited_nodes != 0.0:
            print("Visited {} percent of the {}".format(percentage_of_visited_nodes, street))

        streets[street]["progress"] = percentage_of_visited_nodes

    with open('streets.json', 'w') as f:
        json.dump(streets, f)

    end_time = time.time()
    time_difference = (end_time - start_time) / 60
    print("It took {:.2f} minutes to map match coordinates.".format(time_difference))

create_streets()

# --------------

# $ python3 -m pip install exif

# with open('image.jpg', 'rb') as image_file:
#     my_image = Image(image_file)

#     print(my_image.has_exif)
#     print(my_image.list_all())
#     print(my_image.datetime)
#     print(my_image.datetime_original)
#     print(my_image._gps_ifd_pointer)
#     print(my_image.gps_img_direction)
#     print(my_image.gps_img_direction_ref)

# --------------

# from PIL import Image
# from PIL.ExifTags import TAGS
# from PIL.ExifTags import GPSTAGS

# def get_exif(filename):
#     image = Image.open(filename)
#     image.verify()
#     return image._getexif()

# def get_geotagging(exif):
#     if not exif:
#         raise ValueError("No EXIF metadata found")

#     geotagging = {}
#     for (idx, tag) in TAGS.items():
#         if tag == 'GPSInfo':
#             if idx not in exif:
#                 raise ValueError("No EXIF geotagging found")

#             for (key, val) in GPSTAGS.items():
#                 if key in exif[idx]:
#                     geotagging[val] = exif[idx][key]

#     return geotagging

# def get_decimal_from_dms(dms):
#     degrees = dms[0]
#     minutes = dms[1] / 60.0
#     seconds = dms[2] / 3600.0

#     print(degrees + (minutes / 60.0) + (seconds / 3600.0))

#     return round(degrees + minutes + seconds, 5)

# def get_coordinates(geotags):
#     lat = get_decimal_from_dms(geotags['GPSLatitude'])
#     lon = get_decimal_from_dms(geotags['GPSLongitude'])

#     return (lat, lon)

# exif = get_exif('test.jpg')
# geotags = get_geotagging(exif)
# print(geotags)
# print(get_coordinates(geotags))

# --------------

# photos_file = open("photos.js", "w")
# photos_file.write("var photos = [")
# folder_path = 'photos'

# for csv_file in glob.glob(os.path.join(folder_path, '*.csv')):
#     with open(csv_file, 'r') as source_file:
#         print(source_file)
#         csv_reader = csv.DictReader(source_file)
#         line_count = 0
#         for row in csv_reader:
#             if line_count == 0:
#                 line_count += 1

#             latitude = row["GPSLatitude"]
#             longitude = row["GPSLongitude"]

#             if latitude == "-" and longitude == "-":
#                 continue
            
#             photos_file.write("[{}, {}],".format(latitude, longitude))

#             line_count += 1
        
# photos_file.write("];")
# photos_file.close()