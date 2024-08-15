var potholes; // Declare the variable here
var segments; // Declare the variable for segments

function display_map(mapboxAccessToken, potholes, segments, mid, role, userId) {
  console.log("ROLE", role);
  console.log("USERID", userId)

  if (!mapboxAccessToken) {
    console.error("Mapbox token is not defined.");
    return;
  }

  // Initialize Mapbox
  mapboxgl.accessToken = mapboxAccessToken;
  var map = new mapboxgl.Map({
    container: "map",
    style: "mapbox://styles/mapbox/streets-v12",
    center: mid == null ? [121.0359, 14.5794] : [mid[0], mid[1]], // Default center
    zoom: mid == null ? 16 : 20,
    bearing: -17.6,
    pitch: 45,
  });

  map.segments = [];
  map.potholes = [];
  var segmentFilter = "None";
  displaySegments(map, segments, role, userId, segmentFilter);
  displayPotholes(map, potholes, segments);
  //displayHeatmap(map,segments);

  // Add navigation control

  var segmentsVisible = true; // Flag to track the visibility of segments
  var potholesVisible = false;
  //var heatMapVisible = false;
  document
    .getElementById("showPotholesButton")
    .addEventListener("click", function () {
      closeModal();
      segment_id = document.getElementById("showPotholesButton").value;
      segment_potholes = [];
      potholes.forEach(function (pothole) {
        if (pothole.segment_id == segment_id) segment_potholes.push(pothole);
      });
      displayPotholes(map, segment_potholes, segments);
      document
        .getElementById("toggleSegmentsButtonLabel")
        .classList.remove("bg-orange-200");
      document
        .getElementById("toggleSegmentsButtonLabel")
        .classList.add("bg-slate-200");
      document
        .getElementById("togglePotholesButtonLabel")
        .classList.add("bg-orange-200");
      document
        .getElementById("togglePotholesButtonLabel")
        .classList.remove("bg-slate-200");
      segmentsVisible = false;
      potholesVisible = true;
      hideMarkers(map.segments);

      toggleMarkers(map.potholes, potholesVisible);
    });
  document
    .getElementById("toggleSegmentsButton")
    .addEventListener("click", function () {
      toggleSegments();
    });
  function toggleSegments() {
    // Get the map layer by ID

    // Toggle the visibility of the segments layer
    if (!segmentsVisible) {
      map.setLayoutProperty("segments-line-layer", "visibility", "visible");
      document
        .getElementById("toggleSegmentsButtonLabel")
        .classList.add("bg-orange-200");
      document
        .getElementById("toggleSegmentsButtonLabel")
        .classList.remove("bg-slate-200");
      document
        .getElementById("togglePotholesButtonLabel")
        .classList.remove("bg-orange-200");
      document
        .getElementById("togglePotholesButtonLabel")
        .classList.add("bg-slate-200");
      segmentsVisible = true;
      potholesVisible = false;
      hideMarkers(map.potholes);
    }
    toggleMarkers(map.segments, segmentsVisible);
  }

  document
    .getElementById("togglePotholesButton")
    .addEventListener("click", function () {
      togglePotholes();
    });

  function togglePotholes() {
    // Toggle the visibility of the potholes layer
    if (!potholesVisible) {
      displayPotholes(map, potholes, segments);
      map.setLayoutProperty("segments-line-layer", "visibility", "none");
      document
        .getElementById("toggleSegmentsButtonLabel")
        .classList.remove("bg-orange-200");
      document
        .getElementById("toggleSegmentsButtonLabel")
        .classList.add("bg-slate-200");
      document
        .getElementById("togglePotholesButtonLabel")
        .classList.add("bg-orange-200");
      document
        .getElementById("togglePotholesButtonLabel")
        .classList.remove("bg-slate-200");
      segmentsVisible = false;
      potholesVisible = true;
      hideMarkers(map.segments);
    }
    toggleMarkers(map.potholes, potholesVisible);
  }
  function hideMarkers(markers) {
    markers.forEach((marker) => {
      marker.getElement().style.display = "none";
    });
  }

  function toggleMarkers(markers, visible) {
    markers.forEach((marker) => {
      marker.getElement().style.display = visible ? "block" : "none";
    });
  }

  const statusDropdown = document.getElementById('statusDropdown');
  console.log(`Selected Layer: ${this.value}`);
statusDropdown.addEventListener('change', function () {
  console.log(`Selected Layer: ${this.value}`);
  if (map.segments && map.segments.length > 0) {
    map.segments.forEach((marker) => {
      if (marker.getElement().value.job_order_status !== this.value) {
        marker.getElement().style.display = "none";
      } else {
        marker.getElement().style.display = "block"; // Show the marker if it matches the value
      }
      if (this.value == "none"){
        marker.getElement().style.display = "block";
      }
    });
  }
});

const priorityLevelDropdown = document.getElementById('priorityLevelDropdown');
console.log(`Selected priorityLevelDropdown: ${this.value}`);
priorityLevelDropdown.addEventListener('change', function () {
console.log(`Selected priorityLevelDropdown: ${this.value}`);
if (map.segments && map.segments.length > 0) {
  map.segments.forEach((marker) => {
    if(this.value == "High"){
      if(marker.getElement().value.priority_score >= 0.7 && marker.getElement().value.priority_score <=1 ){
        marker.getElement().style.display = "block";
      }
      else{
        marker.getElement().style.display = "none";
      }
    }
    else if(this.value == "Medium-High"){
      if(marker.getElement().value.priority_score >= 0.4 && marker.getElement().value.priority_score < 0.7){
        marker.getElement().style.display = "block";
      }
      else{
        marker.getElement().style.display = "none";
      }
    }
    else if(this.value == "Medium-Low"){
      if(marker.getElement().value.priority_score >= 0.2 && marker.getElement().value.priority_score < 0.4){
        marker.getElement().style.display = "block";
      }
      else{
        marker.getElement().style.display = "none";
      }
    }
    else if(this.value == "Low"){
      if(marker.getElement().value.priority_score < 0.2){
        marker.getElement().style.display = "block";
      }
      else{
        marker.getElement().style.display = "none";
      }
    }
    else if(this.value == "none"){
      marker.getElement().style.display = "block";
    }
  });
}
});
if (segment.priority_score >= 0.7) {
  
} else if (segment.priority_score >= 0.4) {
  lineColor = "orange"; // Orange for Medium-High Priority
} else if (segment.priority_score >= 0.2) {
  lineColor = "yellow"; // Yellow for Medium-Low Priority
} else {
  lineColor = "green"; // Green for Low Priority
}


}
function isInRange(value, min, max) {
  return value >= min && value <= max;
}

// Function to display individual potholes

function clearPotholes(map) {
  // Remove all existing pothole markers from the map
  if (map.potholes && map.potholes.length > 0) {
    map.potholes.forEach((marker) => {
      marker.remove();
    });
    // Clear the array storing references to the pothole markers
    map.potholes = [];
  }
}

function clearSegments(map) {
  if (map.segments && map.segments.length > 0) {
    map.segments.forEach((marker) => {
      marker.remove();
    });

  }

}
function displayPotholes(map, potholes, segments) {
  let unresolvedPotholes = [];
  console.log(potholes);
  clearPotholes(map);
  for (let i = 0; i < potholes.length; i++) {
    let pothole = potholes[i];

    // Find the segment corresponding to this pothole
    let segment = segments.find(
      (segment) => segment._id === pothole.segment_id
    );

    // Check if the segment exists and its status is not resolved
    if (segment && segment.job_order.status !== "Resolved") {
      // Add the pothole to the unresolvedPotholes array
      unresolvedPotholes.push(pothole);
    }
  }
  console.log("unresolved", unresolvedPotholes);
  unresolvedPotholes.forEach((pothole) => {
    // Customize this part based on the structure of your pothole data
    var potholeCoordinates = [pothole.longitude, pothole.latitude];

    var customIcon = document.createElement("div");
    customIcon.className =
      "custom-marker w-12 h-12 bg-center bg-no-repeat rounded-full cursor-pointer";

    // Customize the image path based on the pothole status or other relevant data
    const imagePath = "static/images/pothole.png";

    customIcon.style.backgroundImage = `url(${imagePath})`;
    customIcon.style.backgroundSize = "70% 70%";

    var marker = new mapboxgl.Marker({
      element: customIcon,
    })
      .setLngLat(potholeCoordinates)
      .addTo(map);
    marker.getElement().style.display = "none";
    marker.getElement().addEventListener("click", function () {
      // Customize this part based on what you want to happen when a pothole marker is clicked
      openPotholeModal(pothole);
    });

    map.potholes.push(marker);
  });
}





function displaySegments(map, segments, role, userId) {


  console.log(segments);
  let unresolved = [];
  segments.forEach((segment) => {
    if (segment.job_order.status != "Resolved") {

        unresolved.push(segment);
    }
  
  });

  map.on("style.load", function () {
    var features = unresolved.map((segment) => {
      return {
        type: "Feature",
        geometry: {
          type: "LineString",
          coordinates: segment.snapped_to_road_points.map((point) => [
            point.location.longitude,
            point.location.latitude,
          ]),
        },
        properties: {
          priority_score: segment.priority_score,
          job_order_status: segment.job_order.status,
        },
      };
    });

    map.addSource("segments-source", {
      type: "geojson",
      data: {
        type: "FeatureCollection",
        features: features,
      },
    });

    map.addLayer({
      id: "segments-line-layer",
      type: "line",
      source: "segments-source",
      layout: {
        "line-join": "round",
        "line-cap": "round",
      },
      paint: {
        "line-color": [
          "case",
          [">=", ["get", "priority_score"], 0.7],
          "#FF0000",
          [">=", ["get", "priority_score"], 0.4],
          "#FFA500",
          [">=", ["get", "priority_score"], 0.2],
          "#FFFF00",
          "#008000",
        ],
        "line-width": 15,
      },
    });

    features.forEach((feature, index) => {
      var midpoint = feature.geometry.coordinates[0];
      if (feature.geometry.coordinates.length > 1) {
        midpoint = calculateMidpoint(feature.geometry.coordinates);
      }
      console.log("MIDPOINT: ", midpoint)
      var customIcon = document.createElement("div");
      customIcon.className =
        "custom-marker w-12 h-12 bg-center bg-no-repeat rounded-full cursor-pointer";
      const status = feature.properties.job_order_status;
      var imagePath;
      if (status == "In Progress") {
        imagePath = "static/images/wip.png";
      } else if (status == "For Approval") {
        imagePath = "static/images/testing.png";
      } else {
        imagePath = "static/images/road.png";
      }

      customIcon.style.backgroundImage = `url(${imagePath})`;
      customIcon.style.backgroundSize = "70% 70%";

      // Adding a red circle on top of the icon
      var circle = document.createElement("div");
      circle.className =
        "w-4 h-4 rounded-full absolute top-0 left-1/3 transform -translate-x-1/2";
      circle.style.backgroundColor =
        feature.properties.priority_score >= 0.7
          ? "#FF0000"
          : feature.properties.priority_score >= 0.4
            ? "#FFA500"
            : feature.properties.priority_score >= 0.2
              ? "#FFFF00"
              : "#008000";

      // Append the circle to the custom icon
      customIcon.appendChild(circle);

      var marker = new mapboxgl.Marker({
        element: customIcon,
        color:
          feature.properties.priority_score >= 0.7
            ? "#FF0000"
            : feature.properties.priority_score >= 0.4
              ? "#FFA500"
              : feature.properties.priority_score >= 0.2
                ? "#FFFF00"
                : "#008000",
      })
        .setLngLat(midpoint)
        .addTo(map);
      marker.getElement().value=feature.properties;
      console.log(marker.getElement().value)
      marker.getElement().addEventListener(
        "click",
        (function (segment) {
          return function () {
            map.flyTo({
              center: marker.getLngLat(),
              zoom: 20,
            })
            openModal(segment, role, userId);
          };
        })(unresolved[index])
      );
      map.segments.push(marker);
    });
  });
}

// Calculate the midpoint of an array of points
function calculateMidpoint(points) {
  var totalPoints = points.length;
  var sumLat = 0;
  var sumLng = 0;

  for (i = 0; i < totalPoints; i++) {
    sumLat += points[i][1];
    sumLng += points[i][0];
  }

  var midpoint = [sumLng / totalPoints, sumLat / totalPoints];

  return midpoint;
}

function openPotholeModal(pothole) {
  console.log("pothole opened");
  var potholeModal = document.getElementById("potholeModal");
  var potholeModalContent = document.getElementById("pothole-modal-content");
  console.log(pothole.segment_id);

  var modalHTML = `
    <div class="divide-y divide-gray-100">
        <div class="px-4 py-1 ml-2 sm:grid sm:grid-cols-4 sm:gap-4 sm:px-0">
            <dt class="text-sm font-medium leading-6 text-gray-900 sm:col-span-2">Pothole ID</dt>
            <dd class="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">${pothole._id}</dd>
            <dt class="text-sm font-medium leading-6 text-gray-900 sm:col-span-2">Segment ID</dt>
            <dd class="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">${pothole.segment_id}</dd>
        </div>
        <div class="px-4 py-1 ml-2 sm:grid sm:grid-cols-4 sm:gap-4 sm:px-0 sm:items-center">
            <dt class="text-sm font-medium leading-6 text-gray-900 sm:col-span-2">Pothole Image</dt>
            <dd class="mt-1 sm:col-span-2 sm:mt-0" style="padding-right: 1rem;">
                <img src="static/frames/${pothole.filename}" alt="Pothole Image" style="height: 50%; width: 100%;" class="float-right">
            </dd>
        </div>
    </div>
    `;

  potholeModalContent.innerHTML = modalHTML;

  potholeModal.classList.remove("hidden");
}
// Function to open the modal with segment information
function openModal(segment, role, userId) {
  document.getElementById("showPotholesButton").classList.remove("hidden");
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
    <p class = "font-bold text-white">${segment.priority_level
    } (${segment.priority_score.toFixed(3)})</p>
    </div>
    <dl class="divide-y  divide-gray-100">
            <div class="px-4 py-1 ml-2 sm:grid sm:grid-cols-4 sm:gap-4 sm:px-0">
                <dt class="text-sm font-medium leading-6 text-gray-900 sm:col-span-2">Segment ID</dt>
                <dd class="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">${segment._id
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
                <dd class="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">${segment.nearby_establishments.length
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
                <dd class="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">${segment.population_density
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
                <dd class="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">${segment.traffic_volume
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
                <dd class="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">${segment.points.length
    }</dd>
            </div>
            <div class="px-4 py-1 ml-2 sm:grid sm:grid-cols-4 sm:gap-4 sm:px-0">
                <div class="tooltip sm:col-span-2">
                    <dt class="text-sm font-medium leading-6 text-gray-900">
                        No of concerns
                        <span class="tooltip-icon">i</span>
                    </dt>
                    <span class="tooltiptext">The number of concerns is a critical factor as it shows how many people have reported the same pothole.</span>
                </div>
                <dd class="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">2</dd>
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

  document.getElementById("showPotholesButton").value = segment._id;

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

// Function to hide the loading bar
function hideLoadingBar() {
  const loadingBar = document.getElementById("loading-bar");
  loadingBar.classList.add("hidden");
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



async function jobOrderApproval(segment) {
  const showPotholesButton = document.getElementById("showPotholesButton");
  const modal = document.getElementById("myModal");
  const modalContent = document.getElementById("modal-content");

  // Hide the 'Show Potholes' button
  console.log(segment.job_order);
  showPotholesButton.classList.add("hidden");
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

function showDisapprovalReasonModal(segmentId) {
  // Generate and insert the disapproval reason modal HTML into the body
  const disapprovalReasonModalHTML = `
      <div id="disapprovalReasonModal" class="fixed inset-0 flex items-center justify-center z-50 bg-gray-500 bg-opacity-75">
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



function createJobOrder(segment) {
  const showPotholesButton = document.getElementById("showPotholesButton");
  const modal = document.getElementById("myModal");
  const modalContent = document.getElementById("modal-content");

  // Hide the 'Show Potholes' button
  showPotholesButton.classList.add("hidden");

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
          <input type="hidden" id="fromWhere" name="fromWhere" value = "explore">
            <label for="segmentId">Segment ID:</label>
            <input type="text" id="segmentId" name="segmentId" required value="${segment._id
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
            <label for="job_order_document">Job Order Document:</label>
            <input type="file" name="job_order_document" id="job_order_document" accept=".pdf" class="block mb-2 w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-orange-600 sm:text-sm sm:leading-6"/>
            <button type="submit" class="float-left bg-red-500 hover:bg-red-700 text-white font-bold mt-3 py-2 px-4 rounded focus:outline-none focus:shadow-outline">Submit</button>
          </form>
        `;

      // Set modal content
      modalContent.innerHTML = modalHTML;
    })
    .catch((error) => {
      console.error("Error fetching users:", error);
    });
}



function editJobOrder(segment) {

  const showPotholesButton = document.getElementById("showPotholesButton");
  const modal = document.getElementById("myModal");
  const modalContent = document.getElementById("modal-content");

  // Hide the 'Show Potholes' button
  showPotholesButton.classList.add("hidden");
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
          <form id="jobOrderForm" action="/explore/submit_job_order" method="post">
          <input type="hidden" id="fromWhere" name="fromWhere" value = "explore">
            <label for="segmentId">Segment ID:</label>
            <input type="text" id="segmentId" name="segmentId" required value="${segment._id
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
            <input type="date" id="completionDate" name="completionDate" min="${segment.job_order.start_date
        }" class="block mb-2 w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-orange-600 sm:text-sm sm:leading-6" required value="${segment.job_order.completion_date
        }">
            
            <label for="editReason" class="block text-sm font-medium leading-6 text-gray-900">Reason for reschedule or reassignment:</label>
            <textarea id="editReason" name="editReason" rows="4" class="form-textarea block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-orange-600 sm:text-sm sm:leading-6" required></textarea>
            
            <button type="submit" class="float-left bg-red-500 hover:bg-red-700 text-white font-bold mt-3 py-2 px-4 rounded focus:outline-none focus:shadow-outline">Submit</button>
          </form>
        `;

      // Set modal content
      modalContent.innerHTML = modalHTML;
    })
    .catch((error) => {
      console.error("Error fetching users:", error);
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

// Function to close the modal
function closeModal() {
  var modal = document.getElementById("myModal");
  modal.classList.add("hidden"); // Hide the modal
}

function closePotholeModal() {
  var modal = document.getElementById("potholeModal");
  modal.classList.add("hidden"); //
}
var segmentFilter = "For Approval";





