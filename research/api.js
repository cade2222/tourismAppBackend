let authorize = '';

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
           
    window.location.href = "howdy.html";
    
}

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

  // Populate the event dropdown
  populateEventDropdown(data.events);

  // Call the getPlacetypes function to populate the placetype dropdown
  await getPlacetypes();

  // Populate the table based on the selected event and placetype
  populateTable(data.events, data.places, data.visits);
}

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

function populateTable(events, places, visits) {
  let selectedEvent = document.getElementById("category").value;
  let selectedPlacetype = document.getElementById("placetype").value;

  // Clear existing rows
  let dataBody = document.getElementById("dataBody");
  dataBody.innerHTML = '';

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
          let cellEvent = row.insertCell(0);
          let cellPlace = row.insertCell(1);
          let cellPlaceType = row.insertCell(2);
          let cellVisit = row.insertCell(3);

          // Update cells with event-specific data
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
}

function filterContent() {
    var selectedCategory = document.getElementById("category").value.toLowerCase();
    console.log(selectedCategory);
    var selectedPlacetype = document.getElementById("placetype").value.toLowerCase();
    console.log(selectedPlacetype);
    var searchQuery = document.getElementById("search").value.toLowerCase();
    var dataRows = document.getElementById("dataBody").getElementsByTagName("tr");

    for (var i = 0; i < dataRows.length; i++) {
        var dataRow = dataRows[i];
        var eventName = dataRow.cells[0].innerText.toLowerCase();
        var placeName = dataRow.cells[1].innerText.toLowerCase();
        var placeType = dataRow.cells[2].innerText.toLowerCase();
        var visits = dataRow.cells[3].innerText.toLowerCase();

        // Check if the event and placetype match the selected values
        var categoryMatch = selectedCategory === "all" || eventName.includes(selectedCategory);
        var placetypeMatch = selectedPlacetype === "all" || placeType.includes(selectedPlacetype);

        // Check if any field contains the search query
        var searchMatch = eventName.includes(searchQuery) ||
            placeName.includes(searchQuery) ||
            placeType.includes(searchQuery) ||
            visits.includes(searchQuery);

        // Show the row if all conditions are met
        if (categoryMatch && placetypeMatch && searchMatch) {
            dataRow.style.display = "table-row";
        } else {
            dataRow.style.display = "none";
        }
    }
}
