import datetime
from bson import ObjectId
import ultralytics
from ultralytics import YOLO
import numpy as np
import json
import os
import PIL.Image as pil
import pymongo
import cv2
import torch
from torchvision import transforms
import sys
import models.contributions 
import re
from extractor.folder_objdet.decoders import *
from app import *
import requests
STEREO_SCALE_FACTOR = 5.4


#REPLACE PATHS BEFORE RUNNING
model_path = 'extractor/folder_objdet/model.pt'
folder_path = 'extractor/folder_objdet/images'
model = YOLO(model_path)
google_maps_token = ""
def reverse_geocode(lat, lng):
    
    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={google_maps_token}"

    try:
        response = requests.get(geocode_url)
        result = response.json()["results"][0]
        for address_component in result["address_components"]:
                if "route" in address_component["types"]:
                    return address_component["long_name"]

    except Exception as e:
          print(f"Error in reverse geocoding: {str(e)}")

    return "Unknown Location"

def disp_to_depth(disp, min_depth, max_depth):
    """Convert network's sigmoid output into depth prediction
    The formula for this conversion is given in the 'additional considerations'
    section of the paper.
    """
    min_disp = 1 / max_depth
    max_disp = 1 / min_depth
    scaled_disp = min_disp + (max_disp - min_disp) * disp
    depth = 1 / scaled_disp
    return scaled_disp, depth

def func_objdet(output_folder, db, email, timestamp):

  print("start func")
  for file_name in os.listdir(folder_path):
    print(file_name)
    if file_name.endswith('.jpg'):
      results_list = {
        "images": []
      }

      image_path = folder_path + '/' + file_name

      results = model(image_path)  # predict on an image
      for result in results:
        objects = []

        class_npy = result.cpu().boxes.cls.numpy()
        i = 0
        temp_class = []
        for classes in class_npy:
          temp_class.append(classes)
          i += 1

        i = 0
        temp_boxes = []
        x_point = []
        y_point = []
        x1 = []
        y1 = []
        x2 = []
        y2 = []
        boxes_npy = result.cpu().boxes.xyxy.numpy()
        for box in boxes_npy:
          x_point.append((box[0]+box[2])/2)
          y_point.append(box[3])
          x1.append(box[0])
          y1.append(box[1])
          x2.append(box[2])
          y2.append(box[3])

        for x in range(len(temp_class)):
          full_boxes = [int(x1[x]), int(y1[x]), int(x2[x]), int(y2[x])]
          c_point = [int(x_point[x]), int(y_point[x])]
          objects.append({"class": int(temp_class[x]), "bounding_box": full_boxes, "bottom_center": c_point})

        results_list["images"].append({"filename": file_name, "objects": objects})
        obj_data = {
	'filename': '',
    	'roadFeatures': {
        	'fence': 0,
        	'obstruction': 0,
        	'construction': 0,
        	'sidewalk': 1,
          'pothole': 0,
    		}
	}
        for image in results_list['images']:
          print("for image start")
          coordinates_string = image['filename']
          coordinates_list = coordinates_string.split(",")  # Split the string into a list using comma as separator
          latitude = coordinates_list[0].strip()  # Get the first part (latitude) and remove any leading or trailing whitespace
          longitude = coordinates_list[1].replace('.jpg', '').strip()


          if latitude or longitude:
              print("Latitude:", latitude)
              print("Longitude:", longitude)
          else:
              print("Latitude and longitude not found in the filename.")

          for obj in image['objects']:
            class_id = obj['class']
            if class_id == 0:
              obj_data['roadFeatures']['fence'] += 1
            elif class_id == 1:
              obj_data['roadFeatures']['obstruction'] += 1
            elif class_id == 2:
              obj_data['roadFeatures']['construction'] += 1
            elif class_id == 3:
              obj_data['roadFeatures']['pothole'] += 1
          user_info = db.user.find_one(
              {"email": email}, {"_id": 0, "fname": 1, "lname": 1, "role": 1}
          )
          roadname = reverse_geocode(latitude,longitude)
          print(roadname)
          if obj_data['roadFeatures']['pothole'] !=0 or obj_data['roadFeatures']['obstruction'] != 0:
            contribution_id = ObjectId()
            new_contribution = models.contributions.Contribution(_id = contribution_id, road_name= roadname,
            latitude=latitude,
            longitude=longitude,
            has_sidewalk=1,
            filename=coordinates_string,
            contributor_email=email,
            is_validated = 0,
            contributor_fname=user_info.get("fname", ""),
            contributor_lname=user_info.get("lname", ""),
            contributor_role=user_info.get("role", ""),
            contribution_date=datetime.now(),
            is_rfex=True,
            road_features = obj_data['roadFeatures'],
            image_timestamp= timestamp
            )
            new_contribution.get_barangay()
            
            print(f"==>> new_contribution: {new_contribution.road_name}")
            db.contributions.insert_one({key: value for key, value in new_contribution.to_dict().items() if key != "_id"})
          



        
      output_file_name = os.path.splitext(file_name)[0] + '_temp' + '.json'
      output_path = os.path.join(output_folder, output_file_name)
      jsonStr = json.dumps(results_list, indent=4, separators=(", ", ": "))
      with open(output_path, 'w') as f:
        f.write(jsonStr)

#---------------------------------------------------------------------------------------------------------------

  model_name = "mono+stereo_1024x320"

  encoder_path = os.path.join("extractor","folder_objdet", "models", model_name, "encoder.pth")
  depth_decoder_path = os.path.join("extractor","folder_objdet", "models", model_name, "depth.pth")

  encoder = ResnetEncoder(18, False)
  depth_decoder = DepthDecoder(num_ch_enc=encoder.num_ch_enc, scales=range(4))

  loaded_dict_enc = torch.load(encoder_path, map_location='cpu')
  filtered_dict_enc = {k: v for k, v in loaded_dict_enc.items() if k in encoder.state_dict()}
  encoder.load_state_dict(filtered_dict_enc)

  loaded_dict = torch.load(depth_decoder_path, map_location='cpu')
  depth_decoder.load_state_dict(loaded_dict)

  encoder.eval()
  depth_decoder.eval()

  i = 0
  for file_name in os.listdir(folder_path):
    if file_name.endswith('.jpg'):
      image_path = folder_path + '/' + file_name
      json_path = output_folder + '/' + os.path.splitext(file_name)[0] + '_temp' + '.json'
      final_json = output_folder + '/' + os.path.splitext(file_name)[0] + '.json'

      input_image = pil.open(image_path).convert('RGB')
      original_width, original_height = input_image.size
      feed_height = loaded_dict_enc['height']
      feed_width = loaded_dict_enc['width']
      input_image_resized = input_image.resize((feed_width, feed_height), pil.LANCZOS)

      input_image_pytorch = transforms.ToTensor()(input_image_resized).unsqueeze(0)

      with torch.no_grad():
          features = encoder(input_image_pytorch)
          outputs = depth_decoder(features)

      disp = outputs[("disp", 0)]

      output_name = i
      i+=1
      scaled_disp, depth = disp_to_depth(disp, 0.1, 100)
      name_dest_npy = str(output_name) + '.npy'
      metric_depth = STEREO_SCALE_FACTOR * depth.cpu().numpy()

      with open(json_path, 'r') as f:
        data = json.load(f)
        indx = 0
        lst_del = []
        for objs in data["images"][0]["objects"]:
          bc_x = objs["bottom_center"][0]/original_width
          bc_y = objs["bottom_center"][1]/original_height
          if metric_depth[0,0,int(bc_y*319),int(bc_x*1023)] > 11:
            lst_del.append(indx)
          indx += 1
        lst_del.reverse()
        for ld in lst_del:
          del data["images"][0]["objects"][ld]
        
      jsonStr = json.dumps(data, indent=4, separators=(", ", ": "))
      with open(final_json, 'w') as f:
        f.write(jsonStr)
      os.remove(json_path)
      os.remove(image_path)
      print(final_json)
