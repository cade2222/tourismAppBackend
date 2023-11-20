let counter = 1; // Initial value

function compileData() {
  const city = document.getElementById("city").value;
  const startDate = document.getElementById("startDate").value;
  const endDate = document.getElementById("endDate").value;

  const dateTimeCell = document.getElementById("dateTimeCell");
  const userIDCell = document.getElementById("userIDCell");
  const cityCell = document.getElementById("cityCell");
  const locationCell = document.getElementById("locationCell");

  const currentDate = new Date();
  const formattedDate = currentDate.toLocaleDateString();
  const formattedTime = currentDate.toLocaleTimeString();

  dateTimeCell.innerHTML = `${formattedDate} ${formattedTime}`;
  userIDCell.innerHTML = counter++;
  cityCell.innerHTML = city;
  locationCell.innerHTML = `${city} (${startDate} to ${endDate})`;
}
