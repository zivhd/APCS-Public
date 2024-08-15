import os
from pymongo.mongo_client import MongoClient
import certifi

uri = ""
mapbox_access_token = os.environ.get('MAPBOX_ACCESS_TOKEN')
google_maps_token = os.environ.get('GOOGLE_MAPS_TOKEN')
db = MongoClient(uri, tlsCAFile=certifi.where())
db = db.APCS
SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
FRAMES_FOLDER = os.path.join(SITE_ROOT, "static/frames")


def normalize_variable(value, max_value):
    return value / max_value if max_value != 0 else 0


def calculate_priority(
    is_access_road,
    road_classification,
    num_business_establishments,
    population_density,
    traffic_volume,
    presence_of_sidewalks,
    number_of_potholes,
    is_corner_intersection,
    segment_list
):
    weights = {
        "is_access_road": 0.25,
        "road_classification": 0.2143,
        "num_business_establishments": 0.1786,
        "population_density": 0.07145,
        "traffic_volume": 0.07145,
        "presence_of_sidewalks": 0.1071,
        "number_of_potholes": 0.0714,
        "is_corner_intersection": 0.0357,
    }

    road_classification_map = {"Primary": 3, "Secondary": 2, "Tertiary": 1}

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
        "Standstill": 1.0,
    }

    # Assigning traffic volume value based on the map
    traffic_volume_val = traffic_volume_map.get(traffic_volume, 0)
    normalized_traffic_volume = normalize_variable(traffic_volume_val, 1.0)

    presence_of_sidewalks = int(presence_of_sidewalks)
    is_access_road = int(is_access_road)

    if (
        is_corner_intersection is True
        or is_corner_intersection is None
        or not is_corner_intersection
    ):
        is_corner_intersection = 1
    else:
        is_corner_intersection = 0

    # Calculate the maximum values from the segment_list
    max_population_density = max(segment.population_density for segment in segment_list)
    print(f"==>> max_population_density: {max_population_density}")

    max_num_business_establishments = max(len(segment.nearby_establishments) for segment in segment_list)
    print(f"==>> max_num_business_establishments: {max_num_business_establishments}")

    max_num_potholes = max(len(segment.points) for segment in segment_list)

    print(f"==>> max_num_potholes: {max_num_potholes}")
    normalized_road_classification = normalize_variable(road_classification_map.get(road_classification, 1), 3)
    print(f"==>> normalized_road_classification: {normalized_road_classification}")
    normalized_num_business_establishments = normalize_variable(num_business_establishments, max_num_business_establishments)
    print(f"==>> normalized_num_business_establishments: {normalized_num_business_establishments}")
    normalized_population_density = normalize_variable(population_density, max_population_density)
    print(f"==>> normalized_population_density: {normalized_population_density}")
    normalized_num_potholes = normalize_variable(number_of_potholes, max_num_potholes)
    print(f"==>> normalized_num_potholes: {normalized_num_potholes}")
    normalized_presence_of_sidewalks = normalize_variable(presence_of_sidewalks, 1.0)
    print(f"==>> normalized_presence_of_sidewalks: {normalized_presence_of_sidewalks}")
    normalized_is_corner_intersection = int(is_corner_intersection)
    print(f"==>> normalized_is_corner_intersection: {normalized_is_corner_intersection}")
    normalized_is_access_road = is_access_road
    print(f"==>> normalized_is_access_road: {normalized_is_access_road}")
    if(normalized_road_classification ==  1):
        normalized_is_access_road = 1
    
    priority_score = sum(
        normalized_variable * weights[key] for key, normalized_variable in [
            ("road_classification", normalized_road_classification),
            ("num_business_establishments", normalized_num_business_establishments),
            ("population_density", normalized_population_density),
            ("traffic_volume", normalized_traffic_volume),
            ("presence_of_sidewalks", normalized_presence_of_sidewalks),
            ("number_of_potholes", normalized_num_potholes),
            ("is_corner_intersection", normalized_is_corner_intersection),
            ("is_access_road", normalized_is_access_road),
        ]
    )
    print(f"==>> priority_score: {priority_score}")
    print("<<================>>")
    return priority_score
