document.getElementById('btn-snapshot').addEventListener('click', () => {
	const a = document.createElement('a');
	a.href = '/snapshot';
	a.download = 'snapshot.jpg';
	document.body.appendChild(a);
	a.click();
	a.remove();
});

document.getElementById('btn-save-latest').addEventListener('click', async () => {
  try {
    const r = await fetch('/snapshots/save_latest', { method: 'POST' });
    const j = await r.json();
    alert(j.ok ? ('Saved: ' + j.filename) : ('Failed: ' + j.msg));
  } catch(e) { alert('Error: ' + e); }
});

async function pollStatus() {
  	try {
    	const r = await fetch('/status');
    	const j = await r.json();
    	document.getElementById('status').textContent =
      	`motion: ${j.motion_score} / ${j.threshold}`;
  	} catch (e) {
    	// ignore
  	} finally {
    	setTimeout(pollStatus, 1000);
  	}
}
pollStatus();
