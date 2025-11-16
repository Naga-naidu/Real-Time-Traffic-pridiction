function getPrediction() {
  fetch('http://127.0.0.1:5000/predict')
    .then(response => response.json())
    .then(data => {
      document.getElementById('prediction').textContent = "Traffic: " + data.prediction;
      document.getElementById('timestamp').textContent = "Updated: " + data.timestamp;
    })
    .catch(error => {
      document.getElementById('prediction').textContent = "Error fetching prediction";
      console.error("Error:", error);
    });
}