async function submitForm() {
    username = document.getElementById("loginUsername").value;
    password = document.getElementById("loginPassword").value;
    base64Credentials = btoa(`${username}:${password}`);
    authorize = `Basic ${base64Credentials}`

    let headersList = {
      "Accept": "*/*",
      "User-Agent": "Thunder Client (https://www.thunderclient.com)",
      "Authorization": authorize
     }
     
     let response = await fetch("https://api.explorecityapp.com/auth", { 
       method: "GET",
       headers: headersList
     });
     
     let data = await response.text();
     console.log(data);
           
    window.location.href = "data.html";  
}

let places;
let visits;
let events; 

// New function to fetch events, places, and visits and populate the table
async function getEvents() {
  let headersList = {
      "Accept": "*/*",
      "User-Agent": "Thunder Client (https://www.thunderclient.com)",
      "Authorization": "Basic ZXhhbXBsZTpQYXNzd2QxMjMh"
  }

  let response = await fetch("https://api.explorecityapp.com/research", {
      method: "GET",
      headers: headersList
  });

  let data = await response.json();
  console.log(data);

  places = data.places;
  visits = data.visits;
  events = data.events;
  // console.log(places);
  // console.log(visits);

  // Populate the event dropdown
  populateEventDropdown(data.events);

  // Call the getPlacetypes function to populate the placetype dropdown
  await getPlacetypes();

  // Populate the table based on the selected event and placetype
  populateTable(data.events, data.places, data.visits);
}

let placetype;

// New function to populate the placetype dropdown
async function getPlacetypes() {
  let headersList = {
      "Accept": "*/*",
      "User-Agent": "Thunder Client (https://www.thunderclient.com)",
      "Authorization": 'Basic ZXhhbXBsZTpQYXNzd2QxMjMh'
  }

  let response = await fetch("https://api.explorecityapp.com/research/placetypes", {
      method: "GET",
      headers: headersList
  });

  let data = await response.json();
  placetype = data

  // Get the dropdown element
  let placetypeDropdown = document.getElementById("placetype");

  // Clear existing options
  placetypeDropdown.innerHTML = '<option value="all">All Placetypes</option>';

  // Populate the dropdown with placetypes
  data.forEach(placetype => {
      let option = document.createElement("option");
      option.value = placetype;
      option.text = placetype;
      placetypeDropdown.add(option);
  });
}

async function getCityFromPlaceId(placeId) {
  const apiKey = 'AIzaSyDPFDQebw-Qwis6bU68K_-pmylM4pJc88k';
  const apiUrl = `https://maps.googleapis.com/maps/api/place/details/json?place_id=${placeId}&key=${apiKey}`;

  try {
    const response = await fetch(apiUrl);
    const dat = await response.json();

    if (data.status === 'OK') {
      const addressComponents = dat.result.address_components;
      const cityComponent = addressComponents.find(component =>
        component.types.includes('locality')
      );

      if (cityComponent) {
        return cityComponent.long_name;
      } else {
        throw new Error('City not found in address components.');
      }
    } else {
      throw new Error(`Error in API response: ${dat.status}`);
    }
  } catch (error) {
    console.error('Error fetching city:', error.message);
    return null;
  }
}

// New function to populate the event dropdown
function populateEventDropdown(events) {
  // Get the dropdown element
  let eventDropdown = document.getElementById("category");

  // Clear existing options
  eventDropdown.innerHTML = '<option value="all">All Events</option>';

  // Populate the dropdown with events
  events.forEach(event => {
      let option = document.createElement("option");
      option.value = event.displayname;
      option.text = event.displayname;
      eventDropdown.add(option);
  });
}

var originalRows = [];

// New function to populate the table with city information
async function populateTable(events, places, visits) {
  let selectedEvent = document.getElementById("category").value;
  let selectedPlacetype = document.getElementById("placetype").value;

  // Clear existing rows
  let dataBody = document.getElementById("dataBody");
  dataBody.innerHTML = '';

  // Create header row with column names
  let headerRow = dataBody.insertRow();
  let cellHeaderCity = headerRow.insertCell(0);
  let cellHeaderEvent = headerRow.insertCell(1);
  let cellHeaderPlace = headerRow.insertCell(2);
  let cellHeaderPlaceType = headerRow.insertCell(3);
  let cellHeaderVisit = headerRow.insertCell(4);

  // Set header cell values
  cellHeaderCity.innerText = "City";
  cellHeaderEvent.innerText = "Event";
  cellHeaderPlace.innerText = "Place";
  cellHeaderPlaceType.innerText = "Place Type";
  cellHeaderVisit.innerText = "Visits";

  // Use a set to keep track of unique combinations of event and place
  let uniqueCombinations = new Set();

  // Iterate through events
  for (let event of events) {
      // Check if the event matches the selected event
      if (selectedEvent === "all" || selectedEvent === event.id) {
          // Filter places based on the selected placetype
          let filteredPlaces = places.filter(place => selectedPlacetype === "all" || place.types.includes(selectedPlacetype));

          // Iterate through filtered places
          for (let place of filteredPlaces) {
              // Create a unique key for the combination of event and place
              let combinationKey = `${event.id}-${place.id}`;

              // Check if the combination has already been added to the set
              if (!uniqueCombinations.has(combinationKey)) {
                  // Create a row for each unique combination
                  let row = dataBody.insertRow();
                  let cellCity = row.insertCell(0);
                  let cellEvent = row.insertCell(1);
                  let cellPlace = row.insertCell(2);
                  let cellPlaceType = row.insertCell(3);
                  let cellVisit = row.insertCell(4);

                  // Update cells with event-specific data
                  // console.log(place.id)              
                  // cellCity.innerText = await getCityFromPlaceId(place.id);                  
                  // console.log(cellCity.innerText)
                  cellEvent.innerText = event.displayname;
                  cellPlace.innerText = place.name;

                  // Check if there are visits for the current place in the current event
                  if (visits[event.id] && visits[event.id][place.id]) {
                      cellVisit.innerText = visits[event.id][place.id];
                  } else {
                      // If no visits for the current place, indicate 0 visits
                      cellVisit.innerText = '0';
                  }

                  // Update cellPlaceType with types information
                  cellPlaceType.innerText = place.types.join(', '); // Join types with a comma and space

                  // Add the combination to the set to mark it as processed
                  uniqueCombinations.add(combinationKey);
              }
          }
      }
  }
  originalRows = Array.from(dataBody.getElementsByTagName("tr"));
}

function filterContent() {
  var selectedCategory = document.getElementById("category").value.toLowerCase();
  var selectedPlacetype = document.getElementById("placetype").value.toLowerCase();
  var searchQuery = document.getElementById("search").value.toLowerCase();
  var dataBody = document.getElementById("dataBody");

  for (var i = 0; i < originalRows.length; i++) {
    var dataRow = originalRows[i];
    var eventName = dataRow.cells[1].innerText.toLowerCase();  // Assuming event name is in the second column
    var placeName = dataRow.cells[2].innerText.toLowerCase();  // Assuming place name is in the third column
    var placeType = dataRow.cells[3].innerText.toLowerCase();  // Assuming place type is in the fourth column
    var visits = dataRow.cells[4].innerText.toLowerCase();      // Assuming visits is in the fifth column

    // Check if the event and placetype match the selected values
    var categoryMatch = selectedCategory === "all" || eventName.includes(selectedCategory);
    var placetypeMatch = selectedPlacetype === "all" || placeType.includes(selectedPlacetype);

    // Check if any field contains the search query
    var searchMatch = eventName.includes(searchQuery) ||
                      placeName.includes(searchQuery) ||
                      placeType.includes(searchQuery) ||
                      visits.includes(searchQuery);

    // Show or hide the row based on filter conditions
    dataRow.style.display = categoryMatch && placetypeMatch && searchMatch ? "" : "none";
  }
}


function generateBarGraph() {
  // Get the selected event
  let selectedEventName = document.getElementById("category").value;
  let selectedEvent = events.find(event => event.displayname === selectedEventName);
  console.log(selectedEvent.id)

  // Filter visits for the selected event
  let filteredVisits = visits[selectedEvent.id];

  const placeTypesAndVisits = {};

  placetype.forEach(function(key) {
        placeTypesAndVisits[key] = 0;
  });

  for (const visitKey in visits) {
    const visitData = visits[visitKey];
      
    // Iterate through the inner object of visitData
    for (const placeId in visitData) {

      const matchingPlace = places.find(place => place.id === placeId).types;
      console.log(matchingPlace)

      if (matchingPlace) {
        matchingPlace.forEach(placeType => {
          console.log(placeType)
          if (placeTypesAndVisits.hasOwnProperty(placeType)) {
            placeTypesAndVisits[placeType] += visitData[placeId] || 0;
          }
        });
      }      
    }
  }
  
  
  // Print the result
  console.log(placeTypesAndVisits);
  
// Sort the place types based on visit counts in descending order
const sortedPlaceTypes = Object.keys(placeTypesAndVisits).sort((a, b) => placeTypesAndVisits[b] - placeTypesAndVisits[a]);

// Extract the labels and data for the bar graph
const labels = sortedPlaceTypes;
const dataValues = sortedPlaceTypes.map(placeType => placeTypesAndVisits[placeType]);

// Create a new window and open an HTML document
const newWindow = window.open('', '_blank');
newWindow.document.write('<html><head><title>' + selectedEventName + ' Bar Graph</title></head><body>');

// Add a canvas element for the chart
newWindow.document.write('<canvas id="barGraph" width="400" height="400"></canvas>');

// Add the Chart.js library (make sure to include the library in your project)
newWindow.document.write('<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>');

// Add a script to generate the chart in the new window
newWindow.document.write('<script>');
newWindow.document.write(`
  var ctx = document.getElementById('barGraph').getContext('2d');
  var myBarChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ${JSON.stringify(labels)},
      datasets: [{
        label: 'Visits',
        data: ${JSON.stringify(dataValues)},
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1
      }]
    },
    options: {
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });
`);
newWindow.document.write('</script>');

newWindow.document.write('</body></html>');

// Make sure to close the document stream
newWindow.document.close();
}



function generatePieChart() {
  // Get the selected event
  let selectedEventName = document.getElementById("category").value;
  let selectedEvent = events.find(event => event.displayname === selectedEventName);

  // Filter visits for the selected event
  let filteredVisits = visits[selectedEvent.id];

  // Create a new object to store counts for the selected event
  const placeTypesAndVisits = {};

  // Initialize counts for each place type to 0
  placetype.forEach(function (key) {
      placeTypesAndVisits[key] = 0;
  });

  // Update the dictionary based on the visits data for the selected event
  for (const visitKey in filteredVisits) {
      const visitCount = filteredVisits[visitKey];
      const matchingPlace = places.find(place => place.id === visitKey);

      if (matchingPlace && matchingPlace.types) {
          matchingPlace.types.forEach(placeType => {
              if (placeTypesAndVisits.hasOwnProperty(placeType)) {
                  placeTypesAndVisits[placeType] += visitCount || 0;
              }
          });
      }
  }

  // Extract the labels and data for the pie chart
  const labels = Object.keys(placeTypesAndVisits);
  const dataValues = Object.values(placeTypesAndVisits);

  // Create a new window and open an HTML document
  const newWindow = window.open('', '_blank');
  newWindow.document.write('<html><head><title>' + selectedEventName + ' Pie Chart</title></head><body>');

  // Add a canvas element for the chart
  newWindow.document.write('<canvas id="pieChart" width="400" height="400"></canvas>');

  // Add the Chart.js library (make sure to include the library in your project)
  newWindow.document.write('<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>');

  // Add a script to generate the chart in the new window
  newWindow.document.write('<script>');
  newWindow.document.write(`
      var ctx = document.getElementById('pieChart').getContext('2d');
      var myPieChart = new Chart(ctx, {
          type: 'pie',
          data: {
              labels: ${JSON.stringify(labels)},
              datasets: [{
                  data: ${JSON.stringify(dataValues)},
                  backgroundColor: [
                      'rgba(255, 99, 132, 0.8)',
                      'rgba(54, 162, 235, 0.8)',
                      'rgba(255, 206, 86, 0.8)',
                      'rgba(75, 192, 192, 0.8)',
                      'rgba(153, 102, 255, 0.8)',
                      'rgba(255, 159, 64, 0.8)'
                  ],
              }]
          },
          options: {
              // Your options here
          }
      });
  `);
  newWindow.document.write('</script>');

  newWindow.document.write('</body></html>');

  // Make sure to close the document stream
  newWindow.document.close();
}
