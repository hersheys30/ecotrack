function palette() {
  return {
    s1: "#8a9e6e",
    s2: "#a9c087",
    s3: "#6e8a9e",
    grid: "rgba(255,255,255,.08)",
    text: "rgba(255,255,255,.92)",
    muted: "rgba(255,255,255,.70)",
  };
}

function baseChartOptions() {
  const p = palette();
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: p.muted, boxWidth: 10, boxHeight: 10 },
      },
      tooltip: {
        backgroundColor: "rgba(20,20,20,.95)",
        borderColor: "rgba(255,255,255,.10)",
        borderWidth: 1,
        titleColor: p.text,
        bodyColor: p.text,
      },
    },
    scales: {
      x: {
        ticks: { color: p.muted },
        grid: { color: p.grid },
      },
      y: {
        ticks: { color: p.muted },
        grid: { color: p.grid },
      },
    },
  };
}

window.EcoTrackCharts = { palette, baseChartOptions };

