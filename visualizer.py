# import polyline
import requests
import json
import os
import glob
import ujson
# from exif import Image
import csv

def get_activities(amount_per_page, access_token):
    url = "https://www.strava.com/api/v3/activities?access_token={}&per_page={}&page=1".format(access_token, amount_per_page)
    print(url)
    response = requests.get(url)

    return response.json()

def get_activity(id, access_token):
    url = "https://www.strava.com/api/v3/activities/{}?include_all_efforts=true&access_token={}".format(id, access_token)
    response = requests.get(url)

    return response.json()

# --------------

# access_token = ""

# with open('temp.json', 'w') as activities_file:
#     json.dump(get_activities(1, access_token), activities_file)

# f = open('temp.json')

# data = json.load(f)
  
# for element in data:
#     id = element["id"]
#     print(id)

#     response = get_activity(id, access_token)
#     with open("activities/new/{}.json".format(id), "w") as json_file:
#         json.dump(response, json_file)
  
# f.close()

# --------------

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
