function escapeHtml(unsafe) {
  return unsafe
       .replace(/&/g, "&amp;")
       .replace(/</g, "&lt;")
       .replace(/>/g, "&gt;")
       .replace(/"/g, "&quot;")
       .replace(/'/g, "&#039;");
}

function displayLogs(logsArray, targetElement) {
  if (logsArray && Array.isArray(logsArray) && logsArray.length > 0) {
    const logsHtml = logsArray.map(line => escapeHtml(line)).join('\n');
    const logSection = '<h4>Log Messages:</h4>' + 
      '<pre style="max-height: 200px; overflow-y: auto; background-color: #e9e9e9; padding: 5px; ' +
      'border: 1px solid #ccc; text-align: left; white-space: pre-wrap; font-size: 12px;">' + 
      logsHtml + '</pre>';
    
    if (targetElement.innerHTML.includes('successfully')) {
      targetElement.innerHTML += logSection;
    } else {
      targetElement.innerHTML = targetElement.innerHTML + logSection;
    }
    
    console.log("Displayed logs:", logsArray.length, "lines");
    return true;
  } else {
    console.warn("No logs to display or invalid logs format", logsArray);
    return false;
  }
}

function attachLlmMode(event) {
  const selectedLlmMode = document.getElementById('llm_mode_select').value;
  const form = event.target;
  const llmModeInputs = form.querySelectorAll('.llm_mode_input');
  llmModeInputs.forEach(input => {
    input.value = selectedLlmMode;
  });
}

let eventSource;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
const reconnectDelay = 2000; // 2 seconds

function setupLogStream() {
  if (eventSource) {
    eventSource.close();
  }

  eventSource = new EventSource('/log-stream');
  const logContainer = document.getElementById('live-log-container');
  const statusIndicator = document.getElementById('status-indicator');
  
  eventSource.onopen = function() {
    console.log('Log stream connected');
    reconnectAttempts = 0;
    logContainer.innerHTML += '<div class="log-line">[System] Connected to log stream</div>';
    logContainer.scrollTop = logContainer.scrollHeight;
  };
  
  eventSource.onmessage = function(event) {
    try {
      const data = JSON.parse(event.data);
      
      if (data.logs && Array.isArray(data.logs)) {
        data.logs.forEach(logLine => {
          logContainer.innerHTML += `<div class="log-line">${escapeHtml(logLine)}</div>`;
        });
        logContainer.scrollTop = logContainer.scrollHeight;
      }
      
      if (data.status) {
        if (data.status.active) {
          statusIndicator.className = "status-indicator status-active";
        } else {
          statusIndicator.className = "status-indicator status-inactive";
        }
      }
      
    } catch (e) {
      console.error('Error parsing log stream data:', e);
      logContainer.innerHTML += `<div class="log-line error">[System] Error processing log: ${e.message}</div>`;
    }
  };
  
  eventSource.onerror = function(error) {
    console.error('Log stream error:', error);
    statusIndicator.className = "status-indicator status-inactive";
    logContainer.innerHTML += '<div class="log-line error">[System] Connection error. Attempting to reconnect...</div>';
    
    eventSource.close();
    
    if (reconnectAttempts < maxReconnectAttempts) {
      reconnectAttempts++;
      setTimeout(setupLogStream, reconnectDelay * reconnectAttempts);
      logContainer.innerHTML += `<div class="log-line">[System] Reconnect attempt ${reconnectAttempts}/${maxReconnectAttempts}...</div>`;
    } else {
      logContainer.innerHTML += '<div class="log-line error">[System] Failed to reconnect after multiple attempts. Please reload the page.</div>';
    }
  };
}

document.addEventListener('DOMContentLoaded', setupLogStream);

document.addEventListener('DOMContentLoaded', function() {
  // Initialize all llm_mode_input fields with the current dropdown value
  const selectedLlmMode = document.getElementById('llm_mode_select').value;
  document.querySelectorAll('.llm_mode_input').forEach(input => {
    input.value = selectedLlmMode;
  });

  const projectForm = document.querySelector('.process-project-form');
  if (projectForm) {
      projectForm.addEventListener('submit', async function(event) {
          event.preventDefault();
          attachLlmMode(event);

          const formData = new FormData(projectForm);
          const statusDiv = document.getElementById('project-status');
          statusDiv.className = 'status-message';
          statusDiv.innerHTML = 'Processing project... please wait.';
          statusDiv.classList.add('info');

          try {
              const response = await fetch('/process-project', {
                  method: 'POST',
                  body: formData
              });
              
              let result = {};
              try {
                  result = await response.json();
                  console.log("Received JSON response:", result);
              } catch (parseError) {
                  const textContent = await response.text();
                  console.error("Failed to parse JSON response:", parseError);
                  console.log("Raw response text:", textContent.substring(0, 500) + "...");
                  result = { 
                      error: "Failed to parse server response: " + parseError.message,
                      message: "Server returned non-JSON response",
                      logs: ["Error parsing server response. Raw content (truncated):", textContent.substring(0, 300) + "..."]
                  };
              }
              
              if (response.ok) {
                  statusDiv.innerHTML = result.message || 'Project processing completed.';
                  statusDiv.classList.remove('info', 'error');
                  statusDiv.classList.add('success');
                  
                  displayLogs(result.logs, statusDiv);
              } else {
                  statusDiv.innerHTML = 'Error: ' + (result.error || result.message || 'Unknown error');
                  statusDiv.classList.remove('info', 'success');
                  statusDiv.classList.add('error');
                  
                  displayLogs(result.logs, statusDiv);
              }
          } catch (error) {
              console.error("Network or fetch error:", error);
              statusDiv.innerHTML = 'Network error or server unavailable: ' + error.toString();
              statusDiv.classList.remove('info', 'success');
              statusDiv.classList.add('error');
          }
      });
  }
  
  document.querySelectorAll('.generate-form').forEach(form => {
      form.addEventListener('submit', async function(event) {
          event.preventDefault();
          attachLlmMode(event);

          const formData = new FormData(form);
          const filePath = formData.get('path');
          const safeFilePathId = filePath.replace(/\./g, '-').replace(/\//g, '-');
          const statusDiv = document.getElementById(`status-${safeFilePathId}`);
          
          if (!statusDiv) {
              console.error('Could not find status div for', filePath);
              return;
          }

          statusDiv.className = 'file-status status-message';
          statusDiv.innerHTML = `Processing ${escapeHtml(filePath)}...`;
          statusDiv.classList.add('info');

          try {
              const response = await fetch('/generate', {
                  method: 'POST',
                  body: formData
              });
              
              let result = {};
              try {
                  result = await response.json();
                  console.log("Received JSON response for file:", filePath, result);
              } catch (parseError) {
                  const textContent = await response.text();
                  console.error("Failed to parse JSON for file:", filePath, parseError);
                  console.log("Raw response text:", textContent.substring(0, 500) + "...");
                  result = { 
                      error: "Failed to parse server response: " + parseError.message,
                      logs: ["Error parsing server response. Raw content (truncated):", textContent.substring(0, 300) + "..."]
                  };
              }

              if (response.ok) {
                  statusDiv.innerHTML = `Successfully processed ${escapeHtml(filePath)}.<br>Readme: ${escapeHtml(result.readme_path || 'unknown')}`;
                  statusDiv.classList.remove('info', 'error');
                  statusDiv.classList.add('success');
                  
                  displayLogs(result.logs, statusDiv);
              } else {
                  statusDiv.innerHTML = `Error processing ${escapeHtml(filePath)}: ${escapeHtml(result.error || 'Unknown error')}`;
                  statusDiv.classList.remove('info', 'success');
                  statusDiv.classList.add('error');
                  
                  displayLogs(result.logs, statusDiv);
              }
          } catch (error) {
              console.error("Network or fetch error for file:", filePath, error);
              statusDiv.innerHTML = `Network error for ${escapeHtml(filePath)}: ${escapeHtml(error.toString())}`;
              statusDiv.classList.remove('info', 'success');
              statusDiv.classList.add('error');
          }
      });
  });
}); 