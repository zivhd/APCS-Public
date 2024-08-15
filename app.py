from datetime import datetime
import os
from datetime import timedelta
import re
import string
import time
from typing import List
from werkzeug.utils import secure_filename
from flask import (
    Flask,
    render_template,
    send_from_directory,
    url_for,
    request,
    redirect,
    session,
    flash,
    jsonify,
)
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from bson import ObjectId
from extractor.folder_objdet.objdet import *
import secrets
import json
import requests
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from exif import Image as exifImage
from shapely.geometry import Point, shape
import asyncio
import certifi
import xml.etree.ElementTree as ET
import urllib3
import math
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import piexif
from models.pothole import Pothole
from models.segments import Segment, update_segments
from models.contributions import Contribution
from algo import *
from reset import remove_everything
from bson import json_util
from models.job_order import JobOrder
from extractor.extractor import *
import numpy as np
import cv2
import requests
from dotenv import load_dotenv 

load_dotenv()
uri = (
    ""
)
mapbox_access_token = os.environ.get('MAPBOX_ACCESS_TOKEN')
google_maps_token = os.environ.get('GOOGLE_MAPS_TOKEN')
client = MongoClient(uri, tlsCAFile=certifi.where())
db = client.APCS
SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
FRAMES_FOLDER = os.path.join(SITE_ROOT, "static/frames")


def create_app():
    app = Flask(__name__)
    limiter = Limiter(
    key_func=get_remote_address, default_limits=["200 per day", "50 per hour"]
    )
    limiter.init_app(app)
    app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY')
    app.config["MAIL_SERVER"] = os.environ.get('MAIL_SERVER')
    app.config["MAIL_PORT"] = int(os.environ.get('MAIL_PORT', 465))
    app.config["MAIL_USE_SSL"] = os.environ.get('MAIL_USE_SSL') == 'True'
    app.config["MAIL_USERNAME"] = os.environ.get('MAIL_USERNAME')
    app.config["MAIL_PASSWORD"] = os.environ.get('MAIL_PASSWORD')
    app.config["MAIL_DEFAULT_SENDER"] = os.environ.get('MAIL_DEFAULT_SENDER')
    app.config['RECAPTCHA_SITE_KEY'] = os.getenv('RECAPTCHA_SITE_KEY')
    app.config['RECAPTCHA_SECRET_KEY'] = os.getenv('RECAPTCHA_SECRET_KEY')
    mail = Mail(app)

    # user is user in session
    # access is a list of roles that can access that route
    # url is the route if user_role is in access
    def has_access(user, access):
        if user == None:
            return False
        if user["role"] in access:
            return True
        else:
            return False
    def send_email(subject, sender, recipients, body):
        msg = Message(
            subject,
            sender=sender,
            recipients=recipients,
        )
        msg.body = body
        mail.send(msg)



    @app.route("/potholes")
    def get_potholes():
        remove_everything(db)
        cursor_potholes = db.potholes.find()
        # print("Querying potholes from the database.")
        potholes_list = [
            Pothole(**pothole_data) for pothole_data in cursor_potholes]
        
        # THIS SHOULD ONLY BE USED FOR TESTING PURPOSES
       
        # for pothole_instance in potholes_list:
        #     pothole_instance.get_details()
        #     pothole_instance.update_pothole()
            
        # for pothole_instance in potholes_list:
        #     update_segments(pothole_instance)
        # cursor_segments = db.segments.find()
        # segment_list = [Segment(**segment_data) for segment_data in cursor_segments]
        # print(f"==>> segment_list length: {len(segment_list)}")
        # for to_update_segment in segment_list:
        #     print(f"==>> to_update_segment: {str(to_update_segment._id)}")
        #     to_update_segment.get_segment_priority()
        #     db.segments.update_one({"_id": ObjectId(to_update_segment._id)}, {"$set": {key: value for key, value in to_update_segment.to_dict().items() if key != "_id"}})

        potholes_dict_list = [pothole.to_dict() for pothole in potholes_list]

        return jsonify(potholes_dict_list)

    @app.route("/segments")
    def segments():
        cursor_segments = db.segments.find()
        # print("Querying potholes from the database.")
        segment_list = [
        Segment(**segment_data) for segment_data in cursor_segments]
        segment_dict_list  = [segment.to_dict() for segment in segment_list]

        return jsonify(segment_dict_list)
    # START - DASHBOARD MODULE ----------------------------------------------------------------------------------------------------------
    @app.route("/")
    def home():
        role = session.get("role")
        fname = session.get("fname")
        lname = session.get("lname")
        contribcollection = db.contributions
        count = contribcollection.count_documents({"is_validated": 0})
        head_count = contribcollection.count_documents({"is_validated": 1, "head_validated": 0})
        if "email" in session and role and fname and lname:  # Ensure all session variables are present
            # Fetch total number of unvalidated potholes from MongoDB
            today = datetime.now().date()
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = datetime.combine(today, datetime.max.time())

            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            start_of_week_str = start_of_week.strftime("%Y-%m-%d")
            end_of_week_str = end_of_week.strftime("%Y-%m-%d")
            unvalidated_count = db.contributions.count_documents({"contribution_date": {"$gte": start_of_day, "$lt": end_of_day}, "is_validated": 0})
            duejoborders = db.segments.count_documents({
            "job_order.start_date": {
                "$gte": start_of_week_str,
                "$lte": end_of_week_str,
            },
            "job_order.status": "In Progress"  # Additional condition on job_order.status
            })
            recently_validated = db.contributions.count_documents({"validation_date": {"$gte": start_of_day, "$lt": end_of_day}, "is_validated": 1})

            # Fetch top 5 highest priority damaged road segments
            top_segments = db.segments.find().sort("priority_score", -1).limit(5)

            return render_template("home.html", role=role, fname=fname, lname=lname, unvalidated_count=unvalidated_count, recently_validated=recently_validated, top_segments=top_segments, contribcount=count, duejoborders=duejoborders, head_contribcount=head_count)
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not recaptcha_response:
            return render_template("login.html", site_key=app.config['RECAPTCHA_SITE_KEY'])

        # Verify reCAPTCHA response with Google
        data = {
            'secret': app.config['RECAPTCHA_SECRET_KEY'],
            'response': recaptcha_response
        }
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        if not response.json()['success']:
            return render_template("login.html", site_key=app.config['RECAPTCHA_SITE_KEY'], error="reCAPTCHA verification failed. Please try again.")
        flash("error", "You need to log in!")  # Flash an error message if user not logged in or session variables missing
        return render_template("login.html", site_key=app.config['RECAPTCHA_SITE_KEY'])


    
    @app.route("/priority_counts")
    def priority_counts():
        if "email" in session:
            # Fetch data from MongoDB
            segments_data = db.segments.aggregate([
                {"$match": {"job_order.status": {"$ne": "Resolved"}}},
                {"$group": {"_id": "$priority_level", "count": {"$sum": 1}}}
            ])
            # Prepare data for rendering the bar graph
            priority_counts = {doc["_id"]: doc["count"] for doc in segments_data}

            return jsonify(priority_counts)
        return jsonify({})
    # END - DASHBOARD MODULE ----------------------------------------------------------------------------------------------------------

    # START - USER SERVICES MODULE ----------------------------------------------------------------------------------------------------------
    @app.route("/login", methods=["GET", "POST"])
    @limiter.limit("2000 per hour")
    def login():
        if request.method == "POST":
            # Verify reCAPTCHA
            recaptcha_response = request.form.get('g-recaptcha-response')
            if not recaptcha_response:
                return render_template("login.html", site_key=app.config['RECAPTCHA_SITE_KEY'], error="Please complete the reCAPTCHA.")

            # Verify reCAPTCHA response with Google
            data = {
                'secret': app.config['RECAPTCHA_SECRET_KEY'],
                'response': recaptcha_response
            }
            response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
            if not response.json()['success']:
                return render_template("login.html", site_key=app.config['RECAPTCHA_SITE_KEY'], error="reCAPTCHA verification failed. Please try again.")

            user = db.user
            login_user = user.find_one(
                {"email": request.form["email"], "verified": True}
            )

            if login_user and check_password_hash(
                login_user["password"], request.form["password"]
            ):
                session["email"] = request.form["email"]
                session["role"] = login_user.get("role", "Contributor")
                session["fname"] = login_user.get("fname")
                session["lname"] = login_user.get("lname")
                session['_id'] = str(login_user.get("_id"))
                return redirect(url_for("home"))

            else: 
                flash("Invalid credentials!")  # Flash an error message
        return render_template("login.html", site_key=app.config['RECAPTCHA_SITE_KEY'])


    @app.route("/signup", methods=["GET", "POST"])
    @limiter.limit("2000 per hour")
    def signup():
        if request.method == "POST":
            # Verify reCAPTCHA
            recaptcha_response = request.form.get('g-recaptcha-response')
            if not recaptcha_response:
                return render_template("signup.html", error="Please complete the reCAPTCHA.", site_key=app.config['RECAPTCHA_SITE_KEY'])

            # Verify reCAPTCHA response with Google
            data = {
                'secret': app.config['RECAPTCHA_SECRET_KEY'],
                'response': recaptcha_response
            }
            response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
            if not response.json()['success']:
                return render_template("signup.html", error="reCAPTCHA verification failed. Please try again.", site_key=app.config['RECAPTCHA_SITE_KEY'])

            email = request.form["email"]
            fname = request.form["first_name"]
            lname = request.form["last_name"]
            password = request.form["password"]
            confirm_password = request.form["confirm_password"]
            honeypot = request.form.get('honeypot')
            if honeypot:
                return "Spam detected, submission blocked."
            else:
                if len(password) < 8:
                    return render_template(
                        "signup.html", site_key=app.config['RECAPTCHA_SITE_KEY'], error="Password must be at least 8 characters long, contain at least one number, and have a combination of uppercase and lowercase letters"
                    )

                if password != confirm_password:
                    return render_template("signup.html", site_key=app.config['RECAPTCHA_SITE_KEY'], error="Passwords do not match")

                if not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) \
                        or not re.search(r'[0-9]', password) or not re.search(r'[\W_]', password):
                    return render_template("signup.html", site_key=app.config['RECAPTCHA_SITE_KEY'], error="Password must meet complexity requirements (Must have at least one capital letter, one number, and one special character)")

                user = db.user
                existing_user = user.find_one({"email": request.form["email"]})

                if existing_user is None:
                    hash_pass = generate_password_hash(request.form["password"])

                    verification_token = secrets.token_urlsafe(20)

                    user.insert_one(
                        {
                            "email": request.form["email"],
                            "fname": fname,
                            "lname": lname,
                            "password": hash_pass,
                            "role": "Contributor",
                            "verified": False,
                            "verification_token": verification_token,
                        }
                    )

                    msg = Message(
                        "Verify Your Email",
                        sender="autopriority.classification.sys@gmail.com",
                        recipients=[request.form["email"]],
                    )
                    verification_link = url_for(
                        "verify", token=verification_token, _external=True
                    )
                    msg.body = f"Click the following link to verify your email: {verification_link}"
                    mail.send(msg)

                    return render_template("verification_prompt.html")
                else:
                    return render_template(
                        "signup.html",
                        error="Invalid! Account is already registered, please make sure it is verified", site_key=app.config['RECAPTCHA_SITE_KEY']
                    )
        return render_template("signup.html", site_key=app.config['RECAPTCHA_SITE_KEY'])

    @app.route("/logout")
    def logout():
        session.pop("email", None)
        session.pop("role", None)
        return redirect(url_for("home"))

    @app.route("/verify/<token>")
    def verify(token):
        user = db.user
        # Find the user with the verification token
        user_to_verify = user.find_one({"verification_token": token})

        if user_to_verify:
            # Update 'verified' to True and remove 'verification_token'
            user.update_one(
                {"_id": user_to_verify["_id"]},
                {"$set": {"verified": True}, "$unset": {"verification_token": 1}},
            )
            return render_template("verification_success.html")
        else:
            return render_template("verification_error.html")

    @app.route("/users", methods = ["POST", "GET"])
    @limiter.limit("1000 per hour")
    def user_dashboard():
        contribcollection = db.contributions
        count = contribcollection.count_documents({"is_validated": 0})
        head_count = contribcollection.count_documents({"is_validated": 1, "head_validated": 0})
        user_data = list(db.user.find())
        if request.method == "POST":
            for user in user_data:
                user['_id'] = str(user['_id'])
            return jsonify(user_data)
        if request.method == "GET":
            access = ["Admin"]
            role = session.get("role")
            if role == None:
                session.pop("email", None)
                return render_template("login.html")
            fname = session.get("fname")
            lname = session.get("lname")
            if has_access(session, access) == False:
                session.pop("email", None)
                return render_template("login.html")
            # Fetch all users from MongoDB
            userCollection = db.user
            user = userCollection.find()
            # Render the dashboard template with user data
            return render_template("users.html", user=user, role=role, fname=fname, lname=lname, contribcount=count, head_contribcount=head_count)

    @app.route("/add_user", methods=["GET", "POST"])
    @limiter.limit("1000 per hour")
    def add_user():
        access = ["Admin"]
        role = session.get("role")
        if role == None:
                session.pop("email", None)
                return render_template("login.html")
        fname = session.get("fname")
        lname = session.get("lname")
        contribcollection = db.contributions
        count = contribcollection.count_documents({"is_validated": 0})
        head_count = contribcollection.count_documents({"is_validated": 1, "head_validated": 0})
        if not has_access(session, access):
            session.pop("email", None)
            return render_template("login.html")

        if request.method == "POST":
            # Check if email already exists
            contribcollection = db.contributions
            count = contribcollection.count_documents({"is_validated": 0})
            head_count = contribcollection.count_documents({"is_validated": 1, "head_validated": 0})
            userCollection = db.user
            existing_user = userCollection.find_one({"email": request.form["email"]})
            if existing_user:
                return render_template(
                    "add_user.html",
                    role=role,
                    error="Email already exists. Please choose a different email.",
                )

            # Check if passwords match
            password = request.form["password"]
            confirm_password = request.form["confirm_password"]
            if password != confirm_password:
                flash("Passwords do not match. Please try again.", "error")
                return render_template(
                    "add_user.html", role=role, error="Passwords do not match!"
                )
            
            verification_token = secrets.token_urlsafe(20)
            # Add user to the database
            user_data = {
                "fname": request.form["fname"],
                "lname": request.form["lname"],
                "email": request.form["email"],
                "role": request.form["role"],
                "password": generate_password_hash(password),
                "verified": False, 
                "verification_token": verification_token
            }
            verification_link = url_for(
            "verify", token=verification_token, _external=True
            )
            send_email("Verify Your Email","autopriority.classification.sys@gmail.com",[request.form["email"]],f"Click the following link to verify your email: {verification_link}")
       

            userCollection.insert_one(user_data)
            flash("User added successfully.", "success")
            return redirect(url_for("user_dashboard"))

        return render_template("add_user.html", role=role, fname=fname, lname=lname, contribcount=count, head_contribcount=head_count)
    
    @app.route("/forgot_password", methods=["GET", "POST"])
    @limiter.limit("1000 per hour")
    def forgot_password():
        if request.method == "POST":
            email = request.form.get("email")
            user = db.user.find_one({"email": email})
            if user:
                # Generate a password reset token
                reset_token = secrets.token_urlsafe(20)
                # Update user document with reset token
                db.user.update_one({"email": email}, {"$set": {"forgot_password_token": reset_token}})
                # Send email with password reset link
                forgot_passwordlink = url_for(
                "reset_password", token=reset_token, _external=True
                )
                send_email("Reset Your Password on APCS", "autopriority.classification.sys@gmail.com", [request.form["email"]],f"Click the following link to reset your password: {forgot_passwordlink}")
               
                flash("Password reset link sent to your email.", "success")
                return redirect(url_for("login"))
            else:
                flash("User with this email does not exist.", "error")
                return redirect(url_for("forgot_password"))
        return render_template("forgot_password.html")
    
    @app.route("/reset_password/<token>", methods=["GET", "POST"])
    def reset_password(token):
        error = None  # Initialize error message variable
        if request.method == "POST":
            new_password = request.form.get("new_password")
            confirm_password = request.form.get("confirm_password")
            
            if len(new_password) < 8:
                error = "Password must be at least 8 characters long."
            elif new_password != confirm_password:
                error = "Passwords do not match. Please try again."
            else:
                # Proceed with password reset logic
                user = db.user.find_one({"forgot_password_token": token})
                if user:
                    # Update user's password with the new one
                    hashed_password = generate_password_hash(new_password)
                    db.user.update_one({"_id": user["_id"]}, {"$set": {"password": hashed_password}})
                    # Remove the reset token from the user document
                    db.user.update_one({"_id": user["_id"]}, {"$unset": {"forgot_password_token": 1}})
                    flash("Password reset successful. You can now login with your new password.", "success")
                    return redirect(url_for("login"))
                else:
                    error = "Invalid or expired reset token. Please try again."

        # Pass error message to the template
        return render_template("reset_password.html", error=error)

    @app.route("/edit_user/<user_id>", methods=["GET", "POST"])
    @limiter.limit("1000 per hour")
    def edit_user(user_id):
        access = ["Admin"]
        role = session.get("role")
        if role == None:
                session.pop("email", None)
                return render_template("login.html")
        fname = session.get("fname")
        lname = session.get("lname")
        contribcollection = db.contributions
        count = contribcollection.count_documents({"is_validated": 0})
        head_count = contribcollection.count_documents({"is_validated": 1, "head_validated": 0})
        if not has_access(session, access):
            session.pop("email", None)
            return render_template("login.html")

        userCollection = db.user
        user = userCollection.find_one({"_id": ObjectId(user_id)})

        if request.method == "POST":
            fname = request.form["fname"]
            lname = request.form["lname"]
            email = request.form["email"]
            role = request.form["role"]
            password = request.form["password"]

            if password and len(password) < 8:
                flash("Password must be at least 8 characters long.", "error")
                return redirect(url_for("edit_user", user_id=user_id))

            userCollection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "fname": fname,
                        "lname": lname,
                        "email": email,
                        "role": role,
                        "password": (
                            generate_password_hash(password)
                            if password
                            else user["password"]
                        ),
                    }
                },
            )
            return redirect(url_for("user_dashboard"))

        return render_template("edit_user.html", user=user, role=role, fname=fname, lname=lname, contribcount=count, head_contribcount=head_count)

    @app.route("/delete_user/<user_id>", methods=["POST"])
    @limiter.limit("1000 per hour")
    def delete_user(user_id):
        # Check if the user has the necessary access
        access = ["Admin"]
        if not has_access(session, access):
            return jsonify({"error": "Unauthorized"}), 403

        # Delete the user from the database
        userCollection = db.user
        userCollection.delete_one({"_id": ObjectId(user_id)})

        return jsonify({"message": "User deleted successfully"}), 200

    # END - USER SERVICES MODULE ----------------------------------------------------------------------------------------------------------
    # START - AUXILIARY PAGES -------------------------------------------------------------------------------------------------------------
    @app.route("/about")
    @limiter.limit("1000 per hour")
    def about():
        access = ["Admin", "Engineering", "Contributor" , "TPMO", "Engineering Head", "TPMO Head"]
        role = session.get("role")
        if role == None:
                session.pop("email", None)
                return render_template("login.html")
        fname = session.get("fname")
        lname = session.get("lname")
        if not has_access(session, access):
            session.pop("email", None)
            return render_template("login.html")
        contribcollection = db.contributions
        count = contribcollection.count_documents({"is_validated": 0})
        head_count = contribcollection.count_documents({"is_validated": 1, "head_validated": 0})
        return render_template("about.html", role=role, fname=fname, lname=lname, contribcount=count, head_contribcount=head_count)

    # Contact Us
    @app.route("/contactus")
    @limiter.limit("1000 per hour")
    def contactus():
        access = ["Admin", "Engineering", "Contributor" , "TPMO", "Engineering Head", "TPMO Head"]
        role = session.get("role")
        if role == None:
                session.pop("email", None)
                return render_template("login.html")
        fname = session.get("fname")
        lname = session.get("lname")
        if not has_access(session, access):
            session.pop("email", None)
            return render_template("login.html")
        contribcollection = db.contributions
        count = contribcollection.count_documents({"is_validated": 0})
        head_count = contribcollection.count_documents({"is_validated": 1, "head_validated": 0})
        return render_template("contactus.html", role=role, fname=fname, lname=lname, contribcount=count, head_contribcount=head_count)

    @app.route("/cfsubmission", methods=["POST"])
    @limiter.limit("1000 per hour")
    def cfsubmission():
        if request.method == "POST":
            # Retrieve form data
            name = request.form.get("name")
            email = request.form.get("email")
            message = request.form.get("message")
            honeypot = request.form.get('honeypot')

            # Check honeypot field
            if honeypot:
                # Terminate user session
                session.clear()
                return render_template("login.html")

            # Send submitted contact form to APCS email
            cf_email(name, email, message)

            # Redirect to form submission verification page
            return redirect(url_for("cf_success"))

    @app.route("/cf_success")
    def cf_success():
        access = ["Admin", "Engineering", "Contributor" , "TPMO", "Engineering Head", "TPMO Head"]
        role = session.get("role")
        if role == None:
                session.pop("email", None)
                return render_template("login.html")
        fname = session.get("fname")
        lname = session.get("lname")
        if not has_access(session, access):
            session.pop("email", None)
            return render_template("login.html")
        contribcollection = db.contributions
        count = contribcollection.count_documents({"is_validated": 0})
        head_count = contribcollection.count_documents({"is_validated": 1, "head_validated": 0})
        return render_template("contactus.html", role=role, fname=fname, lname=lname, contribcount=count, head_contribcount=head_count)


    def cf_email(name, email, message):
        subject = "Contact Us Form Submission"
        body = f"Name: {name}\nEmail: {email}\nMessage: {message}"
  

        msg = Message(
            subject, recipients=["autopriority.classification.sys@gmail.com"], body=body
        )

        mail.send(msg)

    # END - AUXILIARY PAGES -------------------------------------------------------------------------------------------------------------
    # START - CONTRIBUTION MODULE -------------------------------------------------------------------------------------------------------------


    def is_contribution_blank(image_path ):
        # Load the image
        black_pixel_threshold=10
        black_threshold=0.1
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Image not found or unable to load.")
        
        # Convert the image to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Compute the number of pixels that are close to black
        num_black_pixels = np.sum(gray < black_pixel_threshold)
        total_pixels = gray.shape[0] * gray.shape[1]
        pct_black_pixels = num_black_pixels / total_pixels
        
        # Check if the percentage of black pixels exceeds the threshold
        if pct_black_pixels > black_threshold:
            return True
        else:
            return False

    def is_contribution_duplicate(image_path):
        save_path = os.path.join(FRAMES_FOLDER, f"{image_path}.jpg")
        print()
        return os.path.exists(save_path)

 # Processing Frames
    def process_uploaded_files(video_file_path, gpx_file_path):
        print("process_uploaded_files start")
        username = session.get("fname") + session.get("lname")
        is_valid = validateVideo(video_file_path)
        csv_file = video_file_path.replace('.mp4', '.csv')
        object_detected_folder = os.path.join(SITE_ROOT, f"extractor/folder_objdet/images/")
        if not is_valid:
            print("Invalid video")
        else:
            gpx_file_path = match_starting_timestamp(gpx_file_path, video_file_path)
            datetime = extract_and_convert_to_philippine_time(gpx_file_path)
            print("match starting done")
            print("datetime",datetime)
            filenames = extractFrames(video_file_path, gpx_file_path, csv_file, username)
            print("Extract frame done")
            for filename in filenames:
                print(f"==>> type(filename): {type(filename)}")
                print(f"==>> filename: {filename}")
                coordinates = extract_coordinates(filename)
                if not is_in_mandaluyong(coordinates[0],coordinates[1]):
                    print("not in mandaluyong")
                    os.remove(object_detected_folder + filename)
            func_objdet(object_detected_folder,db, session.get("email"),datetime)

        # Optionally, delete uploaded files after processing
        os.remove(video_file_path)
        os.remove(gpx_file_path)

        return 1
    def extract_coordinates(filename):
        pattern = r'(\d+\.\d+),\s*(\d+\.\d+)'
        match = re.search(pattern, filename)
        if match:
            latitude = float(match.group(1))
            longitude = float(match.group(2))
            return latitude, longitude
        else:
            return None

    def process_video(mp4_file, gpx_file):
        # Upload MP4
        print("upload_contribution Upload MP4")
        mp4_filename = secure_filename(mp4_file.filename)
        mp4_file_path = os.path.join(SITE_ROOT, "static/videos", mp4_filename)
        mp4_file.save(mp4_file_path)

        # Upload GPX
        print("upload_contribution Upload GPX")
        gpx_filename = secure_filename(gpx_file.filename)
        gpx_file_path = os.path.join(SITE_ROOT, "static/gpx", gpx_filename)
        gpx_file.save(gpx_file_path)

        # Process uploaded files
        print("upload_contribution process_uploaded_files")
        result = process_uploaded_files(mp4_file_path, gpx_file_path)

        return result



    @app.route("/contribution")
    @limiter.limit("5000 per hour")
    def contribution():
        access = ["Admin", "Engineering", "Contributor" , "TPMO", "Engineering Head", "TPMO Head"]
        role = session.get("role")
        if role == None:
                session.pop("email", None)
                return render_template("login.html")
        fname = session.get("fname")
        lname = session.get("lname")
        if not has_access(session, access):
            session.pop("email", None)
            return render_template("login.html")
        contribcollection = db.contributions
        count = contribcollection.count_documents({"is_validated": 0})
        head_count = contribcollection.count_documents({"is_validated": 1, "head_validated": 0})
        return render_template("contribution.html", role=role, fname=fname, lname=lname, contribcount=count, head_contribcount=head_count)
    
    @app.route("/contribution/rfex_instruction")
    @limiter.limit("5000 per hour")
    def rfex_instruction():
        access = ["Admin", "Engineering", "Contributor" , "TPMO", "Engineering Head", "TPMO Head"]
        role = session.get("role")
        if role == None:
                session.pop("email", None)
                return render_template("login.html")
        fname = session.get("fname")
        lname = session.get("lname")
        if not has_access(session, access):
            session.pop("email", None)
            return render_template("login.html")
        return render_template("instructions.html", role=role, fname=fname, lname=lname)

    @app.route("/upload_contribution", methods=["POST"])
    @limiter.limit("5000 per hour")
    def upload_contribution():
        print("Start upload_contribution")
        if request.method == "POST":
            print("upload_contribution pass POST if")
            if "gpx_file" not in request.files or "mp4_file" not in request.files:
                print("upload_contribution fail request files")
                flash("No file part")
                return redirect(request.url)
            gpx_file = request.files["gpx_file"]
            mp4_file = request.files["mp4_file"]
            # If user does not select file, browser also
            # submit an empty part without filename
            if gpx_file.filename == "" or mp4_file.filename == "":
                print("upload_contribution fail request files")
                flash("No selected file")
                return redirect(request.url)
            # Call the process_video function
            print("upload_contribution start process_video")
            process_video(mp4_file, gpx_file)
            return redirect(url_for("contribution"))

        return render_template("contribution.html")

    @app.route("/check_if_in_mandaluyong", methods=["POST"])
    def check_if_in_mandaluyong():
        # Get latitude and longitude from the request JSON body
        data = request.json
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        print(latitude)
        print(longitude)

        data = get_barangay_polygons()

        for polygon in data:
            boundaries = shape(
                {"type": "Polygon", "coordinates": polygon["Coordinates"]}
            )
            name = polygon["NAME_03"]
            print(name)

            point_coordinates = Point(float(longitude), float(latitude))

            if boundaries.contains(point_coordinates):
                return {"message": "Location is in Mandaluyong"}, 200
        return {"message": "Location is not in Mandaluyong"}, 400
    
    def is_in_mandaluyong(latitude,longitude):

        print(latitude)
        print(longitude)

        data = get_barangay_polygons()

        for polygon in data:
            boundaries = shape(
                {"type": "Polygon", "coordinates": polygon["Coordinates"]}
            )
            name = polygon["NAME_03"]
            print(name)

            point_coordinates = Point(float(longitude), float(latitude))

            if boundaries.contains(point_coordinates):
                return True
        return False
    
    def hms_to_decimal_degrees(hours, minutes, seconds):
        # Calculate total seconds
        total_seconds = hours * 3600 + minutes * 60 + seconds

        # Calculate decimal degrees
        decimal_degrees = total_seconds / 3600.0

        return decimal_degrees
    def decimal_coords(coords, ref):
        decimal_degrees = coords[0] + coords[1] / 60 + coords[2] / 3600
        if ref == "S" or ref =='W' :
            decimal_degrees = -decimal_degrees
        return decimal_degrees
    def image_coordinates(image_path):
        with open(image_path, 'rb') as src:
            img = exifImage(src)
        if img.has_exif:
            try:
                img.gps_longitude
                coords = (decimal_coords(img.gps_latitude,
                        img.gps_latitude_ref),
                        decimal_coords(img.gps_longitude,
                        img.gps_longitude_ref))
            except AttributeError:
                print ('No Coordinates')
                return 1
                
        else:
            print ('The Image has no EXIF information')
            return 1
            
        print({"imageTakenTime":img.datetime_original, "geolocation_lat":coords[0],"geolocation_lng":coords[1]})
        return f"{coords[0]},{coords[1]}"

    @app.route("/non_rfex_upload", methods=["POST"])
    def upload_file():
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        # Save the uploaded file to a temporary location or process it as needed
        # For simplicity, we'll just use the filename

        # Get coordinates using your function
        coordinates = request.headers.get("coordinatesCheck")

        filename = file.filename
        file.save(filename)
        coordinates = image_coordinates(filename)
        print(f"==>> coordinates: {coordinates}")

        if is_contribution_blank(filename) :
            print('blankkkk')
            coordinates = -1
        if is_contribution_duplicate(coordinates):
            print('is_contribution_duplicate')
            coordinates = -1
   
        os.remove(filename)
        print(f"==>> coordinates test: {coordinates}")

        # print(f"coordinates:{coordinates}")

        # Return the coordinates in the response
        return jsonify({"coordinates": coordinates})

    @app.route("/non_rfex_upload/get_image_date" , methods =["POST"])
    def get_date_taken(path):
        exif = Image.open(path)._getexif()
        if not exif:
            return jsonify({"timestamp" : -1}), 404
        return jsonify({"timestamp" : exif[36867]}), 200
    @app.route('/extract_exif_date_time', methods=['POST'])
    def extract_exif_date_time():
        try:
            file = request.files['file']
            if file:
                img = Image.open(file)
                exif_data = img._getexif()
                if exif_data:
                    date_time_original = exif_data.get(36867)  # EXIF tag for DateTimeOriginal
                    if date_time_original:
                        return jsonify({"date_time": date_time_original})
                print("No EXIF data found in the image")
                return jsonify({"error": "No EXIF data found in the image"}), 400
            else:
                print("No file uploaded")
                return jsonify({"error": "No file uploaded"}), 400
        except Exception as e:
            print(str(e))
            return jsonify({"error": str(e)}), 500
    
    @app.route("/upload_non_rfex_contribution", methods=["POST", "GET"])
    def upload_non_rfex_contribution():
        access = ["Admin", "Engineering", "Contributor" , "TPMO", "Engineering Head", "TPMO Head"]
        action = request.form.get("action")
        coords = request.form.get("coords")
        timestamp = request.form.get("timeStamp")
        print(f"TIMESTAMP:{timestamp} ")
        email = session.get("email")
        role = session.get("role")
        if role == None:
                session.pop("email", None)
                return render_template("login.html")
        fname = session.get("fname")
        lname = session.get("lname")
        if not has_access(session, access):
            session.pop("email", None)
            return render_template("login.html")
        contribcollection = db.contributions
        count = contribcollection.count_documents({"is_validated": 0})
        head_count = contribcollection.count_documents({"is_validated": 1, "head_validated": 0})
        # print(f"upload{coords}")
        if request.method == "POST":
            if "non_rfex_image" not in request.files:
                flash("No file part")
                return redirect(request.url)
            if request.files["non_rfex_image"].filename == "":
                flash("No selected file")
                return redirect(request.url)
      
            save_path = os.path.join(FRAMES_FOLDER, f"{coords}.jpg")
            has_sidewalk = request.form.get("is_sidewalk")
            is_oneway = request.form.get("is_oneway")
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            if has_sidewalk is None or not has_sidewalk:
                has_sidewalk = False
            elif has_sidewalk == "on":
                has_sidewalk = True

            if is_oneway is None or not is_oneway:
                is_oneway = False
            elif is_oneway == "on":
                is_oneway = True
            image = Image.open(request.files["non_rfex_image"])
            # print(save_path)
            image.save(save_path)
            print(f"==>> save_path: {save_path}")
            coordinates_split = coords.split(",")
            print(coords)

                
            user_info = db.user.find_one(
                {"email": email}, {"_id": 0, "fname": 1, "lname": 1, "role": 1}
            )
            contribution_id = ObjectId()
            new_contribution = Contribution(_id = contribution_id, road_name=  coordinates_split[2].strip() if len(coordinates_split) >= 3 else reverse_geocode(coordinates_split[0], coordinates_split[1]) ,
            latitude=coordinates_split[0],
            longitude=coordinates_split[1],
            has_sidewalk=has_sidewalk,
            is_oneway=is_oneway,
            filename=f"{coords}.jpg".strip(),
            contributor_email=email,
            is_validated = 0,
            contributor_fname=user_info.get("fname", ""),
            contributor_lname=user_info.get("lname", ""),
            contributor_role=user_info.get("role", ""),
            contribution_date=datetime.now(),
            is_rfex=False,
            image_timestamp = timestamp
            )
            new_contribution.get_barangay()
            
            print(f"==>> new_contribution: {new_contribution.road_name}")



            db.contributions.insert_one({key: value for key, value in new_contribution.to_dict().items() if key != "_id"})
            return redirect("/contribution")

        return redirect("/contribution")

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

    @app.route("/coordinates", methods=["POST"])
    def process_coordinates():
        try:
            data = request.get_json()
            lat = data.get("lat")
            lng = data.get("lng")


            street = reverse_geocode(lat, lng)

            return jsonify({"lat": lat, "lng": lng, "street": street})

        except Exception as e:
            return jsonify({"error": "Failed to process coordinates"}), 500

    # END - UPLOAD/TAKE PICTURE MODULE
    # END - CONTRIBUTION MODULE -------------------------------------------------------------------------------------------------------------
    # START - EXPLORE MODULE ----------------------------------------------------------------------------------------------------------------
    @app.route("/explore")
    @limiter.limit("5000 per hour")
    def explore():
        access = ["Admin", "Engineering", "Contributor" , "TPMO", "Engineering Head", "TPMO Head"]
        role = session.get("role")
        if role == None:
                session.pop("email", None)
                return render_template("login.html")
        fname = session.get("fname")
        lname = session.get("lname")
        user_id = session.get("_id")
        print(f"==>> user_id: {user_id}")
        
        contribcollection = db.contributions
        count = contribcollection.count_documents({"is_validated": 0})
        head_count = contribcollection.count_documents({"is_validated": 1, "head_validated": 0})
        if has_access(session, access) == False:
            session.pop("email", None)
            return render_template("login.html")
        return render_template("explore.html", role=role,user_id = user_id, fname=fname, lname=lname, mapbox_access_token=mapbox_access_token, contribcount=count, head_contribcount=head_count)
    
    @app.route('/explore/<segment_id>')
    @limiter.limit("5000 per hour")
    def view_explore(segment_id):
        access = ["Admin", "Engineering", "Contributor", "TPMO", "Engineering Head", "TPMO Head"]
        role = session.get("role")
        if role == None:
                session.pop("email", None)
                return render_template("login.html")
        fname = session.get("fname")
        lname = session.get("lname")
        user_id = session.get("_id")
        contribcollection = db.contributions
        count = contribcollection.count_documents({"is_validated": 0})
        head_count = contribcollection.count_documents({"is_validated": 1, "head_validated": 0})
        if has_access(session, access) == False:
            session.pop("email", None)
            return render_template("login.html")
        
        return render_template("explore.html", role=role,user_id = user_id, fname=fname, lname=lname, mapbox_access_token=mapbox_access_token, contribcount=count, head_contribcount=head_count, segment_id = segment_id)
    @app.route('/get_segment/<segment_id>')
    def get_segment(segment_id):
        if segment_id is not None:
            segment = db.segments.find_one({'_id' : ObjectId(segment_id)})
            segment['_id'] = segment_id
        return jsonify(segment)
    
    @app.route('/explore/submit_job_order', methods=['POST'])
    def submit_job_order():
        if request.method == 'POST':
            # Get the form data
            segment_id = request.form.get('segmentId')
            print(f"==>> segment_id: {segment_id}")
            start_date = request.form.get('startDate')
            print(f"==>> start_date: {start_date}")
            completion_date = request.form.get('completionDate')
            print(f"==>> completion_date: {completion_date}")
            person_responsible = request.form.get('personResponsible')
            print(f"==>> person_responsible: {person_responsible}")
            reason = request.form.get('editReason')

            from_where = request.form.get('fromWhere')
            
            segment = db.segments.find_one(
                {"_id": ObjectId(segment_id)},
            )
            if segment:
                barangays_affected = ', '.join(segment.get('barangays_affected', []))
                roads_affected = ', '.join(segment.get('roads_affected', []))
                priority_score = segment.get('priority_score')
                priority_level = segment.get('priority_level')
                person = db.user.find_one(
                {"_id": ObjectId(person_responsible)},
                )
                person_responsible_email = person.get('email')

            contributor_list = get_contributors_from_segment(segment_id)
            
            send_email("[APCS] Reported Pothole Under Repair",
                       "autopriority.classification.sys@gmail.com",
                       contributor_list,
                       f"Your Reported Pothole on Streets: {roads_affected} and Barangays: {barangays_affected} with a Priority Score of {priority_score} ({priority_level}) is currently under repair! (Start Date: {start_date} | Completion Date: {completion_date})"
            )
            
            send_email("[APCS] Your Job Order Was Successfully Created",
                       "autopriority.classification.sys@gmail.com",
                       [session.get("email")],
                       f"Your Job Order on Streets: {roads_affected} and Barangays: {barangays_affected} with a Priority Score of {priority_score} ({priority_level}) was successfully created! (Start Date: {start_date} | Completion Date: {completion_date})"
            )

            send_email( "[APCS] A Job Order Was Assigned to You",
                       "autopriority.classification.sys@gmail.com",
                        [person_responsible_email],
                        f"Your Job Order on Streets: {roads_affected} and Barangays: {barangays_affected} with a Priority Score of {priority_score} ({priority_level}) was successfully created! (Start Date: {start_date} | Completion Date: {completion_date})")
      

            print(segment['job_order']['status'])
            if segment['job_order']['status'] == "None" or segment['job_order']['status'] is None:
                new_job_order = JobOrder(start_date,completion_date,person_responsible,'In Progress',None,None,None,None)
                db.segments.update_one(
                {"_id": ObjectId(segment_id)},
                {"$set": {
                    'job_order': new_job_order.to_dict()
                }}
            )
            else:
                edit_job_order = JobOrder(segment['job_order']['start_date'],segment['job_order']['completion_date'],segment['job_order']['person_responsible'],'For Approval',reason,person_responsible,start_date,completion_date)
                db.segments.update_one(
                {"_id": ObjectId(segment_id)},
                {"$set": {
                    'job_order': edit_job_order.to_dict()
                }})
                engineering_head = db.user.find(
                {"role": "Engineering Head"},
                {"_id": 0, "email": 1}
                )
                
                engineering_head_emails = [user['email'] for user in engineering_head]
    
                send_email("[APCS] New Pending Job Order Edit Request",
                           "autopriority.classification.sys@gmail.com",
                            engineering_head_emails,
                             f"Job Order for segment {segment_id} has a pending request for edit. Please review in the explore or job order tab."
                           )
                
            if from_where == "explore":
                return redirect(url_for("explore"))
            else:
                return redirect(url_for("job_order_list"))
        

            
    @app.route('/explore/cancel_job_order', methods=['POST'])
    def cancel_job_order():
        # Get jobOrderId from request data
        data = request.json
        job_order_id = data.get('jobOrderId')
        collection = db.segments
        # Find the document by ID and update the fields inside the job_order object to null
        updated_job_order = collection.find_one_and_update(
            {'_id': ObjectId(job_order_id)},
            {'$set': {'job_order.start_date': None, 'job_order.completion_date': None, 'job_order.person_responsible': None, 'job_order.status': None}},
            return_document=True
        )
        if updated_job_order:
            # Job order successfully cancelled
            return jsonify({'success': True, 'message': 'Job order cancelled successfully'})
        else:
            # Job order not found or failed to cancel
            return jsonify({'success': False, 'message': 'Failed to cancel job order'}), 404
        
    def resolve_segment_transaction(session, segment_id):
        db.segments.update_one(
            {"_id": ObjectId(segment_id)},
            {"$set": {
                'job_order.status': 'Resolved'
            }},
            session=session
        )
        update_segment_priority(segment_id)
    @app.route('/explore/approve_edit', methods=['POST'])
    def approve_job_order_edit():
        if request.method == 'POST':
            # Get the form data
            data = request.json
            segment_id = data.get('segmentId')
            segment = db.segments.find_one(
                {"_id": ObjectId(segment_id)},
            )
            person_responsible = segment['job_order']['person_responsible']
            barangays_affected = ', '.join(segment.get('barangays_affected', []))
            roads_affected = ', '.join(segment.get('roads_affected', []))
            priority_score = segment.get('priority_score')
            priority_level = segment.get('priority_level')
            person = db.user.find_one(
                {"_id": ObjectId(person_responsible)},
                )
            person_responsible_email = person.get('email')
            if segment:
                new_job_order = JobOrder(segment['job_order']['edit_start_date'],segment['job_order']['edit_completion_date'],segment['job_order']['edit_person_responsible'],'In Progress',None,None,None,None)
                db.segments.update_one(
                {"_id": ObjectId(segment_id)},
                {"$set": {
                    'job_order': new_job_order.to_dict()
                }}
            )
                new_segment = db.segments.find_one(
                {"_id": ObjectId(segment_id)},
            )
                send_email("[APCS] Job_Order Reschedule Approved",
                       "autopriority.classification.sys@gmail.com",
                       [person_responsible_email],
                       f"Your Request for Reschedule for the Job Order on Pothole on Streets: {roads_affected} and Barangays: {barangays_affected} with a Priority Score of {priority_score} ({priority_level}) has been approved!"
                )     
        return redirect(url_for("explore"))
    @app.route('/explore/disapprove_edit', methods=['POST'])
    def disapprove_job_order_edit():
        if request.method == 'POST':
            
        # Get the form data
            data = request.json
            segment_id = data.get('segmentId')
            reason = data.get('reason')
            print(f"==>> segment_id: {segment_id}")
            segment = db.segments.find_one(
               
                {"_id": ObjectId(segment_id)},
            )
            person_responsible = segment['job_order']['person_responsible']
            barangays_affected = ', '.join(segment.get('barangays_affected', []))
            roads_affected = ', '.join(segment.get('roads_affected', []))
            priority_score = segment.get('priority_score')
            priority_level = segment.get('priority_level')
            person = db.user.find_one(
                {"_id": ObjectId(person_responsible)},
                )
            person_responsible_email = person.get('email')
            print(person_responsible_email)
            print(f"==>> segment: {segment}")
            if segment:
                new_job_order = JobOrder(segment['job_order']['start_date'],segment['job_order']['completion_date'],segment['job_order']['person_responsible'],'In Progress',None,None,None,None)
                db.segments.update_one(
                {"_id": ObjectId(segment_id)},
                {"$set": {
                    'job_order': new_job_order.to_dict()
                }}
            )
            send_email("[APCS] Job_Order Reschedule Disapproved",
                       "autopriority.classification.sys@gmail.com",
                       [person_responsible_email],
                       f"Your Request for Reschedule for the Job Order on Pothole on Streets: {roads_affected} and Barangays: {barangays_affected} with a Priority Score of {priority_score} ({priority_level}) has been disapproved! Reason: {reason}"
                )
        return redirect(url_for("explore"))

    
        
    def get_contributors_from_segment(segment_id):
            potholes = db.potholes.find({"segment_id": ObjectId(segment_id)})
            potholes_list = [
            Pothole(**pothole_data) for pothole_data in potholes]
            print(potholes_list)
            cursor_contributions = db.contributions.find()
            contribution_list = [
                Contribution(**contribution_data)
                for contribution_data in cursor_contributions
            ]
            contributor_list = []
            # THIS IS VERY UGLY AND SLOW
            for pothole in potholes_list:
                for contribution in contribution_list:
                    if str(pothole.contribution_id) == str(contribution._id):
                        if contribution.contributor_email not in contribution_list:
                            contributor_list.append(contribution.contributor_email)   
      
            return contributor_list
        
    @app.route('/explore/get_person_responsible/<user_id>')
    def get_person_responsible(user_id):
        print(f"==>> user_id: {user_id}")
        if user_id:
            user = db.user.find_one({"_id": ObjectId(user_id)})
            if user:
                user_dict = {
                    "fname": user["fname"],
                    "lname": user["lname"],
                    "email": user["email"],
                    "role": user["role"],
                    # Add other fields as needed
                }
                return jsonify(user_dict), 200
            else:
                return jsonify({"error": "User not found"}), 404
        else:
            return jsonify({"error": "User ID not provided"}), 400

                
        
    @app.route('/explore/resolve', methods=['POST'])
    def resolve_segment():
        if request.method == 'POST':
            data = request.json  # Get JSON data from the request body
            segment_id = data.get('segmentId')  # Retrieve segmentId from JSON data
            if segment_id:
                print(f"==>> segment_id: {segment_id}")
                contributor_list = get_contributors_from_segment(segment_id)
                print("Contributors: ",contributor_list)
                try:
                    with client.start_session() as session:
                        session.start_transaction()
                        resolve_segment_transaction(session, segment_id)
                        session.commit_transaction()
                    print("Succesful resolution")
                    segment = db.segments.find_one(
                    {"_id": ObjectId(segment_id)},
                    )
                    if segment:
                        barangays_affected = ', '.join(segment.get('barangays_affected', []))
                        roads_affected = ', '.join(segment.get('roads_affected', []))
                        priority_score = segment.get('priority_score')
                        priority_level = segment.get('priority_level')
                        person_responsible = segment['job_order']['person_responsible']
                        person = db.user.find_one(
                        {"_id": ObjectId(person_responsible)},
                        )
                        person_responsible_email = person.get('email')
                    send_email(
                        "[APCS] Reported Pothole Repair",
                        "autopriority.classification.sys@gmail.com",
                        contributor_list,
                        f"The pothole you reported on Streets: {roads_affected} and Barangays: {barangays_affected} with a Priority Score of {priority_score} ({priority_level}) was successfully repaired!"
                    )
                    send_email(
                        "[APCS] Job Order Successfully Resolved",
                        "autopriority.classification.sys@gmail.com",
                        [person_responsible_email],
                        f"Your Assigned Job Order on Streets: {roads_affected} and Barangays: {barangays_affected} with a Priority Score of {priority_score} ({priority_level}) was successfully resolved!"
                    )
                    return jsonify({'message': 'Segment resolved successfully'}), 200
                except ConnectionFailure:
                    print("error': 'Database connection error'")
                    return jsonify({'error': 'Database connection error'}), 500
                except Exception as e:
                    print({'error': str(e)})
                    return jsonify({'error': str(e)}), 500
            else:
                return jsonify({'error': 'SegmentId not provided'}), 400
        else:
            return jsonify({'error': 'Invalid request method'}), 405
        
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
    @app.route('/boundary', methods=['GET'])
    def get_boundary():
        json_url = "static/data/boundary_mandaluyong.json"
        with open(json_url, "r", encoding="utf-8") as file:
            data = json.load(file)
            return jsonify(data)

    # END - EXPLORE MODULE ------------------------------------------------------------------------------------------------------------------
    # START - QUALITY CONTROL MODULE ------------------------------------------------------------------------------------------------------------------
    @app.route("/qualitycontrol/contributions")
    @limiter.limit("5000 per hour")
    def tpmo_load_contributions():
        session.pop("contributions", None)
        # cursor_contributions = list(db.contributions.find({}, {'_id': 0}))
        cursor_contributions = db.contributions.find()
        # print("Querying contributions from the database.")
        contribution_list = [
            Contribution(**contribution_data)
            for contribution_data in cursor_contributions
        ]
        contributions = [contribution.to_dict() for contribution in contribution_list]
        return jsonify(contributions)
    @app.route("/qualitycontrol/approved_potholes")
    @limiter.limit("5000 per hour")
    def get_approved_potholes():
        try:
            # Find all approved potholes
            approved_potholes = db.potholes.find()
            filtered_potholes = []
            for pothole in approved_potholes:
                segment_id = pothole.get("segment_id")
                if segment_id:
                    segment = db.segments.find_one({"_id": segment_id})
                    if segment:
                        job_order = db.segments.find_one({"_id": segment_id, "job_order.start_date": {"$eq": None}})
                        if job_order:
                            filtered_potholes.append(pothole)

            # Convert the cursor to a list of dictionaries
            potholes_list = [
            Pothole(**pothole_data) for pothole_data in filtered_potholes]
            potholes_dict_list = [pothole.to_dict() for pothole in potholes_list]
            return jsonify(potholes_dict_list), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
    @app.route("/qualitycontrol/validate", methods=["POST"])
    def tpmo_validate_contribution():
        data = request.json
        action = data.get("action")
        contribution_id = data.get("contributionId")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        filename = data.get("filename")
        has_sidewalk = data.get("hasSidewalk")
        is_oneway = data.get("is_oneway")
        traffic_volume = data.get("trafficVolume")
        reason = data.get("reason")

        email = session.get("email")
        user_info = db.user.find_one(
            {"email": email}, {"_id": 0, "fname": 1, "lname": 1, "role": 1}
        )

        if action == "approve":
            try:
                with client.start_session() as transaction:
                    transaction.start_transaction()
                    tpmo_update_approved_contribution(contribution_id, latitude, longitude, filename, has_sidewalk, traffic_volume, user_info, is_oneway)
                    transaction.commit_transaction()
                print("Succesful resolution")
                return jsonify({'message': 'Segment resolved successfully'}), 200
            except ConnectionFailure:
                print("error': 'Database connection error'")
                return jsonify({'error': 'Database connection error'}), 500
            except Exception as e:
                print({'error': str(e)})
                return jsonify({'error': str(e)}), 500
            
            return jsonify({"status": "success", "message": "Contribution approved"})
        else:
            db.contributions.update_one(
                {"_id": ObjectId(contribution_id)},
                {
                    "$set": {
                        "is_validated": -1,
                        "validation_date": datetime.now(),
                        "disapproval_reason": reason,
                    }
                },
            )
            contribution = db.contributions.find_one({"_id": ObjectId(contribution_id)})
            if contribution:
                contributor_street = contribution.get("road_name")
                contributor_brgy = contribution.get("barangay")
                contributor_email = contribution.get("contributor_email")
            
            send_email("[APCS] Your Contribution Was Disapproved",
                       "autopriority.classification.sys@gmail.com",
                       [contributor_email],
                       f"Your contribution on {contributor_street} on Brgy. {contributor_brgy} was disapproved. Reason: {reason}"
                       )
            contribution = db.contributions.find_one({"_id": ObjectId(contribution_id)}, {"filename": 1})
            if not contribution:
                return jsonify({'error': 'Contribution not found'}), 404
            
            filenamee = contribution.get("filename")
            print(filenamee)
            if filenamee:
                file_path = os.path.join(SITE_ROOT, "static/frames", filenamee)
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"File {filenamee} deleted successfully.")
                    else:
                        print(f"File {filenamee} not found.")
                except Exception as e:
                    print(f"Error deleting file {filenamee}: {str(e)}")
                    return jsonify({'error': f"Error deleting file {filenamee}: {str(e)}"}), 500


            return jsonify({"status": "success", "message": "Contribution disapproved"})

    def update_approved_contribution(contribution_id, latitude, longitude, filename, has_sidewalk, traffic_volume, user_info, reason, is_oneway):
        print("update_approved_contribution START")
        db.contributions.update_one(
                {"_id": ObjectId(contribution_id)},
                {
                    "$set": {
                        "head_validated": 1,
                        "validation_date": datetime.now(),
                    }
                },
            )
        print("update_approved_contribution after update one")
        contribution = db.contributions.find_one({"_id": ObjectId(contribution_id)})
        print("update_approved_contribution after find one")
        if contribution:
            contributor_street = contribution.get("road_name")
            contributor_brgy = contribution.get("barangay")
            contributor_email = contribution.get("contributor_email")
            print("update_approved_contribution before send email")
        send_email(  "[APCS] Your Contribution Was Approved",
                   "autopriority.classification.sys@gmail.com",
                   [contributor_email],
                   f"Your contribution on {contributor_street} on Brgy. {contributor_brgy} was approved and is viewable on the Explore tab. Thank you for your contribution!"
                   )

        point = snap_to_roads([{"latitude": latitude, "longitude": longitude}])
        print(f"==>> point: {point}")

        for snapped_point in point:
            print(f"==>> snapped_point: {snapped_point}")
            latitude = snapped_point["location"]["latitude"]
            print(f"==>> latitude: {latitude}")
            longitude = snapped_point["location"]["longitude"]
            print(f"==>> longitude: {longitude}")
                # print(f"Latitude: {latitude}, Longitude: {longitude}")

        result = db.potholes.insert_one(
 
            
                {
                    "contribution_id": contribution_id,
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                    "filename": filename,
                    "has_sidewalk": has_sidewalk,
                    "is_oneway": is_oneway,
                    "traffic_volume": traffic_volume,
                }
            )
        print(f"==>> result: {result}")# VERY IMPORTANT TO ADD A LOADING SCREEN HERE
        pothole = db.potholes.find_one({"_id": ObjectId(result.inserted_id)})
        print(f"==>> pothole: {pothole}")
        pothole =  Pothole(**pothole) 
        print(f"==>> pothole2: {pothole}")
        pothole.get_details()
        print("GET DETAILS")
        pothole.update_pothole()
        print("update_pothole()")
        print('HAFDHAFHAHAHA')
        segment_id = update_segments(pothole)
       
        print(f"==>> ID HEREE: {segment_id}")   
        update_segment_priority(segment_id)

    def tpmo_update_approved_contribution(contribution_id, latitude, longitude, filename, has_sidewalk, traffic_volume, user_info, is_oneway):
        print("tpmo has approved")
        db.contributions.update_one(
                {"_id": ObjectId(contribution_id)},
                {
                    "$set": {
                        "is_validated": 1,
                        "head_validated": 0,
                        "validation_date": datetime.now(),
                        "validator_fname": user_info.get("fname", ""),
                        "validator_lname": user_info.get("lname", ""),
                        "traffic_volume": traffic_volume,
                    }
                },
            )

    def update_segment_priority(segment_id):
        print(f"==>> segment_id: {segment_id}")
        if segment_id:  
            cursor_segments = db.segments.find({"job_order.status": {"$ne": "Resolved"}})
            segment_list = [Segment(**segment_data) for segment_data in cursor_segments]
            print(f"==>> segment_list length: {len(segment_list)}")
            # Calculate the maximum values from the segment_list
            max_population_density = max(segment.population_density for segment in segment_list)
            print(f"==>> max_population_density: {max_population_density}")

            max_num_business_establishments = max(len(segment.nearby_establishments) for segment in segment_list)
            print(f"==>> max_num_business_establishments: {max_num_business_establishments}")

            max_num_potholes = max(len(segment.points) for segment in segment_list)
            print(f"==>> max_num_potholes: {max_num_potholes}")
            print()
            for segment in segment_list:
                print(f"==>> segment: {segment._id}")
                if segment_id == segment._id:
                    print(f"==>> segment: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
                    segment.get_segment_priority(segment_list)
                    db.segments.update_one(
                                        {"_id": ObjectId(segment._id)},
                                        {"$set": {key: value for key, value in segment.to_dict().items() if key != "_id"}}
                    )
                    
                    if len(segment.nearby_establishments) >= max_num_business_establishments or len(segment.points) >= max_num_potholes or segment.population_density >= max_population_density:
                            print("algo slow start")
                            engineering = db.user.find(
                            {"role": "Engineering"},
                            {"_id": 0, "email": 1}
                            )
                            
                            engineering_emails = [user['email'] for user in engineering]
                
                            send_email("[APCS] Damaged Road Priority Values Have Updated",
                                    "autopriority.classification.sys@gmail.com",
                                        engineering_emails,
                                        f"Damaged Road Segment Priority Values have been changed because of a new/updated segment. Please review accordingly."
                                    )
                            for to_update_segment in segment_list:
                                print(f"==>> to_update_segment: {str(to_update_segment._id)}")
                                to_update_segment.get_segment_priority(segment_list)
                                db.segments.update_one(
                                        {"_id": ObjectId(to_update_segment._id)},
                                        {"$set": {key: value for key, value in to_update_segment.to_dict().items() if key != "_id"}}
                    )

                    

           
            
       
    @app.route("/qualitycontrol")
    @limiter.limit("5000 per hour")
    def qualitycontrol():
        access = ["Admin", "TPMO"]
        role = session.get("role")
        if role == None:
                session.pop("email", None)
                return render_template("login.html")
        fname = session.get("fname")
        lname = session.get("lname")
        contribcollection = db.contributions
        count = contribcollection.count_documents({"is_validated": 0})
        head_count = contribcollection.count_documents({"is_validated": 1, "head_validated": 0})
        if has_access(session, access) == False:
            session.pop("email", None)
            return render_template("login.html")
        return render_template("qualitycontrol.html", role=role, fname=fname, lname=lname, contribcount=count, head_contribcount=head_count)

    # TPMO HEAD FUNCTIONALITIES

    @app.route("/head_qualitycontrol")
    @limiter.limit("5000 per hour")
    def head_qualitycontrol():
        access = ["Admin", "TPMO Head"]
        role = session.get("role")
        if role == None:
                session.pop("email", None)
                return render_template("login.html")
        fname = session.get("fname")
        lname = session.get("lname")
        contribcollection = db.contributions
        count = contribcollection.count_documents({"is_validated": 0})
        
        head_count = contribcollection.count_documents({"is_validated": 1, "head_validated": 0})
        if has_access(session, access) == False:
            session.pop("email", None)
            return render_template("login.html")
        return render_template("head_qualitycontrol.html", role=role, fname=fname, lname=lname, contribcount=count, head_contribcount=head_count)
    
    @app.route("/head_qualitycontrol/contributions")
    @limiter.limit("5000 per hour")
    def load_contributions():
        session.pop("contributions", None)
        # cursor_contributions = list(db.contributions.find({}, {'_id': 0}))
        cursor_contributions = db.contributions.find()
        # print("Querying contributions from the database.")
        contribution_list = [
            Contribution(**contribution_data)
            for contribution_data in cursor_contributions
        ]
        contributions = [contribution.to_dict() for contribution in contribution_list]
        return jsonify(contributions)
    
    @app.route("/head_qualitycontrol/validate", methods=["POST"])
    def validate_contribution():
        data = request.json
        action = data.get("action")
        contribution_id = data.get("contributionId")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        filename = data.get("filename")
        has_sidewalk = data.get("hasSidewalk")
        is_oneway = data.get("is_oneway")
        traffic_volume = data.get("trafficVolume")
        reason = data.get("reason")

        email = session.get("email")
        user_info = db.user.find_one(
            {"email": email}, {"_id": 0, "fname": 1, "lname": 1, "role": 1}
        )

        if action == "approve":
            try:
                with client.start_session() as transaction:
                    transaction.start_transaction()
                    print("APPPPPPROOOOOVEEEEEE")
                    update_approved_contribution(contribution_id, latitude, longitude, filename, has_sidewalk, traffic_volume, user_info, reason, is_oneway)
                    transaction.commit_transaction()
                print("Succesful resolution")
                return jsonify({'message': 'Segment resolved successfully'}), 200
            except ConnectionFailure:
                print("error': 'Database connection error'")
                return jsonify({'error': 'Database connection error'}), 500
            except Exception as e:
                print({'error': str(e)})
                return jsonify({'error': str(e)}), 500
            
            return jsonify({"status": "success", "message": "Contribution approved"})
        else:
            db.contributions.update_one(
                {"_id": ObjectId(contribution_id)},
                {
                    "$set": {
                        "head_validated": -1,
                        "is_validated": -1,
                        "disapproval_reason": reason,
                    }
                },
            )
            contribution = db.contributions.find_one({"_id": ObjectId(contribution_id)})
            if contribution:
                contributor_street = contribution.get("road_name")
                contributor_brgy = contribution.get("barangay")
                contributor_email = contribution.get("contributor_email")
            send_email("[APCS] Your Contribution Was Disapproved","autopriority.classification.sys@gmail.com",[contributor_email],f"Your contribution on {contributor_street} on Brgy. {contributor_brgy} was disapproved. Reason: {reason}")

            contribution = db.contributions.find_one({"_id": ObjectId(contribution_id)}, {"filename": 1})
            if not contribution:
                return jsonify({'error': 'Contribution not found'}), 404
            
            filenamee = contribution.get("filename")
            print(filenamee)
            if filenamee:
                file_path = os.path.join(SITE_ROOT, "static/frames", filenamee)
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"File {filenamee} deleted successfully.")
                    else:
                        print(f"File {filenamee} not found.")
                except Exception as e:
                    print(f"Error deleting file {filenamee}: {str(e)}")
                    return jsonify({'error': f"Error deleting file {filenamee}: {str(e)}"}), 500
                
            return jsonify({"status": "success", "message": "Contribution disapproved"})
    # END - QUALITY CONTROL MODULE ------------------------------------------------------------------------------------------------------------------
    # START - REPORTS MODULE ----------------------------------------------------------------------------------------------------------------
    @app.route("/reports", methods=["GET", "POST"])
    @limiter.limit("3000 per hour")
    def reports():
        access = ["Admin", "TPMO", "Engineering", "Engineering Head", "TPMO Head"]
        role = session.get("role")
        if role == None:
                session.pop("email", None)
                return render_template("login.html")
        fname = session.get("fname")
        lname = session.get("lname")
        contribcollection = db.contributions
        count = contribcollection.count_documents({"is_validated": 0})
        head_count = contribcollection.count_documents({"is_validated": 1, "head_validated": 0})
        if has_access(session, access) == False:
            session.pop("email", None)
            return render_template("login.html")

        return render_template("reports.html", role=role, fname=fname, lname=lname, contribcount=count, head_contribcount=head_count)
    

    @app.route("/generate_report", methods=["POST"])
    def generate_report():
        role = session.get("role")
        if role == None:
                session.pop("email", None)
                return render_template("login.html")
        fname = session.get("fname")
        lname = session.get("lname")
        audit_collection = db.audit
        contribution_collection = db.contributions
        contribcollection = db.contributions
        count = contribcollection.count_documents({"is_validated": 0})
        
        head_count = contribcollection.count_documents({"is_validated": 1, "head_validated": 0})
        # Get form data
        start_date_str = request.form["start_date"]
        end_date_str = request.form["end_date"]
        report_type = int(request.form["report_type"])
        # Convert start and end date strings to datetime objects
        
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        # Define filter criteria only for "Contributed Road Damages" report (option 4)
        if report_type == 1:
            filter_criteria = {
                "timestamp": {"$gte": start_date, "$lte": end_date},
                "collectionName": "segments",  # Filter by collectionName "contributions"
                "jo_status": "complete",
                "operationType": "update",
                "details.job_order.completion_date": {"$ne": ""}
            }

            # Fetch documents from audit collection based on filter criteria
            contributions = list(audit_collection.find(filter_criteria))
            
            processed_contributions = []
            
            for contribution in contributions:
                if "details" in contribution:
                    user_collection = db.user
                    user = user_collection.find_one({"_id": ObjectId(contribution["details"]["job_order"]["person_responsible"])})
                    first_name = user.get("fname", "")
                    last_name = user.get("lname", "")
                    contribcollection = db.contributions
                    count = contribcollection.count_documents({"is_validated": 0})
                    head_count = contribcollection.count_documents({"is_validated": 1, "head_validated": 0})
                    road_names = ", ".join(contribution["details"]["roads_affected"]) if "roads_affected" in contribution["details"] else ""
                    barangays = ", ".join(contribution["details"]["barangays_affected"]) if "barangays_affected" in contribution["details"] else ""
                    processed_detail = {
                            "startdate": str(contribution["details"]["job_order"]["start_date"]),
                            "enddate": str(contribution["details"]["job_order"]["completion_date"]),
                            "road_name": road_names,
                            "barangay": barangays,
                            "incharge": str(f"{first_name} {last_name}"),
                            "prio": str(contribution["details"]["priority_level"])
                        }
                    processed_contributions.append(processed_detail)
            # Pass the processed contributions data to the frontend for display
        if report_type == 2:
            segments = db.segments
            filter_criteria = {
                "job_order.start_date": None,
                "job_order.completion_date": None
            }

            # Fetch documents from audit collection based on filter criteria
            contributions = list(segments.find(filter_criteria))
            
            processed_contributions = []
            
            for contribution in contributions:
                road_names = ", ".join(contribution["roads_affected"]) if "roads_affected" in contribution else ""
                barangays = ", ".join(contribution["barangays_affected"]) if "barangays_affected" in contribution else ""
                processed_detail = {
                        "road_name": road_names,
                        "barangay": barangays,
                        "prio": str(contribution["priority_level"])
                    }
                processed_contributions.append(processed_detail)
            # Pass the processed contributions data to the frontend for display
        if report_type == 3:
            segments = db.segments
            filter_criteria = {
                "job_order.completion_date": ""
            }

            # Fetch documents from audit collection based on filter criteria
            contributions = list(segments.find(filter_criteria))
            
            processed_contributions = []
            user_collection = db.user
                    
            for contribution in contributions:
                user = user_collection.find_one({"_id": ObjectId(contribution["job_order"]["person_responsible"])})
                first_name = user.get("fname", "")
                last_name = user.get("lname", "")
                road_names = ", ".join(contribution["roads_affected"]) if "roads_affected" in contribution else ""
                barangays = ", ".join(contribution["barangays_affected"]) if "barangays_affected" in contribution else ""
                processed_detail = {
                        "startdate": contribution["job_order"]["start_date"],
                        "road_name": road_names,
                        "barangay": barangays,
                        "incharge": str(f"{first_name} {last_name}"),
                        "prio": str(contribution["priority_level"])
                    }
                processed_contributions.append(processed_detail)
            # Pass the processed contributions data to the frontend for display
        if report_type == 4:
            filter_criteria = {
                "timestamp": {"$gte": start_date, "$lte": end_date},
                "collectionName": "contributions",  # Filter by collectionName "contributions",
                "operationType": "insert"
            }

            # Fetch documents from audit collection based on filter criteria
            contributions = list(audit_collection.find(filter_criteria))
            
            processed_contributions = []
            
            for contribution in contributions:
                if "details" in contribution:
                    processed_detail = {
                            "timestamp": str(contribution["timestamp"]),
                            "road_name": str(contribution["details"]["road_name"]),
                            "barangay": str(contribution["details"]["barangay"]),
                            "contributor": str(f"{contribution["details"]["contributor_fname"]} {contribution["details"]["contributor_lname"]}"),
                            "contributor_role": str(contribution["details"]["contributor_role"])
                        }
                    processed_contributions.append(processed_detail)
                else:
                    # Handle case where "details" field is missing or None
                    processed_detail = {
                        "timestamp": contribution['timestamp'],
                        "road_name": "",
                        "barangay": "",
                        "contributor": "",
                        "contributor_role": ""
                    }
                    processed_contributions.append(processed_detail)
            # Pass the processed contributions data to the frontend for display
        if report_type == 5:
            filter_criteria = {
                "timestamp": {"$gte": start_date, "$lte": end_date},
                "collectionName": "contributions",  # Filter by collectionName "contributions"
                "operationType": "update",
                "details.is_validated": {"$in": [1, -1]}  # Filter where is_validated is 1 or -1
            }

            # Fetch documents from audit collection based on filter criteria
            contributions = list(audit_collection.find(filter_criteria))
            
            processed_contributions = []
            
            for contribution in contributions:
                if "details" in contribution:
                    processed_detail = {
                            "timestamp": str(contribution["timestamp"]),
                            "road_name": str(contribution["details"]["road_name"]),
                            "barangay": str(contribution["details"]["barangay"]),
                            "contributor": str(f"{contribution["details"]["contributor_fname"]} {contribution["details"]["contributor_lname"]}"),
                            "contributor_role": str(contribution["details"]["contributor_role"]),
                            "validator": str(f"{contribution["details"]["validator_fname"]} {contribution["details"]["validator_lname"]}"),
                            "validation_date": str(contribution["details"]["validation_date"])
                        }
                    processed_contributions.append(processed_detail)
            # Pass the processed contributions data to the frontend for display
        if report_type == 6:
            # Fetch documents from audit collection based on filter criteria
            contributions = contribution_collection.find({})
            
            processed_contributions = []
            
            for contribution in contributions:
                if contribution["is_validated"] == 0:
                    processed_detail = {
                            "timestamp": str(contribution["contribution_date"]),
                            "road_name": str(contribution["road_name"]),
                            "barangay": str(contribution["barangay"]),
                            "contributor": str(f"{contribution["contributor_fname"]} {contribution["contributor_lname"]}"),
                            "contributor_role": str(contribution["contributor_role"])
                        }
                    processed_contributions.append(processed_detail)
            # Pass the processed contributions data to the frontend for display
        if report_type == 7:
            filter_criteria = {
                "timestamp": {"$gte": start_date, "$lte": end_date},
                "collectionName": "contributions",  # Filter by collectionName "contributions"
                "operationType": "update",
                "details.is_validated": 1
            }

            # Fetch documents from audit collection based on filter criteria
            contributions = list(audit_collection.find(filter_criteria))
            
            processed_contributions = []
            
            for contribution in contributions:
                if "details" in contribution:
                    processed_detail = {
                            "timestamp": str(contribution["timestamp"]),
                            "road_name": str(contribution["details"]["road_name"]),
                            "barangay": str(contribution["details"]["barangay"]),
                            "contributor": str(f"{contribution["details"]["contributor_fname"]} {contribution["details"]["contributor_lname"]}"),
                            "contributor_role": str(contribution["details"]["contributor_role"]),
                            "validator": str(f"{contribution["details"]["validator_fname"]} {contribution["details"]["validator_lname"]}"),
                            "validation_date": str(contribution["details"]["validation_date"])
                        }
                    processed_contributions.append(processed_detail)
            # Pass the processed contributions data to the frontend for display
        if report_type == 8:
            filter_criteria = {
                "timestamp": {"$gte": start_date, "$lte": end_date},
                "collectionName": "contributions",  # Filter by collectionName "contributions"
                "operationType": "update",
                "details.is_validated": -1
            }

            # Fetch documents from audit collection based on filter criteria
            contributions = list(audit_collection.find(filter_criteria))
            
            processed_contributions = []
            
            for contribution in contributions:
                if "details" in contribution:
                    processed_detail = {
                            "timestamp": str(contribution["timestamp"]),
                            "road_name": str(contribution["details"]["road_name"]),
                            "barangay": str(contribution["details"]["barangay"]),
                            "contributor": str(f"{contribution["details"]["contributor_fname"]} {contribution["details"]["contributor_lname"]}"),
                            "contributor_role": str(contribution["details"]["contributor_role"]),
                            "validator": str(f"{contribution["details"]["validator_fname"]} {contribution["details"]["validator_lname"]}"),
                            "validation_date": str(contribution["details"]["validation_date"])
                        }
                    processed_contributions.append(processed_detail)
            # Pass the processed contributions data to the frontend for display
        return render_template("generated_report.html", contributions=processed_contributions, role=role, fname=fname, lname=lname, contribcount=count, report_type =report_type, start_date=start_date_str, end_date=end_date_str, head_contribcount=head_count)
    # END - REPORT MODULE ----------------------------------------------------------------------------------------------------------------
    # START - JOB ORDER LIST MODULE ----------------------------------------------------------------------------------------------------------------

    @app.route("/job_order_list")
    @limiter.limit("5000 per hour")
    def job_order_list():
        access = ["Admin", "Engineering" , "Engineering Head"]
        role = session.get("role")
        if role == None:
                session.pop("email", None)
                return render_template("login.html")
        fname = session.get("fname")
        lname = session.get("lname")
        if has_access(session, access) == False:
                session.pop("email", None)
                return render_template("login.html")
        contribcollection = db.contributions
        count = contribcollection.count_documents({"is_validated": 0})
        head_count = contribcollection.count_documents({"is_validated": 1, "head_validated": 0})
        # Query segments where job_order.start_date is not None and job_order status is not "Resolved" or "Cancelled"
        segments_with_start_date = db.segments.find({
            "job_order.start_date": {"$ne": None},
            "job_order.status": {"$nin": ["Resolved", "Cancelled"]}
        })
        
        # Process the segments data
        processed_segments = []
        for segment in segments_with_start_date:
            
            if "job_order" in segment:
                job_order = segment["job_order"]
                road_names = ", ".join(segment["roads_affected"]) if "roads_affected" in segment else ""
                barangays = ", ".join(segment["barangays_affected"]) if "barangays_affected" in segment else ""
                user_collection = db.user
                user = user_collection.find_one({"_id": ObjectId(segment["job_order"]["person_responsible"])})
                if user is not None:
                    first_name = user.get("fname", "")
                    last_name = user.get("lname", "")

                    completion_date_str = segment["job_order"]["completion_date"]
                    completion_date = datetime.strptime(completion_date_str, "%Y-%m-%d")

                    new_completion_date = completion_date + timedelta(days=1)

                    new_completion_date_str = new_completion_date.strftime("%Y-%m-%d")

                    segment["job_order"]["completion_date"] = new_completion_date_str
                    if segment["job_order"]["status"] not in ["Resolved", "Cancelled"]:
                        processed_segment = {
                            "_id": str(segment["_id"]),  # Convert ObjectId to string
                            "start_date": segment["job_order"]["start_date"],
                            "completion_date": segment["job_order"]["completion_date"],
                            "roads_affected": road_names,
                            "barangays_affected": barangays,
                            "priority_level": segment["priority_level"],
                            "person_responsible": str(f"{first_name} {last_name}")
                        }
                        processed_segments.append(processed_segment)
        
        return render_template("joborderlist.html", role=role, fname=fname, lname=lname, contribcount=count, segments_with_start_date=processed_segments, head_contribcount=head_count)
    
    # @app.route('/job_order_list/submit_job_order_list', methods=['POST'])
    # def submit_job_order_list():
    #     if request.method == 'POST':
    #         # Get the form data
    #         segment_id = request.form.get('segmentId')
    #         print(f"==>> segment_id: {segment_id}")
    #         start_date = request.form.get('startDate')
    #         print(f"==>> start_date: {start_date}")
    #         completion_date = request.form.get('completionDate')
    #         print(f"==>> completion_date: {completion_date}")
    #         person_responsible = request.form.get('personResponsible')
    #         print(f"==>> person_responsible: {person_responsible}")
    #         reason = request.form.get('editReason')

    #         # Initialize variables with default values
    #         barangays_affected = ''
    #         roads_affected = ''
    #         priority_score = ''
    #         priority_level = ''
    #         person_responsible_email = ''

    #         segment = db.segments.find_one(
    #             {"_id": ObjectId(segment_id)},
    #         )
    #         if segment:
    #             barangays_affected = ', '.join(segment.get('barangays_affected', []))
    #             roads_affected = ', '.join(segment.get('roads_affected', []))
    #             priority_score = segment.get('priority_score')
    #             priority_level = segment.get('priority_level')
    #             person = db.user.find_one(
    #                 {"_id": ObjectId(person_responsible)},
    #             )
    #             if person:
    #                 person_responsible_email = person.get('email')

    #     contributor_list = get_contributors_from_segment(segment_id)

    #     send_email("[APCS] Reported Pothole Under Repair",
    #                "autopriority.classification.sys@gmail.com",
    #                contributor_list,
    #                f"Your Reported Pothole on Streets: {roads_affected} and Barangays: {barangays_affected} with a Priority Score of {priority_score} ({priority_level}) is currently under repair! (Start Date: {start_date} | Completion Date: {completion_date})"
    #     )

    #     send_email("[APCS] Your Job Order Was Successfully Created",
    #                "autopriority.classification.sys@gmail.com",
    #                [session.get("email")],
    #                f"Your Job Order on Streets: {roads_affected} and Barangays: {barangays_affected} with a Priority Score of {priority_score} ({priority_level}) was successfully created! (Start Date: {start_date} | Completion Date: {completion_date})"
    #     )

    #     if person_responsible_email:
    #         send_email("[APCS] A Job Order Was Assigned to You",
    #                    "autopriority.classification.sys@gmail.com",
    #                    [person_responsible_email],
    #                    f"Your Job Order on Streets: {roads_affected} and Barangays: {barangays_affected} with a Priority Score of {priority_score} ({priority_level}) was successfully created! (Start Date: {start_date} | Completion Date: {completion_date})"
    #         )

    #     if segment:
    #         print(segment['job_order']['status'])
    #         if segment['job_order']['status'] == "None" or segment['job_order']['status'] is None:
    #             new_job_order = JobOrder(start_date, completion_date, person_responsible, 'In Progress', None, None, None, None)
    #             db.segments.update_one(
    #                 {"_id": ObjectId(segment_id)},
    #                 {"$set": {
    #                     'job_order': new_job_order.to_dict()
    #                 }}
    #             )
    #         else:
    #             edit_job_order = JobOrder(segment['job_order']['start_date'], segment['job_order']['completion_date'], segment['job_order']['person_responsible'], 'For Approval', reason, person_responsible, start_date, completion_date)
    #             db.segments.update_one(
    #                 {"_id": ObjectId(segment_id)},
    #                 {"$set": {
    #                     'job_order': edit_job_order.to_dict()
    #                 }}
    #             )
    #             engineering_head = db.user.find(
    #                 {"role": "Engineering Head"},
    #                 {"_id": 0, "email": 1}
    #             )

    #             engineering_head_emails = [user['email'] for user in engineering_head]

    #             send_email("[APCS] New Pending Job Order Edit Request",
    #                        "autopriority.classification.sys@gmail.com",
    #                        engineering_head_emails,
    #                        f"Job Order for segment {segment_id} has a pending request for edit. Please review in the explore or job order tab."
    #             )

    #     return redirect(url_for("job_order_list"))

    @app.route('/user_id')
    @limiter.limit("5000 per hour")
    def user_info():
        user_id = session.get('_id')
        return jsonify(user_id=user_id)
    
    @app.route('/user_role')
    @limiter.limit("5000 per hour")
    def user_role():
        role = session.get('role')
        return jsonify(role=role)


    @app.route("/rate_limit_error")
    def rate_limit_error():
        return render_template("rate_limit_error.html")
    
    @app.route("/not_found_error")
    def not_found_error():
        return render_template("not_found_error.html")
    
    @app.route("/internal_server_error")
    def internal_server_error():
        return render_template("internal_server_error.html")
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return redirect(url_for('rate_limit_error'))
    
    @app.errorhandler(404)
    def ratelimit_handler(e):
        return redirect(url_for('not_found_error'))
    
    @app.errorhandler(500)
    def internal_server_error_handler(e):
        return redirect(url_for('internal_server_error'))


    # END - JOB ORDER LIST MODULE ----------------------------------------------------------------------------------------------------------------
    # END - APP ----------------------------------------------------------------------------------------------------------

    def snap_to_roads(points):
        # print("bbbbbbbbbbbbbbbbbbbbbbbbbbb")
        base_url = "https://roads.googleapis.com/v1/snapToRoads"
        params = {
            "interpolate": "true",
            "path": "|".join(
                [f'{point["latitude"]},{point["longitude"]}' for point in points]
            ),
            "key": google_maps_token,
        }
        response = requests.get(base_url, params=params)
        # print(f"ddddddddddddddddd {response.status_code}")
        if response.status_code == 200:
            # print("ccccccccccccccccccccc")
            result = response.json()
            if "snappedPoints" in result:
                return result["snappedPoints"]
        return None

    return app

app = create_app()
# If this script is executed directly, run the app
if __name__ == "__main__":

    # from waitress import serve
    # serve(app, host="0.0.0.0", port=8080)
    app.run(host="0.0.0.0", debug=True)
    
