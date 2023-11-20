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