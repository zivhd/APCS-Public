import re
from bson import ObjectId
import requests
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi
import json
import os
import urllib3
from shapely.geometry import shape, Point

uri = (
    ""
)
mapbox_access_token = os.environ.get('MAPBOX_ACCESS_TOKEN')
google_maps_token = os.environ.get('GOOGLE_MAPS_TOKEN')
db = MongoClient(uri, tlsCAFile=certifi.where())
db = db.APCS
SITE_ROOT = os.path.realpath(os.path.dirname(__file__))


class Pothole:
    def __init__(
        self,
        _id,
        latitude,
        longitude,
        nearby_establishments=None,
        road_name=None,
        barangay=None,
        road_classification=None,
        is_mabuhay_lane=None,
        population_density=None,
        is_in_intersection=None,
        intersecting_road=None,
        has_sidewalk=None,
        is_oneway=None,
        segment_id=None,
        is_access_road=None,
        traffic_volume=None,
        contribution_id=None,
        filename=None,
        is_resolved=None,
        job_order_id=None,
        
    ):
        self._id = _id
        self.latitude = latitude
        self.longitude = longitude
        self.nearby_establishments = nearby_establishments
        self.road_name = road_name
        self.barangay = barangay
        self.road_classification = road_classification
        self.is_mabuhay_lane = is_mabuhay_lane
        self.population_density = population_density
        self.is_in_intersection = is_in_intersection
        self.intersecting_road = intersecting_road
        self.has_sidewalk = has_sidewalk
        self.is_oneway = is_oneway
        self.is_access_road = is_access_road
        self.traffic_volume = traffic_volume
        self.segment_id = segment_id
        self.contribution_id = contribution_id
        self.job_order_id = job_order_id
        self.is_resolved = is_resolved
        self.filename = filename
    
    
    def to_dict(self):
        # Convert Pothole object to a dictionary
        pothole_dict = {
            "_id": str(self._id),
            "latitude": float(self.latitude),
            "longitude": float(self.longitude),
            "road_name": self.road_name,
            "barangay": self.barangay,
            "nearby_establishments": self.nearby_establishments,
            "road_classification": "Tertiary" if self.road_classification is None or self.road_classification == None else self.road_classification,
            "is_mabuhay_lane": False if self.is_mabuhay_lane is None or self.is_mabuhay_lane == None else self.is_mabuhay_lane,
            "population_density": self.population_density,
            "traffic_volume": self.traffic_volume,
            "is_in_intersection": False if self.is_in_intersection is None or self.is_in_intersection == None else self.is_in_intersection,
            "intersecting_road": self.intersecting_road,
            "is_access_road": False if self.is_access_road is None or self.is_access_road == None else self.is_access_road,
            "segment_id": None if self.segment_id == "None" or self.segment_id is None else str(self.segment_id),
            "contribution_id": str(self.contribution_id),
            "filename": str(self.filename),
        }
        return pothole_dict

    def get_road_name(self):
        if not hasattr(self, "road_name") or self.road_name is None:
            contribution =db.contributions.find_one(
                {"_id": ObjectId(self.contribution_id)},
            )
            road_name = contribution.get("road_name")
            print(road_name)
            self.road_name = road_name

    def add_establishment(self, establishment_name):
        if not self.nearby_establishments or self.nearby_establishments is None:
            self.nearby_establishments = []
        self.nearby_establishments.append(establishment_name)

    def get_establishments(self):
        if not self.nearby_establishments or self.nearby_establishments is None:
            # print(f'Retrieving nearby_establishments for {self._id}')
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={self.latitude}%2C{self.longitude}&radius=50&key={google_maps_token}"
            self.process_page(url)

    def process_page(self, url):
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            location_types = {
                location["name"]: location["types"] for location in data["results"]
            }
    
            for name, types in location_types.items():
                if "establishment" in types:
                    self.add_establishment(name)

            next_page_token = data.get("next_page_token")

            if next_page_token:
                # print("next page")
                next_page_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?pagetoken={next_page_token}&key={google_maps_token}"
                self.process_page(next_page_url)

    def abbreviate_road_name(self, road_name):
        suffix_mapping = {
            "avenue": "ave",
            "drive": "dr",
            "circle": "cir",
            "street": "st",
        }

        for suffix, abbreviation in suffix_mapping.items():
            if road_name.lower().endswith(suffix):
                road_name = road_name[: -len(suffix)] + abbreviation
                break

        return road_name

    def find_one_case_insensitive(self, collection, field, value):
        query = {field: {"$regex": re.compile(value, re.IGNORECASE)}}
        result = collection.find_one(query)
        return result

    def get_road_classification(self):
        if self.road_name is None:
            return

        if self.road_classification is None or self.is_mabuhay_lane is None:
            # print(f'Retrieving road classification for {self._id}')
            abbreviated_road_name = self.abbreviate_road_name(self.road_name)
            result = self.find_one_case_insensitive(
                db.roads, "name", abbreviated_road_name
            )
            if not result or result is None:
                self.road_classification = "Tertiary"
                self.is_mabuhay_lane = False
                return
            if "type" in result:
                self.road_classification = result["type"]
                # print(f'road classification for {self._id} is {self.road_classification} ')

            if "isMabuhayLane" in result:
                self.is_mabuhay_lane = result["isMabuhayLane"]
                # print(f'road is_mabuhay_lane for {self._id} is {self.is_mabuhay_lane} ')

    def get_sidewalks(self):
        if self.has_sidewalk is None:
            # incomplete
            self.has_sidewalk = True

    def get_oneway(self):
        if self.is_oneway is None:
            # incomplete
            self.is_oneway = True

    def get_if_access_road(self):
        print(f"==>> type(self.road_name): {type(self.road_name)}")
        print(f"==>> self.road_name: {self.road_name}")
        if self.road_name is None:
            return
        abbreviated_road_name = self.abbreviate_road_name(self.road_name)
        result = self.find_one_case_insensitive(
           
            db.roads, "name", abbreviated_road_name
        ) 
        
        print(f"==>> result: {result}")
        if not result or result is None:
            self.is_access_road = False
        elif "is_access_road" in result:
            self.is_access_road = True
        else:
            self.is_access_road = False
    def get_intersection(self):
        if (
            not hasattr(self, "is_in_intersection")
            or not hasattr(self, "intersecting_road")
            or self.intersecting_road is None
            or self.is_in_intersection is None
        ):
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(
                f"http://api.geonames.org/findNearestIntersectionOSMJSON?lat={self.latitude}&lng={self.longitude}&username=zivhd",
                verify=False,
            )

            if response.status_code == 200:
                result = response.json()["intersection"]["distance"]

                if float(result) <= 0.01:
                    self.is_in_intersection = True
                    self.intersecting_road = response.json()["intersection"]["street2"]
                else:
                    self.is_in_intersection = False
                    self.intersecting_road = "n/a"

    def get_pop_density(self):
        if not hasattr(self, "barangay") or self.barangay is None:
            return

        if not hasattr(self, "population_density") or self.population_density is None:
            barangay = db.barangays.find_one({"name": self.barangay})

            if barangay:
                population_density = barangay["population"] / barangay["area"]
                self.population_density = population_density

    def get_barangay(self):
        if not hasattr(self, "barangay") or self.barangay is None:
            data = get_barangay_polygons()

            for polygon in data:
                boundaries = shape(
                    {"type": "Polygon", "coordinates": polygon["Coordinates"]}
                )
                name = polygon["NAME_03"]

                point_coordinates = Point(float(self.longitude), float(self.latitude))

                if boundaries.contains(point_coordinates):
                    self.barangay = name

            

    def get_details(self):
        print("1")
        self.get_establishments()
        print("2")
        self.get_road_name()
        print("3")
        self.get_barangay()
        print("4")
        self.get_road_classification()
        print("5")
        self.get_pop_density()
        print("6")
        self.get_intersection()
        print("7")
        self.get_sidewalks()
        print("8")
        self.get_oneway()
        print("9")
        self.get_if_access_road()
        print("10")

    def update_pothole(self):
        update_fields = {}
        print("A")
        if hasattr(self, "is_access_road") or self.is_access_road is not None:
            update_fields["is_access_road"] = self.is_access_road
        print("B")
        if (
            hasattr(self, "is_in_intersection")
            and hasattr(self, "intersecting_road")
            or self.is_in_intersection is not None
            and self.intersecting_road is not None
        ):
            update_fields["is_in_intersection"] = self.is_in_intersection
            update_fields["intersecting_road"] = self.intersecting_road
        print("C")
        if hasattr(self, "population_density") or self.population_density is not None:
            update_fields["population_density"] = self.population_density
        print("D")
        if hasattr(self, "barangay") or self.barangay is not None:
            update_fields["barangay"] = self.barangay
        print("E")           
        if hasattr(self, "is_mabuhay_lane") or self.is_mabuhay_lane is not None:
            update_fields["is_mabuhay_lane"] = self.is_mabuhay_lane
        if hasattr(self, "is_access_road") or self.is_access_road is not None:
            update_fields["is_access_road"] = self.is_access_road
        print("F")
        if (
            hasattr(self, "nearby_establishments")
            or self.nearby_establishments is not None
        ):
            update_fields["nearby_establishments"] = self.nearby_establishments
        print("G")
        if hasattr(self, "road_name") or self.road_name is not None:
            update_fields["road_name"] = self.road_name
        print("H")
        if hasattr(self, "has_sidewalk") or self.has_sidewalk is not None:
            update_fields["has_sidewalk"] = self.has_sidewalk
        print("I")
        if hasattr(self, "is_oneway") or self.is_oneway is not None:
            update_fields["is_oneway"] = self.is_oneway
        print("J")
        if hasattr(self, "road_classification") or self.road_classification is not None:
            update_fields["road_classification"] = self.road_classification
        print("K")        
        if update_fields:
            db.potholes.update_many({"_id": ObjectId(self._id)}, {"$set": update_fields})



def get_barangay_polygons():
    json_url = "static/data/new_barangays.json"

    with open(json_url, "r", encoding="utf-8") as file:
        data = json.load(file)

    polygon_list = []

    if "features" in data:
        for feature in data["features"]:
            properties = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            name_03 = properties.get("ADM4_EN")
            print("name_03:", name_03)
            coordinates = geometry.get("coordinates")

            if name_03 and coordinates:
                result_dict = {"NAME_03": name_03, "Coordinates": coordinates}
                polygon_list.append(result_dict)

    return polygon_list
