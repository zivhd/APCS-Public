# Auto Priority Classification System
System to automatically detect (using RFEX) and classify (using a WSM algorithm) potholes for the Mandaluyong LGU

Created by @Xei-pher , @zivHD, @juliacvc, and @syrelss

Uses RFEX by Agulto et al 2023

## Install FFMPEG for RFEX

1. **Download ffmpeg**
   -  Download from: https://github.com/BtbN/FFmpeg-Builds/releases

2. **For Windows:**
    - Download ffmpeg-master-latest-win64-gpl.zip
    - Extract anywhere
    - Create a folder in a easily accesible directory (i.e. C:/ffmpeg)
    - Copy the contents of the bin folder to your new folder
    - Edit your environtment variables and add that directory to your PATH variables


## Set Up Environment

1. **Set up virtualenv**

    ```bash
    pip install virtualenv
    virtualenv apcs
    myenv\Scripts\activate
    ```

    Run if activate script fails
    ```bash
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    ````    

2. **Install Python Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Install Tailwind CSS and Tailwind CSS Forms for Front-end Styling:**

    ```bash
    npm install -D tailwindcss
    npm install -D @tailwindcss/forms
    ```

4. **Install Concurrency:**

    ```bash
    npm install concurrency
    ```

## Run the Application

To start the application, you can use one of the following commands:

1. **Start the Application with npm for styling Tailwind:**

    ```bash
    npm run start
    ```

2. **Alternatively, Use Python to Run the App:**

    ```bash
    python app.py
    ```

