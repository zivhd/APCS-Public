import os
import threading
import time
import subprocess
import certifi
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import pymongo
import argparse
import cv2
import numpy as np
from gpx_converter import Converter
from math import radians, cos, sin, asin, sqrt
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
import io
import requests
import gpxpy
import datetime
import ffmpeg
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pymediainfo import MediaInfo
import gpxpy
import gpxpy.gpx
from datetime import datetime
import subprocess
import re
import pytz
# Originally taken from RFEX group by Agsunto et al.

def extract_and_convert_to_philippine_time(gpx_file):
    # Parse the GPX file
    with open(gpx_file, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    # Define time zones
    utc = pytz.utc
    philippine_tz = pytz.timezone('Asia/Manila')

    # Extract and convert timestamps to Philippine time
    dates = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                # Convert UTC to Philippine time
                philippine_time = point.time.astimezone(philippine_tz)
                return philippine_time.strftime("%Y:%m:%d %H:%M:%S")

    
    
 

def match_starting_timestamp(gpx_file, mp4_file):
    f = None
    with open(gpx_file, 'r') as f:
        gpx = gpxpy.parse(f)
        print(gpx)
        print("YO")
        vid = ffmpeg.probe(mp4_file)
    try:
        duration = float(vid['format']['duration'])
        duration_timedelta = timedelta(seconds=duration)
        media_info = MediaInfo.parse(mp4_file)
        ct = media_info.tracks[1].encoded_date
        dt = datetime.strptime(ct, '%Z %Y-%m-%d %H:%M:%S')
        dt_with_offset = dt + timedelta(hours=8) - timedelta(seconds=8)
        mp4_start_time = dt_with_offset.replace(tzinfo=timezone.utc)
        mp4_start_time = mp4_start_time - duration_timedelta
        for track in gpx.tracks:
            for segment in track.segments:
                filtered_points = []
                for point in segment.points:
                    pointer = point.time.replace(tzinfo=timezone.utc, microsecond=0)
                    pointer += timedelta(hours=8)
                    print('point.time : {} >= start: {}'.format(pointer, mp4_start_time))
                    if (pointer >= mp4_start_time):
                        print("pass")
                        filtered_points.append(point)
                        print(filtered_points)
                
        gpx.tracks[0].segments[0].points = filtered_points
        if (len(gpx.tracks[0].segments[0].points) == 0):
            print('GPX filter failed. Check for diff. time zones / Wrong files. ')
            return gpx_file
        print(gpx.tracks[0].segments[0].points)
        output_file = os.path.basename(gpx_file)
        with open(output_file, "w") as f:
            f.write(gpx.to_xml())
            print(output_file)
           
            print("Success: GPX File synchronized")    
            return output_file
    except Exception as e:
        print(e)
        print("Warning: GPX File not processed")
        return gpx_file	
def extractFrames(video_file, gpx_file, csv_file, username):
    # (2) CONVERT GPX TO CSV
    print("EXTRACTOR STARTING")
    print(gpx_file)
    Converter(input_file=gpx_file).gpx_to_csv(output_file=gpx_file+'.csv')
    data = pd.read_csv(gpx_file+'.csv')
    print(data)
    date = data['time'][0]
    data.drop('time', inplace=True, axis=1)
    data.drop('altitude', inplace=True, axis=1)

    # (3) Get Longitude and Latitude
    df = data
    df_lat = df['latitude']
    df_long = df['longitude']
    # print(df_lat)
    interval = []
    lines = []
    for line in df.iterrows():
        lines.append(line)

    FPS = 60
    i, j = 0, 0
    x = []
    y = []
    R = 6372.8
    while j < len(lines):
        lat1 = df_lat[i]
        lon1 = df_long[i]
        lat2 = df_lat[j]
        lon2 = df_long[j]

        # (3.1) HAVERSINE COMPUTATION
        l1 = float(lon1)
        l2 = float(lat1)
        l3 = float(lon2)
        l4 = float(lat2)

        dLat = radians(l4 - l2)
        dLon = radians(l3 - l1)
        dlat1 = radians(l2)
        dlat2 = radians(l4)
        a = sin(dLat/2)**2 + cos(dlat1)*cos(dlat2)*sin(dLon/2)**2
        c = 2*asin(sqrt(a))
        # END OF HAVERSINE COMPUTATION
        if (R * c >= 0.01):
            interval.append(j)
            x.append(lat2)
            y.append(lon2)
            i = j
            j += 1
        else:
            j += 1

    # (4) EXTRACTION OF FRAMES
    cap = cv2.VideoCapture(video_file)
    print("Video File is " + video_file)
    if (cap.isOpened() == False):
        print("error")

    i = 0
    filenames = []
    while (cap.isOpened()):
        ret, frame = cap.read()
        if ret == False:
            print("RET FALSE")
            break
        if (i < len(interval)):
            if (cap.get(cv2.CAP_PROP_POS_FRAMES) == interval[i]*FPS+1):

                filename = str(x[i]) + ', ' + str(y[i]) + '.jpg'
                filenames.append(filename)
                coordinates = {
                    "type": "Point",
                    "coordinates": [y[i], x[i]]                                               
                    
                }
                # get createdTime from file metadata
                creation_time = date
                # save image to directory 'xFrames'
                output_folder = 'extractor/folder_objdet/images'
                frames = 'static/frames'
                # # Create output folder if it doesn't exist
                # if not os.path.exists(output_folder):
                #     os.makedirs(output_folder)
                # Apply face and plate blurring [POST-PROCESS]
                print(os.path.join(output_folder, filename))
                cv2.imwrite(os.path.join(output_folder, filename), frame)
                cv2.imwrite(os.path.join(frames, filename), frame)
                #   save_to_drive(frame, filename, coordinates)
                i += 1
    print(f'Added {i} record(s) to username: {username}.')
    print(f'Done extracting frames for {username}')
    # delete csv file after extraction
 
    # When everything done, release the video capture object
    cap.release()
    cv2.destroyAllWindows()
   

    return filenames

def face_blur(filename, frame):
    face_img = frame.copy()
    roi = frame.copy()
    # Detects faces and returns the coordinates and dimensions of detected face's contours.
    face = face_cascade.detectMultiScale(
        face_img, scaleFactor=1.8, minNeighbors=4)

    try:
        for (x, y, w, h) in face:
            # extracting the Region of Interest of license plate for blurring.
            roi_ = roi[y:y+h, x:x+w, :]
            # performing blur operation on the ROI
            blurred_roi = cv2.blur(roi_, ksize=(16, 16))
            # replacing the original license plate with the blurred one.
            face_img[y:y+h, x:x+w, :] = blurred_roi
            # cv2.imwrite('Output/' + filename, face_img)
        return face_img
    except:
        print('Oops! Did not find a face in ' + filename)
        # cv2.imwrite('Output/' + filename, frame)
        return frame
    
# Loads the data required for detecting the license plates from cascade classifier.
plate_cascade = cv2.CascadeClassifier('extractor\indian_license_plate.xml')
# Loads the data required for detecting the faces from cascade classifier.
face_cascade = cv2.CascadeClassifier('extractor\haarcascade_frontalface_alt.xml')
    
    
def get_address_from_coords(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}"
    response = requests.get(url)
    if response.ok:
        data = response.json()
        return data['address']['road'], data['address']['city']
    else:
        return None
    
def plate_blur(filename, frame):
    plate_img = frame.copy()
    roi = frame.copy()
    # Detects numberplates and returns the coordinates and dimensions of detected license plate's contours.
    plate = plate_cascade.detectMultiScale(
        plate_img, scaleFactor=1.3, minNeighbors=7)

    try:
        for (x, y, w, h) in plate:
            # extracting the Region of Interest of license plate for blurring.
            roi_ = roi[y:y+h, x:x+w, :]
            # performing blur operation on the ROI
            blurred_roi = cv2.blur(roi_, ksize=(16, 16))
            # replacing the original license plate with the blurred one.
            plate_img[y:y+h, x:x+w, :] = blurred_roi
        return plate_img  # returning the processed image.
    except:
        print('Oops! Did not find a plate number in ' + filename)
        # cv2.imwrite('Output/' + filename, frame)
        return frame
    
def validateVideo(video):
    # check if video file has more black frames than 10% of the total frames
    cap = cv2.VideoCapture(video)
    # Get the number of frames in the video
    num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    # Set the threshold for the percentage of black pixels
    black_threshold = 0.1
    num_black_frames = 0
    for i in range(num_frames):
        # Extract the ith frame
        ret, frame = cap.read()
        if not ret:
            break
        # Convert the frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Compute the percentage of black pixels
        num_black_pixels = np.sum(gray == 0)
        pct_black_pixels = num_black_pixels / (gray.shape[0] * gray.shape[1])
        # Check if the percentage of black pixels exceeds the threshold
        if pct_black_pixels > black_threshold:
            num_black_frames += 1
    # If more than 50% of frames have black pixels, reject submission
    if num_black_frames > num_frames * 0.5:
        return False
    else:
        return True
    
def extract_frames_and_delete(video_path, gpx_path):
    output_folder = 'extractor/older_objdet/images'
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Extract video name without extension
    video_name = os.path.splitext(os.path.basename(video_path))[0]

    # Open the GPX file
    gpx_file = open(gpx_path, 'r')
    gpx = gpxpy.parse(gpx_file)

    # Check if there are any tracks in the GPX file
    if not gpx.tracks:
        print("No tracks found in the GPX file.")
        # Handle the case when there are no tracks (you can exit or raise an exception)
        return

    # Open the video file
    cap = cv2.VideoCapture(video_path)

    # Get the frames per second (fps) of the input video
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    # Counter for frame numbering
    frame_count = 0

    # Time interval (in seconds) to extract frames
    interval = 1

    # Calculate the frame interval based on the fps
    frame_interval = int(fps * interval)

    # Loop through each track in the GPX file
    for track_idx, track in enumerate(gpx.tracks):
        # Loop through each segment in the track
        for segment_idx, segment in enumerate(track.segments):
            # Loop through each point in the segment
            for point_idx, track_point in enumerate(segment.points):
                # Extract latitude and longitude
                latitude = track_point.latitude
                longitude = track_point.longitude

                # Find the corresponding frame for the current track point
                time_difference = track_point.time.replace(tzinfo=timezone.utc) - gpx.time.replace(tzinfo=timezone.utc)
                time_in_seconds = time_difference.total_seconds()
                frame_number = int(time_in_seconds * fps)

                # Check if the frame number is within the video duration
                if frame_number < cap.get(cv2.CAP_PROP_FRAME_COUNT):
                    # Set the video capture to the desired frame
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

                    # Read the frame
                    ret, frame = cap.read()

                    # Format the filename based on video name, latitude, and longitude
                    filename = f"{video_name}_frame_{frame_count:04d}_lat{latitude}_long{longitude}.jpg"
                    frame_filename = os.path.join(output_folder, filename)
                    frame = plate_blur(frame_filename,frame)
                    frame = face_blur(frame_filename,frame)
                    

                    # Save the frame to the output folder
                    cv2.imwrite(frame_filename, frame)

                    # Increment frame count
                    frame_count += 1

    # Release the video capture object
    cap.release()

    # Delete the input video
    os.remove(video_path)

    # Close the GPX file
    gpx_file.close()
    
