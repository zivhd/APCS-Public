import math
from bson import ObjectId
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import requests
from models.job_order import JobOrder
from models.pothole import Pothole
import math
from bson import ObjectId
from models.pothole import Pothole
import certifi
import os
from typing import List
from algo import calculate_priority

google_maps_token = ""
uri = (
    ""
)
mapbox_access_token = os.environ.get('MAPBOX_ACCESS_TOKEN')
google_maps_token = os.environ.get('GOOGLE_MAPS_TOKEN')
db = MongoClient(uri, tlsCAFile=certifi.where())
db = db.APCS
SITE_ROOT = os.path.realpath(os.path.dirname(__file__))


class Segment:
    def __init__(
        self,
        _id,
        points: list =[],
        snapped_to_road_points: list =[],
        nearby_establishments : list =[],
        road_classification=None,
        is_mabuhay_lane=None,
        population_density=None,
        is_in_intersection=None,
        intersecting_road=None,
        has_sidewalk=None,
        is_oneway=None,
        is_access_road=None,
        traffic_volume=None,
        priority_score=None,
        priority_level=None,
        job_order : JobOrder = None,
        barangays_affected : list= [],
        roads_affected : list = [],

    ):
        self._id = _id
        self.points = points if points is not None else []
        self.snapped_to_road_points = snapped_to_road_points if snapped_to_road_points is not None else []
        self.nearby_establishments = nearby_establishments if nearby_establishments is not None else []
        self.road_classification = road_classification
        self.is_mabuhay_lane = is_mabuhay_lane
        self.population_density = population_density
        self.is_in_intersection = is_in_intersection
        self.intersecting_road = intersecting_road
        self.has_sidewalk = has_sidewalk
        self.is_oneway = is_oneway
        self.is_access_road = is_access_road
        self.traffic_volume = traffic_volume
        self.priority_score = priority_score
        self.priority_level = priority_level
        self.job_order = job_order
        self.barangays_affected = barangays_affected if barangays_affected is not None else []
        self.roads_affected = roads_affected if roads_affected is not None else []
        
        
    def to_dict(self):
  
        segment_dict = {
        "_id": str(self._id),
        "points": self.points,
        "snapped_to_road_points": self.snapped_to_road_points,
        "nearby_establishments": self.nearby_establishments,
        "road_classification": self.road_classification,
        "is_mabuhay_lane": self.is_mabuhay_lane,
        "population_density": self.population_density,
        "is_in_intersection": self.is_in_intersection,
        "intersecting_road": self.intersecting_road,
        "has_sidewalk": self.has_sidewalk,
        "is_oneway": self.is_oneway,
        "traffic_volume": self.traffic_volume,
        "is_access_road": self.is_access_road,
        "priority_score": self.priority_score,
        "priority_level": self.priority_level,
        "barangays_affected" : self.barangays_affected,
        "roads_affected" : self.roads_affected,
         "job_order": JobOrder(None, None, None, None, None, None, None, None).to_dict() if self.job_order is None else self.job_order
            
    }



        return segment_dict


    def update_segment_classification(self, pothole: Pothole):
        if self is not None and self.road_classification is not None:
            current_classification = self.road_classification
            new_classification = pothole.road_classification
            if new_classification is None or not new_classification or new_classification == "None":
                new_classification = "Tertiary"
            # print(f"self.road_classification {self.road_classification}")
            # print(f"pothole.road_classification {pothole.road_classification}")
            if (
                current_classification == "Primary"
                or current_classification == new_classification
            ):
                # print("is_already_primary_or_same")
                return
            road_classifications = ["Primary", "Secondary", "Tertiary"]
            highest_classification_index = min(
                road_classifications.index(current_classification),
                road_classifications.index(new_classification),
            )

            self.road_classification = road_classifications[
                highest_classification_index
            ]

    def update_segment_population_density(self, pothole: Pothole):
        if self is not None and self.population_density is not None:
            current_density = self.population_density
            new_density = pothole.population_density

            if current_density == new_density:
                # print("density_same")
                return
            elif new_density > current_density:
                self.population_density = new_density

    def update_segment_mabuhay_lane(self, pothole: Pothole):
        if self is not None and self.is_mabuhay_lane is not None:
            current_mabuhay = self.is_mabuhay_lane
            new_mabuhay = pothole.is_mabuhay_lane
            if current_mabuhay == True:
                # print("mabuhay true already")
                return
            if new_mabuhay == False:
                # print("new mabuhay false ")
                return
            # print("changed mabuhay lane to true")
            self.is_mabuhay_lane = True

    def update_segment_intersection(self, pothole: Pothole):
        if self is not None and self.is_in_intersection is not None:
            current_intersection = self.is_in_intersection
            new_intersection = pothole.is_in_intersection
            if current_intersection == True:
                # print("is_in_intersection true already")
                return
            if new_intersection == False:
                # print("new is_in_intersection false ")
                return
            # print("changed is_in_intersection to true")
            self.is_in_intersection = True

    def update_segment_traffic_volume(self, pothole: Pothole):
        if self is not None and self.traffic_volume is not None:
            traffic_volume_map = {
                "Extremely Low": 0.1,
                "Very Low": 0.2,
                "Low": 0.3,
                "Moderate": 0.4,
                "High": 0.5,
                "Very High": 0.6,
                "Extremely High": 0.7,
                "Intense": 0.8,
                "Maximum": 0.9,
                "Standstill": 0.10,
            }
            current_traffic_value = traffic_volume_map.get(self.traffic_volume, 0)
            new_traffic_value = traffic_volume_map.get(pothole.traffic_volume, 0)
            if new_traffic_value > current_traffic_value:
                self.traffic_volume = pothole.traffic_volume
    def update_segment_has_sidewalk(self, pothole: Pothole):
        if self is not None and self.has_sidewalk is not None:
            current_has_sidewalk = self.has_sidewalk
            new_has_sidewalk = pothole.has_sidewalk
            if current_has_sidewalk == True:
                # print("is_in_intersection true already")
                return
            if new_has_sidewalk == False:
                # print("new is_in_intersection false ")
                return
            self.is_in_intersection = True
    def update_segment_is_oneway(self, pothole: Pothole):
        if self is not None and self.is_oneway is not None:
            current_is_oneway = self.is_oneway
            new_is_oneway = pothole.is_oneway
            if current_is_oneway == True:
                # print("is_in_intersection true already")
                return
            if new_is_oneway == False:
                # print("new is_in_intersection false ")
                return
            self.is_in_intersection = True
    def update_segment_is_access_road(self,pothole:Pothole):
        if self is not None and self.is_access_road is not None:
            abbreviated_road_name = pothole.abbreviate_road_name(pothole.road_name)
            result = pothole.find_one_case_insensitive(
                db.roads, "name", abbreviated_road_name
            )
            if result is not None and "is_access_road" in result:
                self.is_access_road = True
            else:
                if self.road_classification is not None:
                    if self.road_classification == "Primary":
                        self.is_access_road = True
                        return
                if self.is_mabuhay_lane is not None:
                    if self.is_mabuhay_lane:
                        self.is_access_road = True
                        return
                self.is_access_road = False
            
        
                  
    def get_segment_priority(self,segment_list):
        if self is not None:
            establishment = len(self.nearby_establishments)
            intersection_val = self.is_in_intersection

            if intersection_val == False:
                intersection = 0
            elif intersection_val == True:
                intersection = 1

            road_classification = self.road_classification

            population_density = self.population_density
            
            traffic_volume = self.traffic_volume
            
            access_road = self.is_access_road
            
            presence_of_sidewalks = self.has_sidewalk
            
            is_oneway = self.is_oneway

            potholes = len(self.points)

            priority_score = calculate_priority(
              
                access_road,
                road_classification,
                establishment,
                population_density,
                traffic_volume,
                presence_of_sidewalks,
                potholes,
                intersection,
                segment_list
            )
            print(f"==>> priority_score: {priority_score}")
            

            if priority_score >= 0.7:
                priority_value = "High Priority Road Segment"
            elif priority_score >= 0.4:
                priority_value = "Medium-High Priority Road Segment"
            elif priority_score >= 0.2:
                priority_value = "Medium-Low Priority Road Segment"
            else:
                priority_value = "Low Priority Road Segment"

            # Update priority score in the segment document
            self.priority_score = priority_score
            self.priority_level = priority_value
            # print(f"getting prio score : {priority_score}")


    # NOT DONE YET PLEASE ADD ACCESS ROAD AND TRAFFIC VOLUME!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


# SEIFER'S CODE REFACTORING TO CREATE 2 FUNCTIONS FOR MANUAL SEGMENTATION
def add_to_segment(segment : Segment, pothole: Pothole):

    document_id = ObjectId(segment._id)
    # print(f"{segment._id} updated: added pothole {pothole._id}")

    # Update pothole with the existing segment _id

    pothole.segment_id = str(segment._id)

    # Update segment attributes
    segment.points.append(
        {"latitude": pothole.latitude, "longitude": pothole.longitude}
    )
    segment.nearby_establishments = list(
        set(pothole.nearby_establishments + segment.nearby_establishments)
    )
    
    if pothole.barangay not in segment.barangays_affected:
        segment.barangays_affected.append(pothole.barangay)
        
    if pothole.road_name not in segment.roads_affected:
        segment.roads_affected.append(pothole.road_name)
  


    # Print information about the updated segment establishments count
    # print(f"Updated segment count establishment: {len(segment.nearby_establishments)}")

    # Update segment classification, population density, mabuhay lane, and intersection
    segment.update_segment_classification(pothole)
    segment.update_segment_population_density(pothole)
    segment.update_segment_mabuhay_lane(pothole)
    segment.update_segment_intersection(pothole)
    segment.update_segment_traffic_volume(pothole)
    segment.update_segment_is_access_road(pothole)
    segment.update_segment_has_sidewalk(pothole)
    segment.update_segment_is_oneway(pothole)
    segment.snapped_to_road_points = snap_to_roads(segment.points)
    # Update the segment in the database
    db.segments.update_one(
        {"_id": document_id}, {"$set": {key: value for key, value in segment.to_dict().items() if key != "_id"}}
    )
    
    db.potholes.update_one(
        {"_id": ObjectId(pothole._id)}, {"$set": {"segment_id": document_id}}
    )
    # Return the updated segment
    return segment


def create_new_segment(pothole: Pothole):

    # Create a new segment with the current pothole
    # print(f"New segment added using pothole {pothole._id}")

    # Generate a new ObjectId for the new segment
    new_segment_id = ObjectId()
    
    
    # Create a new Segment object with a generated ObjectId
    new_segment = Segment(
        _id=str(new_segment_id),
        points=[{"latitude": pothole.latitude, "longitude": pothole.longitude}],
        road_classification=pothole.road_classification,
        population_density=pothole.population_density,
        is_mabuhay_lane=pothole.is_mabuhay_lane,
        is_in_intersection=pothole.is_in_intersection,
        nearby_establishments=list(set(pothole.nearby_establishments)),
        has_sidewalk=pothole.has_sidewalk,
        is_oneway=pothole.is_oneway,
        traffic_volume=pothole.traffic_volume,
        is_access_road= True if pothole.road_classification == "Primary" or pothole.is_mabuhay_lane else pothole.is_access_road,
        barangays_affected=[pothole.barangay],
        roads_affected= [pothole.road_name]
    )
    new_segment.snapped_to_road_points = snap_to_roads(new_segment.points)
    result = db.segments.insert_one({key: value for key, value in new_segment.to_dict().items() if key != "_id"})
    
    # Insert the new segment document into the database
    db.segments.update_one(
        {"_id": ObjectId(result.inserted_id)}, {"$set": {key: value for key, value in new_segment.to_dict().items() if key != "_id"}}
    )

    # print(f"new_segment.priority_score :  {new_segment.priority_score} ")
    # Update pothole with the new segment _id
    db.potholes.update_one(
        {"_id": ObjectId(pothole._id)}, {"$set": {"segment_id": ObjectId(result.inserted_id)}}
    )

    # print(f"New segment count establishment: {len(new_segment.nearby_establishments)}")

    # Return the new segment
    return result.inserted_id


# SEIFER'S CODE REFACTORING TO CREATE 2 FUNCTIONS FOR MANUAL SEGMENTATION


def update_segments(pothole: Pothole):
    print(f"==>> segment_id: {pothole.segment_id}")
    if pothole.segment_id is not None:
        return None
    cursor_segments = db.segments.find({"job_order.status": {"$ne": "Resolved"}})
    segment_list = [Segment(**segment_data) for segment_data in cursor_segments]

            
    segment: Segment = find_or_create_segment(pothole, segment_list)
    if segment and segment.job_order['status'] is None:
       return add_to_segment(segment,pothole)
    else:
       return create_new_segment(pothole)


def find_or_create_segment(pothole: Pothole, segments: List[Segment]) -> Segment:
    print(f"==>> len segments: {len(segments)}")
    print(f"==>> pothole.road_classification: {pothole.road_classification}")
    
    distance_thresholds = {
        "Primary": 50,
        "Secondary": 25,
        "Tertiary": 10,
    }

    threshold = distance_thresholds.get(pothole.road_classification, 10)
    print(f"==>> threshold: {threshold}")

    
    for segment in segments:
        distance_to_first_point = haversine(
            segment.points[0]["latitude"],
            segment.points[0]["longitude"],
            pothole.latitude,
            pothole.longitude,
        )
        distance_to_end_point = haversine(
            segment.points[-1]["latitude"],
            segment.points[-1]["longitude"],
            pothole.latitude,
            pothole.longitude,
        )
        distance = min(distance_to_first_point, distance_to_end_point)
        print(f"------------------[DISTANCE]: {distance}----------------------------")
        if distance <= threshold:
            return segment

    return None


def haversine(lat1, lon1, lat2, lon2):
    # Radius of the Earth in kilometers
    R = 6371.0

    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Differences in coordinates
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Distance in kilometers
    distance = R * c * 1000

    return distance


def snap_to_roads(points):
    base_url = "https://roads.googleapis.com/v1/snapToRoads"
    params = {
        "interpolate": "true",
        "path": "|".join(
            [f'{point["latitude"]},{point["longitude"]}' for point in points]
        ),
        "key": google_maps_token,
    }
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        result = response.json()
        if "snappedPoints" in result:
            return result["snappedPoints"]
    return None
