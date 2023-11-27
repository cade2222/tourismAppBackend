function filterContent() {
  var selectedCategory = document.getElementById("category").value.toLowerCase();
  var searchQuery = document.getElementById("search").value.toLowerCase();
  var dataRows = document.getElementById("dataBody").getElementsByTagName("tr");

  for (var i = 0; i < dataRows.length; i++) {
      var dataRow = dataRows[i];
      var eventName = dataRow.cells[0].innerText.toLowerCase(); // Assuming event name is in the first cell
      var eventCategory = dataRow.cells[1].innerText.toLowerCase(); // Assuming category is in the second cell

      // Assuming the category is the event ID
      var categoryMatch = selectedCategory === "all" || eventCategory === selectedCategory;
      var searchMatch = eventName.includes(searchQuery);

      if (categoryMatch && searchMatch) {
          dataRow.style.display = "table-row";
      } else {
          dataRow.style.display = "none";
      }
  }
}
