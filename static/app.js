const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileList = document.getElementById('file-list');
const qrContainer = document.getElementById('qr-container');
const deviceNameInput = document.getElementById('device-name');

let showHistory = false;

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
  formData.append('sender', getDeviceName());

  await fetch('/files', { method: 'POST', body: formData });
}

async function loadFiles() {
  const res = await fetch('/files');
  const data = await res.json();
  fileList.innerHTML = data.files.map(item => `
    <li>
      <div class="file-info">
        <span class="file-name">${escapeHtml(item.filename)}</span>
        <span class="file-meta">From <strong>${escapeHtml(item.sender)}</strong> • ${item.timestamp}</span>
      </div>
      <div class="actions">
        <a href="/files/${encodeURIComponent(item.filename)}" download>Download</a>
        <button class="delete-btn" onclick="deleteFile('${item.filename.replace(/'/g, "\\'")}')">Delete</button>
      </div>
    </li>
  `).join('');
}

async function deleteFile(filename) {
  if (!confirm(`Delete ${filename}?`)) return;

  const res = await fetch(`/files/${encodeURIComponent(filename)}`, { method: 'DELETE' });
  if (!res.ok) {
    alert('Failed to delete file.');
  }
}

async function loadText() {
  const res = await fetch('/text');
  const data = await res.json();
  
  const latestContainer = document.getElementById('latest-snippet');
  const historyContainer = document.getElementById('text-history');
  const toggleBtn = document.getElementById('toggle-history-btn');
  const clearAllBtn = document.getElementById('clear-all-text-btn');

  if (!data.history || data.history.length === 0) {
    latestContainer.innerHTML = '<p style="color: #888; font-size: 13px; margin-top: 10px;">No shared text yet.</p>';
    historyContainer.innerHTML = '';
    toggleBtn.style.display = 'none';
    clearAllBtn.style.display = 'none';
    return;
  }

  clearAllBtn.style.display = 'inline-block';

  const latest = data.history[0];
  const latestSender = latest.sender || 'Unknown Device';
  latestContainer.innerHTML = `
    <div class="text-card primary-card">
      <div class="text-card-header">
        <span><strong>${escapeHtml(latestSender)}</strong> • ${latest.timestamp}</span>
      </div>
      <div class="text-card-body">${escapeHtml(latest.text)}</div>
      <div class="text-card-actions">
        <button class="btn secondary" onclick="copySnippet(this)">📋 Copy</button>
        <button class="delete-btn" onclick="deleteSnippet('${latest.id}')">Delete</button>
      </div>
    </div>
  `;

  const olderEntries = data.history.slice(1);
  if (olderEntries.length > 0) {
    toggleBtn.style.display = 'inline-block';
    toggleBtn.textContent = showHistory 
      ? `📜 Hide History` 
      : `📜 View History (${olderEntries.length})`;

    historyContainer.style.display = showHistory ? 'flex' : 'none';
    historyContainer.innerHTML = olderEntries.map(item => {
      const sender = item.sender || 'Unknown Device';
      return `
        <div class="text-card">
          <div class="text-card-header">
            <span><strong>${escapeHtml(sender)}</strong> • ${item.timestamp}</span>
          </div>
          <div class="text-card-body">${escapeHtml(item.text)}</div>
          <div class="text-card-actions">
            <button class="btn secondary" onclick="copySnippet(this)">📋 Copy</button>
            <button class="delete-btn" onclick="deleteSnippet('${item.id}')">Delete</button>
          </div>
        </div>
      `;
    }).join('');
  } else {
    toggleBtn.style.display = 'none';
    historyContainer.style.display = 'none';
    historyContainer.innerHTML = '';
  }
}

function toggleHistory() {
  showHistory = !showHistory;
  loadText();
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function getDeviceName() {
  let name = localStorage.getItem('device_nickname');
  if (name) return name;

  const ua = navigator.userAgent;
  if (/iPhone|iPad|iPod/.test(ua)) name = "iPhone";
  else if (/Android/.test(ua)) name = "Android";
  else if (/Macintosh/.test(ua)) name = "Mac";
  else if (/Windows/.test(ua)) name = "Windows PC";
  else name = "Desktop";

  return name;
}

function initDeviceName() {
  deviceNameInput.value = getDeviceName();
}

function saveDeviceName() {
  const newName = deviceNameInput.value.trim();
  if (newName) {
    localStorage.setItem('device_nickname', newName);
  } else {
    localStorage.removeItem('device_nickname');
    initDeviceName();
  }
}

async function saveText() {
  const textarea = document.getElementById('shared-text');
  if (!textarea.value.trim()) return;

  const res = await fetch('/text', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      text: textarea.value,
      sender: getDeviceName()
    })
  });

  if (res.ok) {
    textarea.value = '';
    loadText();
  }
}

async function deleteSnippet(id) {
  const res = await fetch(`/text/${id}`, { method: 'DELETE' });
  if (res.ok) {
    loadText();
  }
}

async function clearAllSnippets() {
  if (!confirm("Clear all shared text entries?")) return;

  const res = await fetch('/text', { method: 'DELETE' });
  if (res.ok) {
    loadText();
  }
}

function copySnippet(btnElement) {
  const card = btnElement.closest('.text-card');
  if (!card) return;

  const text = card.querySelector('.text-card-body').innerText;
  if (!text) return;

  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(() => {
      alert('Copied to clipboard!');
    }).catch(() => {
      fallbackCopy(text);
    });
  } else {
    fallbackCopy(text);
  }
}

function fallbackCopy(text) {
  const textArea = document.createElement('textarea');
  textArea.value = text;
  textArea.style.position = 'fixed';
  textArea.style.left = '-9999px';
  textArea.style.top = '0';
  document.body.appendChild(textArea);
  
  textArea.focus();
  textArea.select();
  textArea.setSelectionRange(0, 99999);

  try {
    const successful = document.execCommand('copy');
    if (successful) {
      alert('Copied to clipboard!');
    } else {
      window.prompt('Copy text manually:', text);
    }
  } catch (err) {
    window.prompt('Copy text manually:', text);
  } finally {
    document.body.removeChild(textArea);
  }
}

const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsUrl = `${protocol}//${window.location.host}/ws`;
let ws;

function connectWebSocket() {
  ws = new WebSocket(wsUrl);

  ws.onmessage = (event) => {
    const msg = event.data;
    if (msg === 'file_uploaded' || msg === 'file_deleted' || msg === 'refresh') {
      loadFiles();
    } else if (msg === 'text_added' || msg === 'text_deleted' || msg === 'text_updated') {
      loadText();
    }
  };

  ws.onclose = () => {
    setTimeout(connectWebSocket, 2000);
  };
}

loadFiles();
loadText();
connectWebSocket();
initDeviceName();