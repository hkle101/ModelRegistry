// Helper functions for artifact-related UI rendering
function renderArtifactsTable(container, artifacts) {
	if(!Array.isArray(artifacts) || artifacts.length === 0) {
		container.innerHTML = '<div class="muted">No artifacts found.</div>';
		return;
	}
	const headers = ['ID','Name','Type'];
	const rows = artifacts.map(a => `<tr><td>${a.id || a.artifact_id || ''}</td><td>${a.name || ''}</td><td>${a.type || a.artifact_type || ''}</td></tr>`).join('');
	container.innerHTML = `<table><thead><tr>${headers.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table>`;
}

window.renderArtifactsTable = renderArtifactsTable;
