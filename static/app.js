const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileList = document.getElementById('file-list');
const qrContainer = document.getElementById('qr-container');
const sharedTextarea = document.getElementById('shared-text');

function toggleQR() {
  const isHidden = qrContainer.style.display === 'none' || qrContainer.style.display === '';
  qrContainer.style.display = isHidden ? 'block' : 'none';
}

dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', () => uploadFile(fileInput.files[0]));

dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('hover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('hover'));
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('hover');
  if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
});

async function uploadFile(file) {
  if (!file) return;
  const formData = new FormData();
  formData.append('file', file);

  await fetch('/files', { method: 'POST', body: formData });
}

async function deleteFile(filename) {
  if (!confirm(`Delete ${filename}?`)) return;

  const res = await fetch(`/files/${encodeURIComponent(filename)}`, { method: 'DELETE' });
  if (!res.ok) {
    alert('Failed to delete file.');
  }
}

async function loadFiles() {
  const res = await fetch('/files');
  const data = await res.json();
  fileList.innerHTML = data.files.map(name => `
    <li>
      <span>${name}</span>
      <div class="actions">
        <a href="/files/${encodeURIComponent(name)}" download>Download</a>
        <button class="delete-btn" onclick="deleteFile('${name.replace(/'/g, "\\'")}')">Delete</button>
      </div>
    </li>
  `).join('');
}

async function loadText() {
  const res = await fetch('/text');
  const data = await res.json();
  sharedTextarea.value = data.text;
}

async function saveText() {
  await fetch('/text', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: sharedTextarea.value })
  });
}

async function copyText() {
  if (!sharedTextarea.value) return;

  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(sharedTextarea.value);
      alert('Copied to clipboard!');
      return;
    } catch (err) {
      console.warn('Clipboard API failed, running fallback...', err);
    }
  }

  sharedTextarea.select();
  sharedTextarea.setSelectionRange(0, 99999);
  try {
    const successful = document.execCommand('copy');
    if (successful) {
      alert('Copied to clipboard!');
    } else {
      alert('Failed to copy automatically. Text is selected for manual copy.');
    }
  } catch (err) {
    alert('Copy command not supported on this browser.');
  }
}

// WebSocket Connection Management
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsUrl = `${protocol}//${window.location.host}/ws`;
let ws;

function connectWebSocket() {
  ws = new WebSocket(wsUrl);

  ws.onmessage = (event) => {
    const msg = event.data;
    if (msg === 'file_uploaded' || msg === 'file_deleted' || msg === 'refresh') {
      loadFiles();
    } else if (msg === 'text_updated') {
      loadText();
    }
  };

  ws.onclose = () => {
    setTimeout(connectWebSocket, 2000);
  };
}

// Initializations
loadFiles();
loadText();
connectWebSocket();