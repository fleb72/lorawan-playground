const chartInstances = {}; // Stocke les graphiques par canvasId

function drawChart(canvasId, dataPoints, label, borderColor, yAxisLabel, chartTitle) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  // Détruire l'ancien graphique s'il existe
  if (chartInstances[canvasId]) {
    chartInstances[canvasId].destroy();
  }

  // Créer le nouveau graphique et le stocker
  chartInstances[canvasId] = new Chart(ctx, {
    type: 'line',
    data: {
      datasets: [{
        label: label,
        data: dataPoints,
        borderColor: borderColor,
        backgroundColor: borderColor.replace('1)', '0.2)'),
        fill: false,
        tension: 0.3,
        pointRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          type: 'time',
          time: {
            unit: 'hour',
            tooltipFormat: 'HH:mm',
            displayFormats: { hour: 'HH:mm' }
          },
          title: {
            display: true,
            text: 'Heure'
          }
        },
        y: {
          title: {
            display: true,
            text: yAxisLabel
          }
        }
      },
      plugins: {
        title: {
          display: true,
          text: chartTitle
        }
      }
    }
  });
}
