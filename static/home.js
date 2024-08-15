// JavaScript code to fetch data from Flask and generate Plotly bar graph
fetch('/priority_counts')
    .then(response => response.json())
    .then(priorityData => {
        var priority_labels = Object.keys(priorityData);
        var priority_values = Object.values(priorityData);
        var colors = priority_labels.map(priority => {
            if (priority === "High Priority Road Segment") {
                return "#FF0000"; // Red for High Priority
            } else if (priority === "Medium-High Priority Road Segment") {
                return "#FFA500"; // Orange for Medium-High Priority
            } else if (priority === "Medium-Low Priority Road Segment") {
                return "#FFFF00"; // Yellow for Medium-Low Priority
            } else {
                return "#008000"; // Green for Low Priority
            }
        });
        var pieData = [{
            labels: priority_labels,
            values: priority_values,
            type: 'pie',
            marker: {
                colors: colors
            }
        }];
        var layout = {
            title: 'Priority Distribution',
            annotations: [
                {
                    x: 0.5,
                    y: 1.15,
                    xref: 'paper',
                    yref: 'paper',
                    text: 'Distribution of Road Segments by Priority',
                    showarrow: false,
                    font: {
                        family: 'Arial, sans-serif',
                        size: 14,
                        color: '#000'
                    }
                }
            ],
            legend: {
                x: 1,
                y: 1,
                traceorder: 'normal',
                font: {
                    family: 'Arial, sans-serif',
                    size: 12,
                    color: '#000'
                },
                bgcolor: '#E2E2E2',
                bordercolor: '#FFFFFF',
                borderwidth: 2
            }
        };
        Plotly.newPlot('priority-pie-chart', pieData, layout);
        var plotlyData = [{
            x: priority_labels,
            y: priority_values,
            type: 'bar',
            marker: {
                color: colors
            }
        }];
        var layout = {
            title: 'Priority Counts',
            xaxis: {
                title: 'Priority Level'
            },
            yaxis: {
                title: 'Count'
            },
            annotations: [
                {
                    x: 0.5,
                    y: 1.15,
                    xref: 'paper',
                    yref: 'paper',
                    text: 'Total Number of Road Segments with Potholes: ' + priority_values.reduce((acc, cur) => acc + cur, 0),
                    showarrow: false,
                    font: {
                        family: 'Arial, sans-serif',
                        size: 14,
                        color: '#000'
                    }
                }
            ],
            legend: {
                x: 1,
                y: 1,
                traceorder: 'normal',
                font: {
                    family: 'Arial, sans-serif',
                    size: 12,
                    color: '#000'
                },
                bgcolor: '#E2E2E2',
                bordercolor: '#FFFFFF',
                borderwidth: 2
            }
        };
        Plotly.newPlot('priority-chart', plotlyData, layout);

    });

fetch('/potholes')
    .then(response => response.json())
    .then(potholes => {

        fetch('/segments')
    .then(response => response.json())
    .then(segments => {

        let unresolvedPotholes = [];

        for (let i = 0; i < potholes.length; i++) {
            let pothole = potholes[i];
            
            // Find the segment corresponding to this pothole
            let segment = segments.find(segment => segment._id === pothole.segment_id);
    
            // Check if the segment exists and its status is not resolved
            if (segment && segment.job_order.status !== "Resolved") {
                // Add the pothole to the unresolvedPotholes array
                unresolvedPotholes.push(pothole);
            }
        }
        console.log(unresolvedPotholes);
        document.getElementById("noPotholes").textContent = String(unresolvedPotholes.length);
        // Take only the top 5 segments
        createTopSegmentsPart(segments);
        createTopBarangaySegments(segments);
        // idk if this is faster since it doesnt query the db again, but same functionality as using the endpoint
        // createPriorityCounts(segments);
    })
    .catch(error => console.error('Error fetching segments:', error));
    })
    .catch(error => console.error('Error fetching potholes:', error));



function createTopSegmentsPart(segments) {
    
    let unResolvedSegments = [];
    segments.forEach( segment =>{
        if(segment.job_order.status != "Resolved")
        {unResolvedSegments.push(segment);}
    })
    unResolvedSegments.sort((a, b) => b.priority_score - a.priority_score);
    let topSegments = unResolvedSegments.slice(0, 10);

    topSegments.forEach(segment => {
        let lineColor;
        if (segment.priority_score >= 0.7) {
            lineColor = "red"; // Red for High Priority
        } else if (segment.priority_score >= 0.4) {
            lineColor = "orange"; // Orange for Medium-High Priority
        } else if (segment.priority_score >= 0.2) {
            lineColor = "yellow"; // Yellow for Medium-Low Priority
        } else {
            lineColor = "green"; // Green for Low Priority
        }

        // Create elements with the updated lineColor
        let table = document.getElementById('top-segments-table');
        let row = table.insertRow();

        let segmentIdCell = row.insertCell(0);
        segmentIdCell.innerText = segment._id.substr(segment._id.length - 5);;

        // Remove 'Road Segment' suffix from priority_level
        let priorityLevel = segment.priority_level.replace(' Road Segment', '');

        let priorityCell = row.insertCell(1);
        priorityCell.innerHTML = `<div class="bg-${lineColor}-600 rounded-lg p-1 mx-4 shadow-md px-4 text-center">
                                    <p class="font-bold text-white">${priorityLevel} (${segment.priority_score.toFixed(3)})</p>
                                  </div>`;
        // fix to add all roads
        let roadCell = row.insertCell(2);
        roadCell.innerHTML = `<p class="font-bold text-black">${segment.roads_affected[0]}</p>`;

        let status = segment.job_order['status'];
        console.log('status',status)
        let text = "No"
        if(status == "In Progress" ){
            text = "Yes"
        }
        let jobOrderCell = row.insertCell(3);
        jobOrderCell.innerHTML = `<p class="font-bold text-black"> ${text}</p>`;

        let viewButton = row.insertCell(4);
        viewButton.innerHTML = `<a href="/explore?segment_id=${segment._id}" class="bg-blue-600 rounded-lg p-1 mx-4 shadow-md px-4 text-center font-bold text-white" value="View">View</a>`;


    });
}

function createTopBarangaySegments(segments) {
    let barangays = {};

    segments.forEach(segment => {
        if (segment.job_order && segment.job_order.status !== "Resolved" && segment.barangays_affected && Array.isArray(segment.barangays_affected)) {
            segment.barangays_affected.forEach(barangay => {
                barangays[barangay] = (barangays[barangay] || 0) + 1;
            });
        }
    });
    

    const sortedBarangays = Object.entries(barangays).sort((a, b) => b[1] - a[1]);

    const topBarangays = sortedBarangays.slice(0, 5);

    topBarangays.forEach(([barangay, count]) => {
        let table = document.getElementById('top-barangay-segments-table');
        let row = table.insertRow();

        let barangayCell = row.insertCell(0);
        barangayCell.innerText = barangay;

        let countCell = row.insertCell(1);
        countCell.innerText = count.toString();
    });
    
}
