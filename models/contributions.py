from models.pothole import get_barangay_polygons
from shapely.geometry import shape, Point
class Contribution:
    def __init__(
        self,
        _id=None,
        road_name=None,
        latitude=None,
        longitude=None,
        has_sidewalk=None,
        is_oneway=None,
        filename=None,
        is_validated=False,
        contributor_email=None,
        contributor_fname=None,
        contributor_lname=None,
        contributor_role=None,
        contribution_date=None,
        validator_email= None,
        validator_fname = None,
        validator_lname = None,
        validation_date= None,
        barangay = None,
        is_rfex = None,
        road_features = None,
        image_timestamp = None,
        disapproval_reason = None,
        head_validated = None,
        traffic_volume = None,
    ):
        self._id = _id
        self.road_name = road_name
        self.latitude = latitude
        self.longitude = longitude
        self.has_sidewalk = has_sidewalk
        self.is_oneway = is_oneway
        self.filename = filename
        self.contributor_email = contributor_email
        self.contributor_fname = contributor_fname
        self.contributor_lname = contributor_lname
        self.contributor_role = contributor_role
        self.contribution_date = contribution_date
        self.is_validated = is_validated
        self.validator_email = validator_email
        self.validator_fname = validator_fname
        self.validator_lname = validator_lname
        self.validation_date = validation_date
        self.barangay =barangay
        self.is_rfex = is_rfex
        self.road_features = road_features
        self.image_timestamp = image_timestamp
        self.disapproval_reason = disapproval_reason
        self.head_validated = head_validated
        self.traffic_volume = traffic_volume
    def to_dict(self):
        return {
            "_id": str(self._id),
            "road_name": self.road_name,
            "latitude": float(self.latitude),
            "longitude": float(self.longitude),
            "has_sidewalk": self.has_sidewalk,
            "is_oneway": self.is_oneway,
            "barangay" :self.barangay,
            "filename": self.filename,
            "is_validated": self.is_validated,
            "contributor_email": self.contributor_email,
            "contributor_fname": self.contributor_fname,
            "contributor_lname": self.contributor_lname,
            "contributor_role": self.contributor_role,
            "contribution_date": self.contribution_date,
            "validator_email": self.validator_email,
            "validator_fname": self.validator_fname,
            "validator_lname": self.validator_lname,
            "validation_date": self.validation_date,
            "is_rfex": self.is_rfex,
            "road_features": self.road_features,
            "image_timestamp":  self.image_timestamp,
            "disapproval_reason" : self.disapproval_reason,
            "head_validated" : self.head_validated,
            "traffic_volume" : self.traffic_volume
        }
        
    
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
