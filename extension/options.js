// Saves options to chrome.storage
const saveOptions = () => {
    const name      = document.getElementById('name').value;
    const server    = document.getElementById('server').value;
    const warning   = document.getElementById('warning').value;
  
    chrome.storage.sync.set(
      { name: name, server: server, warning:warning },
      () => {
        // Update status to let user know options were saved.
        const status        = document.getElementById('status');
        status.textContent  = 'Options saved.';

        setTimeout(() => {
          status.textContent = '';
        }, 5000);
      }
    );
};
  
  // Restores select box and checkbox state using the preferences
  // stored in chrome.storage.
  const restoreOptions = () => {
    chrome.storage.sync.get(
      { name: '', server: 'http://127.0.0.1:5000', warning: 5 },
      (items) => {
        document.getElementById('name').value       = items.name;
        document.getElementById('server').value     = items.server;
        document.getElementById('warning').value    = items.warning;
      }
    );
  };
  
  document.addEventListener('DOMContentLoaded', restoreOptions);
  document.getElementById('save').addEventListener('click', saveOptions);