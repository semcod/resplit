"""Shared HTML/CSS/JS snippets used by the day and timeline reporters."""
from __future__ import annotations

JS_HELPERS = """
<script>
function copyToClipboard(format) {
    const data = document.getElementById('data-' + format).textContent;
    navigator.clipboard.writeText(data).then(() => {
        alert('Copied ' + format.toUpperCase() + ' to clipboard!');
    });
}
function downloadFile(format, filename) {
    const data = document.getElementById('data-' + format).textContent;
    const blob = new Blob([data], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename; a.click();
    window.URL.revokeObjectURL(url);
}
</script>
"""

CSS_VARS = """
  :root {
    --bg: #0f172a; --card-bg: rgba(30,41,59,0.7); --border: rgba(255,255,255,0.1);
    --text: #f8fafc; --text-dim: #94a3b8; --primary: #6366f1;
    --success: #10b981; --fail: #ef4444; --warn: #f59e0b;
  }
"""
