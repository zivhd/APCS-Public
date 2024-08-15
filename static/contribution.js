const fileInput = document.getElementById("non_rfex_image");
const uploadModal = document.getElementById("uploadModal");
const closeModalBtn = document.getElementById("closeModalBtn");
const coordinatesText = document.getElementById("coordinatesText");
const uploadedImage = document.getElementById("uploadedImage");
const timeStampText = document.getElementById("timeStampText");
const dateTimePicker = document.getElementById("dateTimePicker");
const dateTimePickerLabel = document.getElementById("dateTimePickerLabel")
const uploadImageButton = document.getElementById("uploadImageButton");
const hiddenTimestamp = document.getElementById("timeStamp");
const notInMandaluyongModal = document.getElementById("notInMandaluyongModal");
const loadingBar = document.getElementById("loading-bar");
const locationText = document.getElementById("locationText");
fileInput.addEventListener("change", handleFileUpload);

document.getElementById('uploadButton').addEventListener('click', function () {
  var gpxFile = document.getElementById('gpx_file').files[0];
  var mp4File = document.getElementById('mp4_file').files[0];

  if (gpxFile && mp4File) {
      var formData = new FormData();
      formData.append('gpx_file', gpxFile);
      formData.append('mp4_file', mp4File);
      loadingBar.classList.remove("hidden");

      fetch('/upload_contribution', {
          method: 'POST',
          body: formData
      })
          .then(response => {
              if (response.ok) {
                loadingBar.classList.add("hidden");
                  alert('Files uploaded successfully');
                  // Optionally, redirect to another page
                  // window.location.href = '/success';
              } else {
                loadingBar.classList.add("hidden");
                  alert('Failed to upload files');
              }
          })
          .catch(error => {
            loadingBar.classList.add("hidden");
              console.error('Error:', error);
              alert('An error occurred while uploading files');
          });
  } else {
    loadingBar.classList.add("hidden");
      alert('Please select both GPX and MP4 files');
  }
});

closeModalBtn.addEventListener("click", () => {
  closeModal();
  document.getElementById("action").value = "cancel";
  document.getElementById("upload_non_rfex").submit();
});

async function handleFileUpload() {
  const file = fileInput.files[0];
  var coordinatesCheck;

  if (file) {
    const formData = new FormData();
    formData.append("file", file);
    console.log(file)

    try {
      const response = await fetch("/non_rfex_upload", {
        method: "POST",
        body: formData,
        headers: { coordinatesCheck: coordinatesCheck },
      });

      const data = await response.json();

    

      var coordinates = data.coordinates;

      console.log("test1");
      console.log(`Coordinates1: ${coordinates}`);
      if (coordinates == -1){
        console.log("ahgsdfhahafhadhafdhah")
        document.getElementById("invalidImageModal").classList.remove("hidden");
      }
        const timestamp = await getDateFromExif(file);
        console.log("timestamp: ",timestamp)
        
        // Call function to check date and time taken
     



      if (coordinates == 1) {
        uploadModal.classList.remove("hidden");
        const coordinates = await displayMap();
        coordinatesCheck = coordinates;
        console.log(`coordinatesCheck: ${coordinates}`);
        document.getElementById("coords").value = coordinates;
        if (coordinates != null) {
          displayCoordinates(coordinates,timestamp);
        }
      } else {
        const coordinatesArray = coordinates.split(",");
        fetch("/check_if_in_mandaluyong", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ latitude: coordinatesArray[0], longitude: coordinatesArray[1] }),
        })
          .then((response) => {
            if (response.status === 200) {
               uploadModal.classList.remove("hidden");
              document.getElementById("coords").value = coordinates;
              displayCoordinates(coordinates,timestamp);
              console.log("Location is in Mandaluyong");
  
            } else {
              // Location is not in Mandaluyong
              // locationText.innerText = `Location is not in Mandaluyong`;
              uploadModal.classList.add("hidden");
              notInMandaluyongModal.classList.remove("hidden")
              console.log("Location is not in Mandaluyong");
              return
            }
          })
          .catch((error) => console.error("Error:", error));
  

            

      }

      uploadedImage.src = URL.createObjectURL(file);
      uploadedImage.alt = "Uploaded Image";
      
 

    } catch (error) {
      console.error("Error:", error);
    }
  }
}

async function getDateFromExif(file) {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/extract_exif_date_time", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error("Failed to extract date and time from image");
    }

    const data = await response.json();
    return data.date_time;
  } catch (error) {
    console.error("Error:", error);
    return null;
  }
}




function displayCoordinates(coordinates,timestamp) {
  console.log('timestampadfadfa!!!',timestamp)
  const coordinatesArray = coordinates.split(",");
  coordinatesText.textContent = `Coordinates: X - ${coordinatesArray[0]}, Y - ${coordinatesArray[1]}`;
  if (timestamp != null){
  const [datePart, timePart] = timestamp.split(' ');
  const [year, month, day] = datePart.split(':').map(Number);
  const [hour, minute, second] = timePart.split(':').map(Number);
  // Create a new Date object
    const timestampDate = new Date(year, month - 1, day, hour, minute, second);
    console.log(timestampDate)
    const now = new Date();
    const differenceMs = now - timestampDate;
    const differenceDays = Math.floor(differenceMs / (1000 * 60 * 60 * 24));
    uploadImageButton.disabled = false;
    dateTimePickerLabel.classList.add("hidden")
    timeStampText.classList.remove('hidden')
    timeStampText.textContent = `Image was taken ${differenceDays} days ago`;
    
    console.log('timestamp!!!',convertDateTime(timestamp))
    hiddenTimestamp.value = convertDateTime(timestamp)
    
  } else{
    dateTimePicker.classList.remove('hidden')
    dateTimePicker.addEventListener('input', toggleUploadButtonState);
  }
}

function convertDateTime(inputDateTime) {
  var parts = inputDateTime.split(/[\s:]/); // Splitting the input by space or colon
  var year = parts[0];
  var month = parts[1];
  var day = parts[2];
  var hour = parts[3];
  var minute = parts[4];
  
  // Creating the formatted date string
  var formattedDate = year + "-" + month + "-" + day + "T" + hour + ":" + minute;
  
  return formattedDate;
}
function toggleUploadButtonState() {
  hiddenTimestamp.value = dateTimePicker.value;
  if (dateTimePicker.value) {
    uploadImageButton.disabled = false;
  } else {
    uploadImageButton.disabled = true;
  }
}
var mapInstance;
async function displayMap() {
  
  return new Promise((resolve) => {
    var coordinatesToReturn;
    setTimeout(function () {
      window.dispatchEvent(new Event("resize"));
    }, 1000);

    const mandaluyongCoordinates = [14.5794, 121.0359];

    if (mapInstance) {
      console.log("map")
      mapInstance.remove(); // Remove the previous map instance
  }

    mapInstance = L.map("map").setView(mandaluyongCoordinates, 20);
    L.tileLayer(
      "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
    ).addTo(mapInstance);

    fetch('/boundary')
    .then(response => response.json())
    .then(data => {
        console.log("data",data)
        L.geoJSON(data).addTo(mapInstance);
    })
    .catch(error => console.error('Error loading the GeoJSON data:', error));

    document
      .getElementById("coordinatesModal")
      .classList.remove("hidden");

    const confirmMapBtn = document.getElementById("confirmMapBtn");
    confirmMapBtn.addEventListener("click", () => {
      closeMapModal();
      resolve(coordinatesToReturn);
    });

    mapInstance.on("click", (e) => {
        confirmMapBtn.disabled = true;
      const { lat, lng } = e.latlng;

      fetch("/coordinates", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ lat, lng }),
      })
        .then((response) => response.json())
        .then((data) => {
          console.log("Coordinates sent to server:", data);
          document.getElementById(
            "coordinatesTextMap"
          ).innerText = `Clicked coordinates: ${data.lat}, ${data.lng}`;
          document.getElementById(
            "streetTextMap"
          ).innerText = ` Streetname: ${data.street}`;
          coordinatesToReturn = `${data.lat}, ${data.lng}, ${data.street}`;
          
          // Check if in Mandaluyong
      
      fetch("/check_if_in_mandaluyong", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ latitude: data.lat, longitude: data.lng }),
      })
        .then((response) => {
          if (response.status === 200) {
            confirmBtnState(data, confirmMapBtn,true);
            console.log("Location is in Mandaluyong");
            locationText.textContent = "";
          } else {
            // Location is not in Mandaluyong
            confirmBtnState(data, confirmMapBtn,false);
            console.log("Location is not in Mandaluyong");
            locationText.textContent = "Location is not in Mandaluyong";
            // Perform actions if the location is not in Mandaluyong
          }
        })
        .catch((error) => console.error("Error:", error));

          // Disable confirm button if street is "Unknown Location"
          
        })
        .catch((error) => console.error("Error:", error));
    });
  });
}

closeMapModalBtn.addEventListener("click", () => {
  document.getElementById("non_rfex_image").value = "";

  closeModal();
  closeMapModal();
  window.location.reload()
});

function confirmBtnState(data, confirmMapBtn, isInMandaluyong) {
  if (data.street === "Unknown Location" || !isInMandaluyong) {
    confirmMapBtn.disabled = true;
    confirmMapBtn.classList.remove("hover:bg-green-700");
  } else {
    confirmMapBtn.disabled = false;
    confirmMapBtn.classList.add("hover:bg-green-700");
  }
}

function closeMapModal() {

  document.getElementById("coordinatesModal").classList.add("hidden");
  event.preventDefault();
}

function closeModal() {
  uploadModal.classList.add("hidden");
  document.getElementById("non_rfex_image").value = "";
  event.preventDefault();
}

function openSuccessModal() {
  var modal = document.getElementById("successModal");
  modal.classList.remove("hidden"); // Show the modal
  uploadModal.classList.add("hidden");

  // Prevent form submission
  event.preventDefault();
}

function closeSuccessModal() {
  var modal = document.getElementById("successModal");
  document.getElementById("upload_non_rfex").submit(); //Submit the form once success modal is closed
  modal.classList.add("hidden"); // Hide the modal
}

function closeMandaluyongModal() {
  var modal = document.getElementById("notInMandaluyongModal");
  location.reload();
}

function closeInvalidImageModal() {
  console.log("Testtgtasdgfasdgasdg")
  location.reload();
}
