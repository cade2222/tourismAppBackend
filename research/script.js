function filterContent() {
    var selectedCategory = document.getElementById("category").value.toLowerCase();
    var selectedPlacetype = document.getElementById("placetype").value.toLowerCase();
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
