let motionChart;

function fmtTime(epoch) {
  const d = new Date(epoch * 1000);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

async function fetchMotionSeries(hours) {
  const r = await fetch(`/api/motion_series?hours=${hours}`);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  const j = await r.json();
  return {
    labels: j.t.map(fmtTime),
    data: j.v,
    bucketSeconds: j.bucket_seconds
  };
}

async function renderMotion(hours) {
  const series = await fetchMotionSeries(hours);
  const ctx = document.getElementById('motionChart').getContext('2d');

  const dataset = {
    label: `Motion score (max per ${series.bucketSeconds}s)`,
    data: series.data,
    pointRadius: 0,
    borderWidth: 1,
    tension: 0.1
  };

  if (!motionChart) {
    motionChart = new Chart(ctx, {
      type: 'line',
      data: { labels: series.labels, datasets: [dataset] },
      options: {
        responsive: true,
        animation: false,
        interaction: { intersect: false, mode: 'index' },
        scales: {
          x: { ticks: { maxTicksLimit: 10 } },
          y: { beginAtZero: true }
        },
        plugins: {
          legend: { display: true },
          tooltip: {
            callbacks: {
              title: items => items[0]?.label ?? '',
              label: ctx => `score: ${ctx.parsed.y}`
            }
          }
        }
      }
    });
  } else {
    motionChart.data.labels = series.labels;
    motionChart.data.datasets[0] = dataset;
    motionChart.update();
  }
}

function currentRangeHours() {
  return parseFloat(document.getElementById('range-select').value || '24');
}

async function refresh() {
  try {
    await renderMotion(currentRangeHours());
  } catch (e) {
    console.error('plots refresh failed:', e);
  }
}

document.getElementById('btn-refresh').addEventListener('click', refresh);
document.getElementById('range-select').addEventListener('change', refresh);

// initial load + periodic refresh (every 60s)
refresh();
setInterval(refresh, 60_000);
