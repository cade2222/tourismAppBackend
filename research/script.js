async function submitForm() {
    // const username = document.getElementById("loginUsername").value;
    // const password = document.getElementById("loginPassword").value;
    // const base64Credentials = btoa(`${username}:${password}`);

    // const headersList = {
    //   "Accept": "*/*",
    //   "User-Agent": "Thunder Client (https://www.thunderclient.com)",
    //   "Authorization": `Basic ${base64Credentials}`
    // };
  
    // try {
    //   const response = await fetch("https://api.explorecityapp.com/auth", {
    //     method: "GET",
    //     headers: headersList
    //   });
  
    //   if (response.ok) {
    //     const data = await response.text();
    //     console.log("Authentication successful:", data);
    //   } else {
    //     console.error("Authentication failed:", response.status, response.statusText);
    //   }
    // } catch (error) {
    //   console.error("Error during authentication:", error.message);
    // }
    window.location.href = "howdy.html";
}

function filterContent() {
    var selectedCategory = document.getElementById("category").value.toLowerCase();
    var searchQuery = document.getElementById("search").value.toLowerCase();
    var contentItems = document.getElementsByClassName("content-item");
  
    for (var i = 0; i < contentItems.length; i++) {
      var contentItem = contentItems[i];
      var itemCategory = contentItem.classList.item(1).toLowerCase(); // Assuming the category class is the second class
  
      var categoryMatch = selectedCategory === "all" || itemCategory === selectedCategory;
      var searchMatch = contentItem.innerText.toLowerCase().includes(searchQuery);
  
      if (categoryMatch && searchMatch) {
        contentItem.style.display = "block";
      } else {
        contentItem.style.display = "none";
      }
    }
  }