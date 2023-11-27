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
     console.log(authorize);

      
    window.location.href = "howdy.html";
    
}

async function getPlacetypes() {
    console.log(authorize);
    let headersList = {
      "Accept": "*/*",
      "User-Agent": "Thunder Client (https://www.thunderclient.com)",
      "Authorization": 'Basic ZXhhbXBsZTpQYXNzd2QxMjMh'
     }
     
     let response = await fetch("https://api.explorecityapp.com/research/placetypes", { 
       method: "GET",
       headers: headersList
     });
     
     let data = await response.text();
     console.log(data);
  
  }


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

    let data = await response.json(); // Parse response as JSON
    console.log(data);

    // Clear existing rows and options
    let dataBody = document.getElementById("dataBody");
    dataBody.innerHTML = '';

    let categoryDropdown = document.getElementById("category");
    categoryDropdown.innerHTML = '<option value="all">All</option>'; // Reset dropdown with 'All' option

    // Assuming data structure is consistent
    for (let event of data.events) {
        // Create option for each event in the dropdown
        let option = document.createElement("option");
        option.value = event.id;  // Assuming event id can be used as a value
        option.text = event.displayname;
        categoryDropdown.add(option);

        // Create row for each event in the table
        let row = dataBody.insertRow();
        let cellEvent = row.insertCell(0);
        let cellPlace = row.insertCell(1);
        let cellVisit = row.insertCell(2);
        let cellPlaceType = row.insertCell(3);

        // Update cells with event-specific data
        cellEvent.innerText = event.displayname;
        // You may need to adjust the following lines based on your actual data structure
        cellPlace.innerText = '';  // No places in the provided data
        cellVisit.innerText = data.visits[event.id] ? 'Visited' : 'Not Visited';
        cellPlaceType.innerText = '';  // You can modify this based on your data structure
    }
}