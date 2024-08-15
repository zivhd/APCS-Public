fetch('/segments')
    .then(response => response.json())
    .then(segments => {
        // Sort segments by priority_score in descending order
        segments.sort((a, b) => b.priority_score - a.priority_score);

        const pendingTbody = document.getElementById('pending-job-orders-tbody');
        const ongoingTbody = document.getElementById('ongoing-job-orders-tbody');
        const forapprovalTbody = document.getElementById('forapproval-job-orders-tbody');

        segments.forEach(async segment => {
            const segmentId = segment._id; // Extract segmentId from _id.$oid
            const roadsAffected = segment.roads_affected.join(", ");
            const priorityLevel = segment.priority_level;
            const priorityScore = segment.priority_score;

            let row;
            if (!segment.job_order || !segment.job_order.status) {
                // Add to Pending Job Orders table
                row = await createTableRow(segment, segmentId, roadsAffected, `/explore?segment_id=${segmentId}`, priorityScore, priorityLevel, 'Create Job Order');
                pendingTbody.appendChild(row);
            } else if (segment.job_order.status === "In Progress") {
                // Add to Ongoing Job Orders table
                row = await createTableRow(segment, segmentId, roadsAffected, `/explore?segment_id=${segmentId}`, priorityScore, priorityLevel, 'View');
                ongoingTbody.appendChild(row);
            }  else if (segment.job_order.status === "For Approval") {
              // Add to For Approval Job Orders table
                row = await createTableRow(segment, segmentId, roadsAffected, `/explore?segment_id=${segmentId}`, priorityScore, priorityLevel, 'View');
                forapprovalTbody.appendChild(row);
            }
        });
    })
    .catch(error => console.error('Error fetching segments:', error));

async function createTableRow(segment, segmentId, roadsAffected, linkUrl, priorityScore, priorityLevel, buttonText) {
    const row = document.createElement('tr');

    const idCell = document.createElement('td');
    idCell.style.textAlign = 'center'; // Center-align text in idCell
    idCell.textContent = segmentId.substr(segmentId.length - 5); // Display last 5 characters of segmentId
    row.appendChild(idCell);

    // Remove 'Road Segment' suffix from priority_level
    priorityLevel = priorityLevel.replace(' Road Segment', '');

    // Determine line color based on priority_score
    let lineColor;
    if (priorityScore >= 0.7) {
        lineColor = "red"; // Red for High Priority
    } else if (priorityScore >= 0.4) {
        lineColor = "orange"; // Orange for Medium-High Priority
    } else if (priorityScore >= 0.2) {
        lineColor = "yellow"; // Yellow for Medium-Low Priority
    } else {
        lineColor = "green"; // Green for Low Priority
    }

    const priorityCell = document.createElement('td');
    priorityCell.style.textAlign = 'center';
    priorityCell.textContent = priorityLevel;
    priorityCell.classList.add(`bg-${lineColor}-600`, 'rounded-lg', 'p-1', 'mx-4', 'shadow-md', 'px-4', 'text-center', 'font-bold', 'text-white');
    row.appendChild(priorityCell);

    const roadsCell = document.createElement('td');
    roadsCell.style.textAlign = 'center';
    roadsCell.textContent = roadsAffected;
    row.appendChild(roadsCell);

    const actionCell = document.createElement('td');
    
    // Add action button
    const actionButton = document.createElement('button');
    const role = await getCurrentUserRole();
    const user_id = await getCurrentUserId();
    actionButton.onclick = function() {
       openModal(segment, role, user_id);
    };
    actionButton.textContent = buttonText;
    actionButton.classList.add('bg-blue-600', 'rounded-lg', 'p-1', 'mx-4', 'shadow-md', 'px-4', 'text-center', 'font-bold', 'text-white');
    actionCell.style.textAlign = 'center';
    actionCell.appendChild(actionButton);
    row.appendChild(actionCell);

    return row;
}


function getUsers() {
    // Make a POST request to the /users endpoint and return the parsed JSON
    return fetch("/users", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .catch((error) => {
        console.error("Error:", error);
      });
  }

  async function getCurrentUserRole() {
    try {
        const response = await fetch('/user_role');
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }
        const data = await response.json();
        console.log(data.role);
        return data.role;
    } catch (error) {
        console.log(error.message);
    }
}

async function getCurrentUserId() {
    try {
        const response = await fetch('/user_id');
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }
        const data = await response.json();
        console.log(data.user_id);
        return data.user_id;
    } catch (error) {
        console.log(error.message);
    }
}


function editJobOrder(segment) {
    const modal = document.getElementById("myModal");
    const modalContent = document.getElementById("modal-content");

    console.log("Hello");
    console.log(segment);
  
    // Fetch users and populate the modal
    getUsers()
        .then((users) => {
            // Filter and format users for display in the modal
            const filteredUsers = users.filter(
                (user) =>
                    user.role === "Engineering" ||
                    (user.role === "Engineering Head" && user.verified)
            );
  
            // Generate HTML for the modal
            // No form action yet
            const modalHTML = `
            <form id="jobOrderForm" action="/explore/submit_job_order" method="post">
            <input type="hidden" id="fromWhere" name="fromWhere" value = "joborderlist">
              <label for="segmentId">Segment ID:</label>
              <input type="text" id="segmentId" name="segmentId" required value="${
                segment._id
              }" class="block mb-2 w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-orange-600 sm:text-sm sm:leading-6" readonly>
              
              <label for="personResponsible">Person Responsible:</label>
              <select id="personResponsible" name="personResponsible" class="block mb-2 w-full rounded-md border-0 px-3 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-orange-600 sm:text-sm sm:leading-6" required">
                ${filteredUsers
                  .map(
                    (user) =>
                      `<option value="${user._id}">${user.fname} ${user.lname}</option>`
                  )
                  .join("")}
              </select>
              
              <label for="startDate">Start Date:</label>
              <input type="date" id="startDate" name="startDate" class="block mb-2 w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-orange-600 sm:text-sm sm:leading-6" required value="${segment.job_order.start_date}">
              
              <label for="completionDate" id="completionDateLabel">Completion Date:</label>
              <input type="date" id="completionDate" name="completionDate" min="${
                segment.job_order.start_date
              }" class="block mb-2 w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-orange-600 sm:text-sm sm:leading-6" required value="${
            segment.job_order.completion_date
          }">
              
              <label for="editReason" class="block text-sm font-medium leading-6 text-gray-900">Reason for reschedule or reassignment:</label>
              <textarea id="editReason" name="editReason" rows="4" class="form-textarea block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-orange-600 sm:text-sm sm:leading-6" required></textarea>
              
              <button type="submit" class="float-left bg-red-500 hover:bg-red-700 text-white font-bold mt-3 py-2 px-4 rounded focus:outline-none focus:shadow-outline">Submit</button>
            </form>
          `;
  
            // Set modal content
            modalContent.innerHTML = modalHTML;
            
            // Display the modal
            modal.classList.remove("hidden");
            modal.classList.add("flex");
        })
        .catch((error) => {
            console.error("Error fetching users:", error);
        });
};

function createJobOrder(segment) {
    console.log("ahgahahafhaf")
    const modal = document.getElementById("myModal");
    const modalContent = document.getElementById("modal-content");
      
    // Fetch users and populate the modal
    getUsers()
      .then((users) => {
        // Filter and format users for display in the modal
        const filteredUsers = users.filter(
          (user) =>
            user.role === "Engineering" ||
            (user.role === "Engineering Head" && user.verified)
        );
  
        // Generate HTML for the modal
        const modalHTML = `
          <form id="jobOrderForm" action="/explore/submit_job_order" method="post">\
           <input type="hidden" id="fromWhere" name="fromWhere" value = "joborderlist">
            <label for="segmentId">Segment ID:</label>
            <input type="text" id="segmentId" name="segmentId" required value="${
              segment._id
            }" class="block mb-2 w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-orange-600 sm:text-sm sm:leading-6" readonly>
            
            <label for="personResponsible">Person Responsible:</label>
            <select id="personResponsible" name="personResponsible" class="block mb-2 w-full rounded-md border-0 px-3 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-orange-600 sm:text-sm sm:leading-6" required">
              ${filteredUsers
                .map(
                  (user) =>
                    `<option value="${user._id}">${user.fname} ${user.lname}</option>`
                )
                .join("")}
            </select>
            
            <label for="startDate">Start Date:</label>
            <input type="date" id="startDate" name="startDate" class="block mb-2 w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-orange-600 sm:text-sm sm:leading-6" required oninput="handleStartDateInput()">
            
            <label for="completionDate" id="completionDateLabel" style="display: none;">Completion Date:</label>
            <input type="date" id="completionDate" name="completionDate" style="display: none;" class="block mb-2 w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-orange-600 sm:text-sm sm:leading-6" required disabled>
            
            <button type="submit" class="float-left bg-red-500 hover:bg-red-700 text-white font-bold mt-3 py-2 px-4 rounded focus:outline-none focus:shadow-outline">Submit</button>
          </form>
        `;
  
        // Set modal content
        modalContent.innerHTML = modalHTML;
        modal.classList.remove("hidden");
        modal.classList.add("flex");
      })
      .catch((error) => {
        console.error("Error fetching users:", error);
      });
  }


  function openModal(segment, role,userId) {
    console.log("testadfasdf");
    var modal = document.getElementById("myModal");
    var modalContent = document.getElementById("modal-content");
    var lineColor, isAccessRoad, isMabuhayLane, hasSidewalk, isinIntersection, is_oneway;
  
    var uniqueRoads = segment.roads_affected;
  
    var uniqueBarangays = segment.barangays_affected;
  
    //Assign lineColor for different road priorities
  
    if (segment.priority_score >= 0.7) {
      lineColor = "red"; // Red for High Priority
    } else if (segment.priority_score >= 0.4) {
      lineColor = "orange"; // Orange for Medium-High Priority
    } else if (segment.priority_score >= 0.2) {
      lineColor = "yellow"; // Yellow for Medium-Low Priority
    } else {
      lineColor = "green"; // Green for Low Priority
    }
  
    //Assign values for boolean variables
    if (segment.is_access_road == 1) {
      isAccessRoad = "Yes";
    } else {
      isAccessRoad = "No";
    }
  
    if (segment.is_mabuhay_lane == 1) {
      isMabuhayLane = "Yes";
    } else {
      isMabuhayLane = "No";
    }
  
    if (segment.has_sidewalk == 1) {
      hasSidewalk = "Yes";
    } else {
      hasSidewalk = "No";
    }
  
    if (segment.is_oneway == 1) {
      is_oneway = "Yes";
    } else {
      is_oneway = "No";
    }
  
  
    if (segment.is_in_intersection == 1) {
      isinIntersection = "Yes";
    } else {
      isinIntersection = "No";
    }
    console.log(segment)
    var modalHTML = `
      <div class = "bg-${lineColor}-600 rounded-lg p-1 shadow-md px-4 text-center">
      <p class = "font-bold text-white">${
        segment.priority_level
      } (${segment.priority_score.toFixed(3)})</p>
      </div>
      <dl class="divide-y  divide-gray-100">
              <div class="px-4 py-1 ml-2 sm:grid sm:grid-cols-4 sm:gap-4 sm:px-0">
                  <dt class="text-sm font-medium leading-6 text-gray-900 sm:col-span-2">Segment ID</dt>
                  <dd class="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">${
                    segment._id
                  }</dd>
              </div>
              <div class="px-4 py-1 ml-2 sm:grid sm:grid-cols-4 sm:gap-4 sm:px-0">
                <div class="tooltip sm:col-span-2">
                    <dt class="text-sm font-medium leading-6 text-gray-900">
                        Road Classification
                        <span class="tooltip-icon">i</span>
                    </dt>
                    <span class="tooltiptext">Roads are classified into primary, secondary and tertiary roads, with primary being the most prioritized in repairs.</span>
                </div>
                <dd class="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">${segment.road_classification}</dd>
            </div>
              <div class="px-4 py-1 ml-2 sm:grid sm:grid-cols-4 sm:gap-4 sm:px-0">
                  <div class="tooltip sm:col-span-2">
                      <dt class="text-sm font-medium leading-6 text-gray-900">
                          Is Access Road?
                          <span class="tooltip-icon">i</span>
                      </dt>
                      <span class="tooltiptext">Access roads are pathways leading to primary roads or Mabuhay lanes.</span>
                  </div>
                  <dd class="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">${isAccessRoad}</dd>
              </div>
              <div class="px-4 py-1 ml-2 sm:grid sm:grid-cols-4 sm:gap-4 sm:px-0">
                  <div class="tooltip sm:col-span-2">
                      <dt class="text-sm font-medium leading-6 text-gray-900">
                          Is Mabuhay Lane?
                          <span class="tooltip-icon">i</span>
                      </dt>
                      <span class="tooltiptext">Mabuhay lanes are express routes designed to facilitate efficient and rapid travel.</span>
                  </div>
                  <dd class="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">${isMabuhayLane}</dd>
              </div>
              <div class="px-4 py-1 ml-2 sm:grid sm:grid-cols-4 sm:gap-4 sm:px-0">
                  <div class="tooltip sm:col-span-2">
                      <dt class="text-sm font-medium leading-6 text-gray-900">
                          Has Sidewalk?
                          <span class="tooltip-icon">i</span>
                      </dt>
                      <span class="tooltiptext">Sidewalks are important to note for road repair as they serve as pathways for pedestrians.</span>
                  </div>
                  <dd class="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">${hasSidewalk}</dd>
              </div>
              <div class="px-4 py-1 ml-2 sm:grid sm:grid-cols-4 sm:gap-4 sm:px-0">
                  <div class="tooltip sm:col-span-2">
                      <dt class="text-sm font-medium leading-6 text-gray-900">
                          Is a One-way road?
                          <span class="tooltip-icon">i</span>
                      </dt>
                      <span class="tooltiptext">One-way roads are roads to keep in mind especially if heavily congested.</span>
                  </div>
                  <dd class="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">${is_oneway}</dd>
              </div>
              <div class="px-4 py-1 ml-2 sm:grid sm:grid-cols-4 sm:gap-4 sm:px-0">
                  <div class="tooltip sm:col-span-2">
                      <dt class="text-sm font-medium leading-6 text-gray-900">
                          Is in Intersection?
                          <span class="tooltip-icon">i</span>
                      </dt>
                      <span class="tooltiptext">Roads located in intersections are crucial for road repair as they often experience higher traffic flow and wear.</span>
                  </div>
                  <dd class="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">${isinIntersection}</dd>
              </div>
              <div class="px-4 py-1 ml-2 sm:grid sm:grid-cols-4 sm:gap-4 sm:px-0">
                  <div class="tooltip sm:col-span-2">
                      <dt class="text-sm font-medium leading-6 text-gray-900">
                          No. of Nearby Establishments
                          <span class="tooltip-icon">i</span>
                      </dt>
                      <span class="tooltiptext">Roads with nearby establishments require timely maintenance to ensure accessibility and safety.</span>
                  </div>
                  <dd class="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">${
                    segment.nearby_establishments.length
                  }</dd>
              </div>
              <div class="px-4 py-1 ml-2 sm:grid sm:grid-cols-4 sm:gap-4 sm:px-0">
                  <div class="tooltip sm:col-span-2">
                      <dt class="text-sm font-medium leading-6 text-gray-900">
                          Population Density
                          <span class="tooltip-icon">i</span>
                      </dt>
                      <span class="tooltiptext">Areas with high population density indicate greater road usage. This is important to note to ensure safety and accessibility for the larger number of people using the roads.</span>
                  </div>
                  <dd class="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">${
                    segment.population_density
                  }</dd>
              </div>
              <div class="px-4 py-1 ml-2 sm:grid sm:grid-cols-4 sm:gap-4 sm:px-0">
                  <div class="tooltip sm:col-span-2">
                      <dt class="text-sm font-medium leading-6 text-gray-900">
                          Traffic Volume
                          <span class="tooltip-icon">i</span>
                      </dt>
                      <span class="tooltiptext">Roads with high traffic volumes experience increased wear and tear due to frequent use.</span>
                  </div>
                  <dd class="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">${
                    segment.traffic_volume
                  }</dd>
              </div>
              <div class="px-4 py-1 ml-2 sm:grid sm:grid-cols-4 sm:gap-4 sm:px-0">
                  <div class="tooltip sm:col-span-2">
                      <dt class="text-sm font-medium leading-6 text-gray-900">
                          No. of Potholes
                          <span class="tooltip-icon">i</span>
                      </dt>
                      <span class="tooltiptext">The number of potholes is a critical factor as they pose safety hazards and indicate the overall condition of the road surface, requiring prompt attention to prevent further deterioration and accidents.</span>
                  </div>
                  <dd class="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">${
                    segment.points.length
                  }</dd>
              </div>
              <div class="px-4 py-1 ml-2 sm:grid sm:grid-cols-4 sm:gap-4 sm:px-0">
          <dt class="text-sm font-medium leading-6 text-gray-900 sm:col-span-2">Roads Affected</dt>
          <dd class="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">
              <ul>
              ${uniqueRoads.map((road) => `<li>${road}</li>`).join("")}
              </ul>
          </dd>
      </div>
      <div class="px-4 py-1 ml-2 sm:grid sm:grid-cols-4 sm:gap-4 sm:px-0">
      <dt class="text-sm font-medium leading-6 text-gray-900 sm:col-span-2">Barangays Affected</dt>
      <dd class="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">
          <ul>
          ${uniqueBarangays.map((barangay) => `<li>${barangay}</li>`).join("")}
          </ul>
      </dd>
  </div>
              
      </dl>`;
      console.log("ID" + role);  
    console.log("ID" + segment._id);
    console.log("segment.job_order.status" + segment.job_order.status);
    if (role != "Contributor" && role != "TPMO" && role != "TPMO Head") {
      if (segment.job_order.status == null || segment.job_order.status == "") {
        modalHTML = modalHTML.concat(
          `<button class="float-left bg-red-500 hover:bg-red-700 text-white font-bold mt-3 mr-2 py-2 px-4 rounded focus:outline-none focus:shadow-outline" onclick="createJobOrder(${htmlEntities(
            JSON.stringify(segment)
          )})">Add Job Order</button>`
        );
      } else if (segment.job_order.status == "For Approval" && (role == "Engineering Head" || role == "Admin")) {
        modalHTML = modalHTML.concat(`     
              <button class="float-left bg-blue-500 hover:bg-blue-700 text-white font-bold mt-3 py-2 px-4 m-4 rounded focus:outline-none focus:shadow-outline" id="editBtn" onclick="jobOrderApproval(${htmlEntities(
                JSON.stringify(segment)
              )})">Inspect Edits</button>
              `);
      } else if ((segment.job_order.person_responsible == userId || role == "Admin") && segment.job_order.status == "In Progress") {
        modalHTML = modalHTML.concat(`     
      
              <button id="resolveButton" class="float-left bg-green-500 hover:bg-green-700 text-white font-bold mt-3 py-2 px-4 rounded focus:outline-none focus:shadow-outline" onclick ='resolveJobOrder(${htmlEntities(
                JSON.stringify(segment._id)
              )})'>Resolve</button>
              <button class="float-left bg-blue-500 hover:bg-blue-700 text-white font-bold mt-3 py-2 px-4 m-4 rounded focus:outline-none focus:shadow-outline" id="editBtn" onclick="editJobOrder(${htmlEntities(
                JSON.stringify(segment)
              )})">Edit Job Order</button>
              `);
      } else {
            modalHTML = modalHTML.concat(`     
        <p>You do not have permission to modify this Job Order. </p> `);

      }
    }
    
    modalContent.innerHTML = modalHTML;
  
    modal.classList.remove("hidden"); // Show the modal
  }
  function htmlEntities(str) {
    return String(str).replace(/"/g, "&quot;");
  }
  function showLoadingBar() {
    const loadingBar = document.getElementById("loading-bar");
  
    loadingBar.classList.remove("hidden");
  }
  
  function resolveJobOrder(segmentId) {
    console.log("Segment resolved successfully");
    var modal = document.getElementById("myModal");
    modal.classList.add("hidden");
    showLoadingBar();
  
    fetch("/explore/resolve", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ segmentId: segmentId }),
    })
      .then((response) => {
        console.log("ahafha");
        hideLoadingBar();
        window.location.reload();
        // Handle response
        if (response.ok) {
          hideLoadingBar();
          console.log("Segment resolved successfully");
          window.location.reload();
        } else {
          // Error
          console.error("Failed to resolve segment");
          window.location.reload();
        }
      })
      .catch((error) => {
        console.error("Error:", error);
      });
  }
function handleStartDateInput() {
    var startDate = document.getElementById("startDate").value;
    var completionDateLabel = document.getElementById("completionDateLabel");
    var completionDate = document.getElementById("completionDate");
  
    if (startDate) {
      // If start date has a value, show and make completion date accessible
      completionDateLabel.style.display = "block";
      completionDate.style.display = "block";
      completionDate.removeAttribute("disabled");
  
      // Set the min attribute of completion date to be later than the start date
      completionDate.setAttribute("min", startDate);
    } else {
      // If start date has no value, hide and disable completion date
      completionDateLabel.style.display = "none";
      completionDate.style.display = "none";
      completionDate.disabled = true;
    }
  }
// Function to hide the loading bar
function hideLoadingBar() {
    const loadingBar = document.getElementById("loading-bar");
    loadingBar.classList.add("hidden");
  }
function closeModal() {
    var modal = document.getElementById("myModal");
    modal.classList.add("hidden"); // Hide the modal
  };

async function jobOrderApproval(segment) {
    const modal = document.getElementById("myModal");
    const modalContent = document.getElementById("modal-content");
  
    // Hide the 'Show Potholes' button
    console.log(segment.job_order);
    try {
        const currentPersonResponsible = await getPersonResponsible(segment.job_order.person_responsible);
        console.log(currentPersonResponsible['fname']);
  
        const editPersonResponsible = await getPersonResponsible(segment.job_order.edit_person_responsible);
        console.log(editPersonResponsible['fname']);
  
  
    // Generate HTML for the modal
    const modalHTML = `
  
        <label for="segmentId">Segment ID:</label>
        <input type="text" id="segmentId" name="segmentId" required value="${segment._id}" class="block mb-2 w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-orange-600 sm:text-sm sm:leading-6" readonly>
        
  
        <label for="personResponsible">Current Person Responsible:</label>
        <input type="text" id="personResponsible" name="personResponsible" value="${currentPersonResponsible['fname'] + " " + currentPersonResponsible['lname']}" class="block mb-2 w-full rounded-md border-0 px-3 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-orange-600 sm:text-sm sm:leading-6" readonly>
  
        <label for="startDate">Current Start Date:</label>
        <input type="date" id="startDate" name="startDate" value="${segment.job_order.start_date}" class="block mb-2 w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-orange-600 sm:text-sm sm:leading-6" readonly>
        
        <label for="completionDate" id="completionDateLabel">Current Completion Date:</label>
        <input type="date" id="completionDate" name="completionDate" value="${segment.job_order.completion_date}" class="block mb-2 w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-orange-600 sm:text-sm sm:leading-6" readonly>
  
        <label for="personResponsible">Replacement Person Responsible:</label>
        <input type="text" id="personResponsible" name="personResponsible" value="${editPersonResponsible['fname'] + " " + editPersonResponsible['lname']}" class="block mb-2 w-full rounded-md border-0 px-3 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-orange-600 sm:text-sm sm:leading-6" readonly>
        <label for="startDate">Replacement Start Date:</label>
        <input type="date" id="startDate" name="startDate" value="${segment.job_order.edit_start_date}" class="block mb-2 w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-orange-600 sm:text-sm sm:leading-6" readonly>
        
        <label for="completionDate" id="completionDateLabel">Replacement Completion Date:</label>
        <input type="date" id="completionDate" name="completionDate" value="${segment.job_order.edit_completion_date}" class="block mb-2 w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-orange-600 sm:text-sm sm:leading-6" readonly>
        
        <label for="editReason" class="block text-sm font-medium leading-6 text-gray-900">Reason for reschedule or reassignment:</label>
        <textarea id="editReason" name="editReason" rows="4" class="form-textarea block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-orange-600 sm:text-sm sm:leading-6" readonly>${segment.job_order.edit_reason}</textarea>
        
        <button type="button" id="approveButton" class="float-left bg-green-500 hover:bg-green-700 text-white font-bold mt-3 py-2 px-4 rounded focus:outline-none focus:shadow-outline">Approve</button>
        <button type="button" id="disapproveButton" class="float-left bg-red-500 hover:bg-red-700 text-white font-bold mt-3 py-2 px-4 rounded focus:outline-none focus:shadow-outline">Disapprove</button>
  
    `;
  
    // Set modal content
    modalContent.innerHTML = modalHTML;
  
    // Disable all input fields
    const inputs = modalContent.querySelectorAll("input, textarea");
    inputs.forEach((input) => {
      input.disabled = true;
    });
  
    // Add event listeners to approve and disapprove buttons
    const approveButton = document.getElementById("approveButton");
    const disapproveButton = document.getElementById("disapproveButton");
  
    approveButton.addEventListener("click", async () => {
        showLoadingBar()
        console.log(segment._id)
        try {
            const response = await fetch('/explore/approve_edit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ segmentId: segment._id })
            });
            if (response.ok) {
                console.log("Job order approved");
                window.location.reload();
            } else {
                console.error('Failed to approve job order:', response.status);
            }
        } catch (error) {
            console.error("Error handling job order approval:", error);
        }
    });
  
    disapproveButton.addEventListener("click", () => {
        showDisapprovalReasonModal(segment._id);
    });
  
  } catch (error) {
    console.error("Error handling job order approval:", error);
  }
  }

  async function getPersonResponsible(userId) {
    try {
        const response = await fetch(`/explore/get_person_responsible/${userId}`);
        const user = await response.json();
        return user;
    } catch (error) {
        console.error("Error fetching user:", error);
        throw error; // Rethrow the error to handle it elsewhere if needed
    }
}

function showDisapprovalReasonModal(segmentId) {
  // Generate and insert the disapproval reason modal HTML into the body
  const disapprovalReasonModalHTML = `
      <div id="disapprovalReasonModal" class="fixed inset-0 flex items-center justify-center z-50 bg-gray-500 bg-opacity-75" style="z-index: 9999;">
          <div class="modal-container bg-white w-11/12 md:max-w-md rounded shadow-lg overflow-y-auto">
              <div class="py-4 px-10">
                  <label for="disapprovalReason" class="block text-sm font-medium leading-6 text-gray-900">Please provide a reason for disapproval:</label>
                  <textarea id="disapprovalReason" name="disapprovalReason" rows="4" class="form-textarea block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-orange-600 sm:text-sm sm:leading-6"></textarea>
                  <div class="flex justify-center">
                      <button id="confirmDisapprovalButton" class="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-7 rounded mt-5 mb-3">Confirm</button>
                      <button id="cancelDisapprovalButton" class="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-7 rounded mt-5 mb-3">Cancel</button>
                  </div>
              </div>
          </div>
      </div>
  `;

  // Append the modal HTML to the body
  document.body.insertAdjacentHTML('beforeend', disapprovalReasonModalHTML);

  // Add event listeners to the confirm and cancel buttons
  document.getElementById("confirmDisapprovalButton").addEventListener("click", async () => {
    const disapprovalReason = document.getElementById("disapprovalReason").value.trim(); // Trim whitespace from the reason

    if (disapprovalReason === "") { // Check if the trimmed reason is empty
        alert("Disapproval reason cannot be empty.");
        return;
    }
    showLoadingBar()
    try {
        const response = await fetch('/explore/disapprove_edit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ segmentId: segmentId, reason: disapprovalReason })
        });
        if (response.ok) {
            console.log("Job order disapproved");
            closeDisapprovalReasonModal();
            window.location.reload();
        } else {
            console.error('Failed to disapprove job order:', response.status);
        }
    } catch (error) {
        console.error("Error handling job order disapproval:", error);
    }
});

  document.getElementById("cancelDisapprovalButton").addEventListener("click", () => {
    closeDisapprovalReasonModal(); // Call the function to close the modal
});
}

function closeDisapprovalReasonModal() {
  const modal = document.getElementById("disapprovalReasonModal");
  console.log("cancelled")
  if (modal) {
      modal.remove();
  }
}
