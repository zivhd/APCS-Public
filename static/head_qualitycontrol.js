
const disapprovalReason = document.getElementById('disapprovalReason');
const submitDisapprovalBtn = document.getElementById('submitDisapprovalBtn');
function showLoadingBar() {
  const loadingBar = document.getElementById("loading-bar");

  loadingBar.classList.remove("hidden");

}
var map;
// Function to hide the loading bar
function hideLoadingBar() {
  const loadingBar = document.getElementById("loading-bar");
  loadingBar.classList.add("hidden");
}

fetch("/head_qualitycontrol/contributions")
  .then((response) => response.json())
  .then((data) => {
    const contributionsBody = document.getElementById("contributions-body");
    data.forEach((contribution) => {
      if (contribution.is_validated === 1 && contribution.head_validated === 0) {
        const row = document.createElement("tr");
        const contrib_type = document.createElement("td");

        contrib_type.textContent = "Image";
        if (contribution.is_rfex) {
          if (contribution.is_rfex == true) {
            contrib_type.textContent = "RFEX";
          }
        }
        const contrib_name = document.createElement("td");
        contrib_name.textContent = contribution.contributor_fname + " " + contribution.contributor_lname;
        const contrib_role = document.createElement("td");
        contrib_role.textContent = contribution.contributor_role;
        const contrib_date = document.createElement("td");

        const contrib_validator = document.createElement("td");
        contrib_validator.textContent = contribution.validator_fname + " " + contribution.validator_lname;

        const date = new Date(contribution.contribution_date);
        // Get the current date
        const today = new Date();
        // Set the time component of today to 00:00:00 to represent the start of the day
        today.setHours(0, 0, 0, 0);
        // Assuming 'date' is the date you want to compare against
        // Set the time component of 'date' to 00:00:00 to represent the start of the day
        date.setHours(0, 0, 0, 0);

        const timeDifference = today - date;

        const daysAgo = Math.floor(timeDifference / (1000 * 60 * 60 * 24));

        if (daysAgo === -1) {
          // If the contribution was made today, set the text content to "Today"
          contrib_date.textContent = "Today";
        }
        else if (daysAgo === 0) {
          contrib_date.textContent = "Yesterday";
        }
        else {
          // Otherwise, set the text content to "x days ago"
          contrib_date.textContent = `${daysAgo + 1} days ago`;
        }

        const streetNameCell = document.createElement("td");
        streetNameCell.textContent = contribution.road_name;
        const barangayNameCell = document.createElement("td");
        barangayNameCell.textContent = contribution.barangay;

        contrib_type.classList.add("py-3", "px-12");
        contrib_name.classList.add("py-3", "px-12");
        contrib_role.classList.add("py-3", "px-12");
        contrib_date.classList.add("py-3", "px-12");
        streetNameCell.classList.add("py-3", "px-12");
        barangayNameCell.classList.add("py-3", "px-12");
        contrib_type.classList.add("py-3", "px-12");
        contrib_validator.classList.add("py-3", "px-12");

        row.appendChild(contrib_type);
        row.appendChild(contrib_name);
        row.appendChild(contrib_role);
        row.appendChild(contrib_date);
        row.appendChild(streetNameCell);
        row.appendChild(barangayNameCell);
        row.appendChild(contrib_validator);
        const actionsCell = document.createElement("td");
        actionsCell.classList.add("py-3", "px-12");
        const inspectButton = document.createElement("button");
        inspectButton.classList.add(
          "bg-blue-500",
          "hover:bg-blue-700",
          "text-white",
          "font-bold",
          "py-2",
          "px-4",
          "rounded"
        );
        inspectButton.textContent = "Inspect";
        inspectButton.addEventListener("click", function () {

          const modal = document.getElementById("modal");
          modal.classList.remove("hidden");
          document.getElementById("modal-latitude").textContent =
            contribution.latitude;
        document.getElementById("traffic-volume").value = contribution.traffic_volume;
          document.getElementById("modal-longitude").textContent =
            contribution.longitude;
          document.getElementById("modal-filename").textContent =
            contribution.filename;
          document.getElementById("modal-id").textContent = contribution._id;
          document.getElementById("modal-barangay").textContent =
            contribution.barangay;
          document.getElementById("modal-roadname").textContent =
            contribution.road_name;
          console.log("contribution.has_sidewalk", contribution.has_sidewalk)
          document.getElementById("has-sidewalk").checked = contribution.has_sidewalk
          document.getElementById("is_oneway").checked = contribution.is_oneway
          const timestampText = document.getElementById("timeStampText")
          console.log(contribution.image_timestamp)
          let image_timestamp = contribution.image_timestamp;
          const regex = /^\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}$/;
          if (regex.test(image_timestamp)) {
            image_timestamp = image_timestamp.replace(/^(\d{4}):(\d{2}):(\d{2})/, '$1-$2-$3');
            // Replace the space between the date and time with a 'T'
            image_timestamp = image_timestamp.replace(' ', 'T');
          }

          // Convert the date string to a Date object
          initializeMap(contribution.latitude,contribution.longitude)
          const date = new Date(image_timestamp);
          console.log(date)
          // Get the current date
          const today = new Date();
          // Set the time component of today to 00:00:00 to represent the start of the day
          today.setHours(0, 0, 0, 0);
          // Assuming 'date' is the date you want to compare against
          // Set the time component of 'date' to 00:00:00 to represent the start of the day
          date.setHours(0, 0, 0, 0);


          const timeDifference = today - date;

          const daysAgo = Math.floor(timeDifference / (1000 * 60 * 60 * 24));
          console.log(daysAgo + 1)

          if (daysAgo === -1) {
            // If the contribution was made today, set the text content to "Today"
            timestampText.textContent = "Today";
          }
          else if (daysAgo === 0) {
            timestampText.textContent = "Yesterday";
          }
          else {
            // Otherwise, set the text content to "x days ago"
            timestampText.textContent = `Image taken ${daysAgo + 1} days ago`;
          }

          const streetNameCell = document.createElement("td");
          streetNameCell.textContent = contribution.road_name;
          const barangayNameCell = document.createElement("td");
          console.log(contribution.filename)
          const imageElement = document.getElementById("modal-image");
          imageElement.src = `static/frames/${contribution.filename}`;
        });
        actionsCell.appendChild(inspectButton);
        row.appendChild(actionsCell);

        contributionsBody.appendChild(row);
      }
    });
  })
  .catch((error) => console.error("Error fetching contributions:", error));
document.getElementById("searchInput").addEventListener("input", function () {
  const input = this.value.toLowerCase();
  const rows = document.querySelectorAll("#contributions-body tr");

  rows.forEach((row) => {
    const contribName = row.children[1].textContent.toLowerCase();
    const streetName = row.children[3].textContent.toLowerCase();
    const barangayName = row.children[4].textContent.toLowerCase();

    if (
      contribName.includes(input) ||
      streetName.includes(input) ||
      barangayName.includes(input)
    ) {
      row.style.display = "";
    } else {
      row.style.display = "none";
    }
  });
});
document.getElementById("close-modal").addEventListener("click", function () {
  const modal = document.getElementById("modal");
  modal.classList.add("hidden");
});
document
  .getElementById("approve-button")
  .addEventListener("click", function () {
    showLoadingBar();
    modal.classList.add("hidden");
    const contributionId = document.getElementById("modal-id").textContent;
    const filename = document.getElementById("modal-filename").textContent;
    const latitude = document.getElementById("modal-latitude").textContent;
    const longitude = document.getElementById("modal-longitude").textContent;
    const trafficVolume = document.getElementById("traffic-volume").value;
    const hasSidewalk = document.getElementById("has-sidewalk").checked;
    const is_oneway = document.getElementById("is_oneway").checked;
    sendValidationAction(
      contributionId,
      latitude,
      longitude,
      filename,
      trafficVolume,
      hasSidewalk,
      is_oneway,
      "approve"
    )
  });


// Disapprove Button inside the modal
document
  .getElementById("disapprove-button")
  .addEventListener("click", function () {
    modal.classList.add("hidden");
    openDisapproveModal();

  });

  document
  .getElementById("submitDisapprovalBtn")
  .addEventListener("click", function () {
    modal.classList.add("hidden");
    var disapprovalReasonDropdown = document.getElementById('disapprovalReason');
    var textarea = document.getElementById('otherReason');
    console.log("AHHHHHHHHHHHHHHHHHHHHHHHHHHH");
    console.log(textarea.value);
    if (disapprovalReasonDropdown.value === 'other') {
      document.getElementById('disapprovalReason').value = textarea.value;
    }
    const contributionId = document.getElementById("modal-id").textContent;
    const filename = document.getElementById("modal-filename").textContent;
    const latitude = document.getElementById("modal-latitude").textContent;
    const longitude = document.getElementById("modal-longitude").textContent;
    const trafficVolume = document.getElementById("traffic-volume").value;
    const hasSidewalk = document.getElementById("has-sidewalk").checked;
    const is_oneway = document.getElementById("is_oneway").checked;
    let reason = document.getElementById('disapprovalReason').value;
    if (reason == ''){
      reason = textarea.value;
    }
    closeDisapproveModal()
    sendValidationAction(
      contributionId,
      filename,
      latitude
      ,longitude,
      trafficVolume,
      hasSidewalk,
      is_oneway,
      "disapprove",
      reason
    )

  });

function sendValidationAction(
  contributionId,
  latitude,
  longitude,
  filename,
  trafficVolume,
  hasSidewalk,
  is_oneway,
  action,
  reason
) {
  fetch("/head_qualitycontrol/validate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      action: action,
      contributionId: contributionId,
      latitude: latitude,
      longitude: longitude,
      filename: filename,
      trafficVolume: trafficVolume,
      hasSidewalk: hasSidewalk,
      is_oneway: is_oneway,
      reason: reason,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log("Testss")
      if (action == "approve") {
        openSuccessModal();
      }
      console.log("Validation response:", data);

    })
    .catch((error) =>
      console.error("Error sending validation action:", error)
    );
}

function openSuccessModal() {
  var modal = document.getElementById("successModal");
  modal.classList.remove("hidden"); // Show the modal

  // Prevent form submission
  // event.preventDefault();
}
function initializeMap(latitude,longitude){
  if (map) {
    console.log("map")
    map.remove(); // Remove the previous map instance
}
  map = L.map('map').setView([latitude, longitude], 13);

 // Add a tile layer (OpenStreetMap)
 L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
   maxZoom: 19,
 }).addTo(map);

 // Add a marker to the map
  marker = L.marker([latitude, longitude]).addTo(map);
 // Convert the date string to a Date object
}
function submitDisapproval() {

  sendValidationAction(
    contributionId,
    latitude,
    longitude,
    filename,
    trafficVolume,
    hasSidewalk,
    is_oneway,
    action,
    reason
  )
}

function openDisapproveModal() {
  var modal = document.getElementById("disapprovalModal");
  modal.classList.remove("hidden");
  



}

function closeDisapproveModal() {
  var modal = document.getElementById("disapprovalModal");
  modal.classList.add("hidden");

  window.location.reload();
}

function closeSuccessModal() {
  var modal = document.getElementById("successModal");
  modal.classList.add("hidden"); // Hide the modal
  window.location.reload();
}





function toggleButton() {
  if (disapprovalReason.value.trim() !== '') {
    submitDisapprovalBtn.disabled = false;
  } else {
    submitDisapprovalBtn.disabled = true;
  }
}

disapprovalReason.addEventListener('input',toggleButton);