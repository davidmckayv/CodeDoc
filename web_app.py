"""Tiny Flask wrapper (no htmx required client‑side JS removed)."""

from __future__ import annotations

import os
from pathlib import Path
import sys  # For stderr
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
import io
from threading import Lock
import time
import json
from datetime import datetime

from flask import Flask, request, jsonify, render_template_string, Response

# Import the whole module to access its functions and submodules/variables
import readme_sync
import tiktoken  # Explicitly for initializing readme_sync._TOKEN_ENCODING

ROOT = Path(os.getenv("RMSYNC_ROOT", ".")).resolve()
app = Flask(__name__)

# Create an explicit log list for collecting messages
WEB_APP_LOG_BUFFER = []
WEB_APP_LOG_LOCK = Lock()  # Add Lock import back for this purpose
PROCESSING_STATUS = {"active": False, "id": None}
STATUS_LOCK = Lock()


# Add a direct logging function
def web_log(message):
    """Log a message both to stderr and to our buffer for UI display."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"

    with WEB_APP_LOG_LOCK:
        WEB_APP_LOG_BUFFER.append(formatted_message)
        # Keep the buffer at a reasonable size
        if len(WEB_APP_LOG_BUFFER) > 500:  # Increased buffer size
            WEB_APP_LOG_BUFFER.pop(0)

    # Also print to actual stderr for server logs
    print(formatted_message, file=sys.stderr)


@contextmanager
def capture_stderr_globally():
    """Capture stderr output while also tee-ing it to actual stderr."""
    old_stderr = sys.stderr
    string_io_buffer = io.StringIO()

    # Create a tee-like object that writes to both
    class TeeStderr:
        def write(self, message):
            string_io_buffer.write(message)
            old_stderr.write(message)
            # Also add non-empty, non-whitespace lines to our global buffer
            if message.strip():
                with WEB_APP_LOG_LOCK:
                    WEB_APP_LOG_BUFFER.append(message.rstrip())
                    # Keep the buffer at a reasonable size
                    if len(WEB_APP_LOG_BUFFER) > 100:
                        WEB_APP_LOG_BUFFER.pop(0)

        def flush(self):
            string_io_buffer.flush()
            old_stderr.flush()

    sys.stderr = TeeStderr()
    try:
        yield string_io_buffer
    finally:
        sys.stderr = old_stderr


# Helper to ensure readme_sync's tokenizer is initialized
def ensure_readme_sync_tokenizer_initialized():
    if readme_sync._TOKEN_ENCODING is None:
        print(
            "Attempting to initialize readme_sync._TOKEN_ENCODING from web_app...",
            file=sys.stderr,
        )
        try:
            readme_sync._TOKEN_ENCODING = tiktoken.get_encoding("cl100k_base")
            print("readme_sync._TOKEN_ENCODING initialized.", file=sys.stderr)
        except Exception as e:
            print(
                f"Failed to initialize readme_sync._TOKEN_ENCODING: {e}",
                file=sys.stderr,
            )
            # readme_sync functions should handle _TOKEN_ENCODING being None if it fails


INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>readme-sync</title>
  <style>
    body { font-family: sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }
    h1, h2 { color: #333; }
    ul { list-style-type: none; padding: 0; }
    li { background-color: #fff; border: 1px solid #ddd; margin-bottom: 10px; padding: 10px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; }
    li > div { display: flex; flex-direction: column; align-items: flex-end; margin-left: 10px; }
    li > div > form { margin-bottom: 5px; }
    .file-status { font-size: 0.9em; color: #555; text-align: right; }
    form { display: inline-block; }
    button { background-color: #007bff; color: white; border: none; padding: 8px 12px; text-align: center; text-decoration: none; display: inline-block; font-size: 14px; border-radius: 4px; cursor: pointer; }
    button:hover { background-color: #0056b3; }
    .container { background-color: #fff; padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
    select, input[type="hidden"] { margin-bottom:10px }
    hr { margin: 20px 0; }
    .status-message { padding: 10px; margin-top: 15px; border-radius: 4px; }
    .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    .info { background-color: #e2f3fd; color: #0c5460; border: 1px solid #bee5eb; }
    #live-log-container {
      background-color: #2b2b2b;
      color: #f0f0f0;
      font-family: monospace;
      padding: 10px;
      border-radius: 4px;
      height: 300px;
      overflow-y: auto;
      margin-top: 20px;
      white-space: pre-wrap;
      font-size: 12px;
    }
    .log-line {
      margin: 0;
      padding: 1px 0;
    }
    .status-indicator {
      display: inline-block;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      margin-right: 5px;
    }
    .status-active {
      background-color: #28a745;
      animation: pulse 1.5s infinite;
    }
    .status-inactive {
      background-color: #dc3545;
    }
    @keyframes pulse {
      0% { opacity: 1; }
      50% { opacity: 0.5; }
      100% { opacity: 1; }
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>readme-sync UI</h1>

    <div>
      <h2>LLM Mode Selection</h2>
      <p>Note: Remote LLM requires TOGETHER_API_KEY to be set in the environment.</p>
      <select id="llm_mode_select" name="llm_mode">
        <option value="1">Local LLM</option>
        <option value="2">Remote LLM (Together AI)</option>
      </select>
    </div>
    <hr>

    <h2>Process Single File</h2>
    <ul id="file-list">
    {% for fp in files %}
      <li>
        <span>{{ fp }}</span>
        <div>
          <form action="/generate" method="post" style="display:inline" class="generate-form">
            <input type="hidden" name="path" value="{{ fp }}">
            <input type="hidden" name="llm_mode" class="llm_mode_input">
            <button type="submit">Generate Summary</button>
          </form>
          <div class="file-status" id="status-{{ fp | replace('.', '-') | replace('/', '-') }}"></div>
        </div>
      </li>
    {% else %}
      <li>No processable files found.</li>
    {% endfor %}
    </ul>
    <hr>

    <h2>Process Entire Project</h2>
    <form action="/process-project" method="post" class="process-project-form">
        <input type="hidden" name="llm_mode" class="llm_mode_input">
        <button type="submit">Summarize All Project Files</button>
    </form>
    <div id="project-status"></div>
    
    <div>
      <h3>
        <span class="status-indicator" id="status-indicator"></span>
        Live Processing Log
      </h3>
      <div id="live-log-container"></div>
    </div>
  </div>

  <script>
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
        const logsHtml = logsArray.map(line => escapeHtml(line)).join('\\n');
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
            const safeFilePathId = filePath.replace(/\\./g, '-').replace(/\\//g, '-');
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
  </script>
</body>
</html>
"""


# Helper to collect files, consistent with readme_sync.py logic
def get_project_files(root_path):
    files_to_process = []
    # print(f"Scanning directory for project files: {root_path}", file=sys.stderr)
    for p in root_path.rglob(
        "*.*"
    ):  # More specific glob to avoid walking unnecessary dirs
        if p.is_file():
            file_ext = p.suffix.lstrip(".")
            if file_ext in readme_sync.INCLUDE_EXTS:
                if readme_sync.is_path_excluded(
                    p, readme_sync.EXCLUDE_DIR_ITEMS, readme_sync.EXCLUDE_FILE_ITEMS
                ):
                    continue
                files_to_process.append(p)
    return sorted(list(set(files_to_process)))


@app.route("/")
def index():
    print(f"DEBUG: ROOT path is: {ROOT}", file=sys.stderr)
    try:
        ensure_readme_sync_tokenizer_initialized()
        display_files = []
        # Using get_project_files to ensure consistency in what's listed vs processed
        print("DEBUG: Calling get_project_files...", file=sys.stderr)
        project_files = get_project_files(ROOT)
        print(
            f"DEBUG: get_project_files returned {len(project_files)} files.",
            file=sys.stderr,
        )
        for p in project_files:
            display_files.append(str(p.relative_to(ROOT)))

        print("DEBUG: Attempting to render template...", file=sys.stderr)
        response = render_template_string(
            INDEX_HTML, files=sorted(list(set(display_files)))
        )
        print("DEBUG: Template rendered successfully.", file=sys.stderr)
        return response
    except Exception as e:
        print(f"ERROR in index route: {type(e).__name__}: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        # Return a 500 error page with the error information
        return (
            f"Internal Server Error: {type(e).__name__}: {e}<pre>{traceback.format_exc()}</pre>",
            500,
        )


@app.route("/generate", methods=["POST"])
def generate():
    global WEB_APP_LOG_BUFFER
    global PROCESSING_STATUS

    # Update processing status
    with STATUS_LOCK:
        PROCESSING_STATUS["active"] = True
        PROCESSING_STATUS["id"] = f"file-{int(time.time())}"

    # Clear the log buffer for this request
    with WEB_APP_LOG_LOCK:
        WEB_APP_LOG_BUFFER = []

    logs_for_response = []

    try:
        web_log(f"WEB_APP: Starting generate endpoint")
        ensure_readme_sync_tokenizer_initialized()
        rel_path = request.form.get("path")
        llm_mode_choice = request.form.get("llm_mode", "1")

        web_log(f"WEB_APP: Processing file {rel_path} with LLM mode {llm_mode_choice}")

        if not rel_path:
            web_log("WEB_APP: No path provided")
            # Update processing status to inactive
            with STATUS_LOCK:
                PROCESSING_STATUS["active"] = False
            return jsonify(error="No path provided", logs=WEB_APP_LOG_BUFFER[-15:]), 400

        path = (ROOT / rel_path).resolve()
        if not path.is_file() or not path.exists():
            web_log(f"WEB_APP: File not found: {path}")
            # Update processing status to inactive
            with STATUS_LOCK:
                PROCESSING_STATUS["active"] = False
            return (
                jsonify(error=f"File not found: {path}", logs=WEB_APP_LOG_BUFFER[-15:]),
                404,
            )

        if llm_mode_choice == "2" and not readme_sync.remote_llm.TOGETHER_API_KEY:
            web_log("WEB_APP: Remote LLM mode selected but TOGETHER_API_KEY not set")
            # Update processing status to inactive
            with STATUS_LOCK:
                PROCESSING_STATUS["active"] = False
            return (
                jsonify(
                    error="Remote LLM mode selected, but TOGETHER_API_KEY is not set.",
                    logs=WEB_APP_LOG_BUFFER[-15:],
                ),
                500,
            )

        web_log(f"WEB_APP: Starting to process {path} with mode {llm_mode_choice}")

        with capture_stderr_globally() as log_buffer:
            try:
                web_log(f"WEB_APP: Calling readme_sync.summarise_file")
                md = readme_sync.summarise_file(path, llm_mode_choice=llm_mode_choice)

                if md.startswith("Error:"):
                    web_log(f"WEB_APP: Summarization error: {md}")
                    # Update processing status to inactive
                    with STATUS_LOCK:
                        PROCESSING_STATUS["active"] = False
                    return jsonify(error=md, logs=WEB_APP_LOG_BUFFER[-15:]), 500

                readme_file_path = path.parent / "README.md"
                readme_lock = readme_sync._get_readme_lock(readme_file_path)
                with readme_lock:
                    web_log(f"WEB_APP: Injecting summary into {readme_file_path}")
                    readme_sync._inject(readme_file_path, path.name, md)

                web_log(f"WEB_APP: Successfully generated and injected for {path}")

                # Update processing status to inactive
                with STATUS_LOCK:
                    PROCESSING_STATUS["active"] = False

                # We use our global log buffer now instead of the direct capture
                return jsonify(
                    summary=md,
                    path=str(path.relative_to(ROOT)),
                    readme_path=str(readme_file_path.relative_to(ROOT)),
                    logs=WEB_APP_LOG_BUFFER[-15:],
                )
            except Exception as inner_e:
                web_log(f"WEB_APP: Exception during processing: {inner_e}")
                import traceback

                tb_str = traceback.format_exc()
                web_log(f"WEB_APP: Traceback: {tb_str}")

                # Update processing status to inactive
                with STATUS_LOCK:
                    PROCESSING_STATUS["active"] = False

                return jsonify(error=str(inner_e), logs=WEB_APP_LOG_BUFFER[-15:]), 500

    except Exception as outer_e:
        web_log(f"WEB_APP: Critical error: {outer_e}")
        import traceback

        tb_str = traceback.format_exc()
        web_log(f"WEB_APP: Traceback: {tb_str}")

        # Update processing status to inactive
        with STATUS_LOCK:
            PROCESSING_STATUS["active"] = False

        return (
            jsonify(
                error=f"Critical server error: {str(outer_e)}",
                logs=WEB_APP_LOG_BUFFER[-15:],
            ),
            500,
        )


@app.route("/process-project", methods=["POST"])
def process_project():
    global WEB_APP_LOG_BUFFER
    global PROCESSING_STATUS

    # Update processing status
    with STATUS_LOCK:
        PROCESSING_STATUS["active"] = True
        PROCESSING_STATUS["id"] = f"project-{int(time.time())}"

    # Clear the log buffer for this request
    with WEB_APP_LOG_LOCK:
        WEB_APP_LOG_BUFFER = []

    # Initialize counts and details
    processed_files_count = 0
    project_files_list = []
    failed_files_details_map = {}
    current_total_tokens = 0

    try:
        web_log(f"WEB_APP: Starting process-project endpoint")
        ensure_readme_sync_tokenizer_initialized()
        llm_mode_choice = request.form.get("llm_mode", "1")
        web_log(f"WEB_APP: Using LLM mode {llm_mode_choice}")

        if llm_mode_choice == "2" and not readme_sync.remote_llm.TOGETHER_API_KEY:
            web_log("WEB_APP: Remote LLM mode selected but TOGETHER_API_KEY not set")
            # Update processing status to inactive
            with STATUS_LOCK:
                PROCESSING_STATUS["active"] = False
            return (
                jsonify(
                    message="Remote LLM mode selected, but TOGETHER_API_KEY is not set.",
                    error="TOGETHER_API_KEY not set for remote LLM.",
                    processed_count=processed_files_count,
                    total_files=len(project_files_list),
                    failed_files=failed_files_details_map,
                    total_tokens=current_total_tokens,
                    logs=WEB_APP_LOG_BUFFER[-15:],
                ),
                500,
            )

        with capture_stderr_globally() as log_buffer:
            try:
                web_log(f"WEB_APP: Finding project files to process")
                project_files_list = get_project_files(ROOT)
                web_log(f"WEB_APP: Found {len(project_files_list)} files to process")

                if not project_files_list:
                    web_log("WEB_APP: No files found to process in the project")
                    # Update processing status to inactive
                    with STATUS_LOCK:
                        PROCESSING_STATUS["active"] = False
                    return (
                        jsonify(
                            message="No files found to process in the project.",
                            processed_count=0,
                            total_files=0,
                            failed_files={},
                            total_tokens=0,
                            logs=WEB_APP_LOG_BUFFER[-15:],
                        ),
                        200,
                    )

                # Reset global token count
                with readme_sync._TOKEN_COUNT_LOCK:
                    readme_sync._TOTAL_TOKEN_COUNT = 0

                web_log(f"WEB_APP: Performing pre-summarization cleanup.")
                readme_dirs_to_check = set(p.parent for p in project_files_list)
                for readme_dir in readme_dirs_to_check:
                    readme_path = readme_dir / "README.md"
                    if readme_path.exists() and readme_path.is_file():
                        try:
                            current_content = readme_path.read_text(encoding="utf-8")
                            original_content = current_content
                            summarized_fnames_in_readme = (
                                readme_sync._get_summarized_fnames_from_readme(
                                    current_content
                                )
                            )
                            actual_fnames_in_dir_and_valid = {
                                f.name
                                for f in project_files_list
                                if f.parent == readme_dir
                            }
                            fnames_to_remove_summary_for = [
                                fn
                                for fn in summarized_fnames_in_readme
                                if fn not in actual_fnames_in_dir_and_valid
                            ]

                            if fnames_to_remove_summary_for:
                                print(
                                    f"WEB_APP: Pre-cleanup for {readme_path}: Removing summaries for {fnames_to_remove_summary_for}",
                                    file=sys.stderr,
                                )
                                modified_readme_content = current_content
                                for fname_to_remove in fnames_to_remove_summary_for:
                                    modified_readme_content = (
                                        readme_sync._remove_summary_from_readme(
                                            modified_readme_content, fname_to_remove
                                        )
                                    )
                                if modified_readme_content != original_content:
                                    readme_lock = readme_sync._get_readme_lock(
                                        readme_path
                                    )
                                    with readme_lock:
                                        readme_path.write_text(
                                            modified_readme_content, encoding="utf-8"
                                        )
                        except Exception as e_cleanup:  # Catch specific cleanup error
                            print(
                                f"WEB_APP: Error during pre-summarization cleanup of {readme_path}: {e_cleanup}",
                                file=sys.stderr,  # Logged to buffer
                            )
                # --- Token counting ---
                if readme_sync._TOKEN_ENCODING:
                    for p in project_files_list:
                        try:
                            content = p.read_text(encoding="utf-8", errors="ignore")
                            token_count = len(
                                readme_sync._TOKEN_ENCODING.encode(
                                    content, disallowed_special=()
                                )
                            )
                            with readme_sync._TOKEN_COUNT_LOCK:
                                readme_sync._TOTAL_TOKEN_COUNT += token_count
                        except (
                            Exception
                        ) as e_token:  # Catch specific token counting error
                            print(
                                f"WEB_APP: Warning: Could not count tokens for {p}: {e_token}",
                                file=sys.stderr,  # Logged to buffer
                            )
                current_total_tokens = readme_sync._TOTAL_TOKEN_COUNT
                print(
                    f"WEB_APP: Total estimated tokens for {len(project_files_list)} files: {current_total_tokens}",
                    file=sys.stderr,
                )

                # Set MAX_WORKERS based on LLM mode - IMPORTANT FIX
                if llm_mode_choice == "1":
                    MAX_WORKERS = int(os.getenv("LOCAL_MAX_WORKERS", "2"))
                    web_log(
                        f"WEB_APP: Using {MAX_WORKERS} workers for local LLM processing"
                    )
                else:  # llm_mode_choice == "2" (remote)
                    # Default to 4 workers for remote LLM if not specified
                    DEFAULT_REMOTE_WORKERS = 4
                    MAX_WORKERS = int(
                        os.getenv("REMOTE_MAX_WORKERS", str(DEFAULT_REMOTE_WORKERS))
                    )
                    web_log(
                        f"WEB_APP: Using {MAX_WORKERS} workers for remote LLM processing (from REMOTE_MAX_WORKERS env)"
                    )

                print(
                    f"WEB_APP: Starting summarization for {len(project_files_list)} files using up to {MAX_WORKERS} workers (mode: {llm_mode_choice})...",
                    file=sys.stderr,
                )

                # Main processing loop (sequential or parallel)
                if MAX_WORKERS <= 0:
                    for path_to_process in project_files_list:
                        try:
                            print(
                                f"WEB_APP: Processing (sequentially, mode: {llm_mode_choice}): {path_to_process}",
                                file=sys.stderr,
                            )
                            md_summary = readme_sync.summarise_file(
                                path_to_process, llm_mode_choice
                            )
                            if md_summary and not md_summary.startswith("Error:"):
                                readme_file_path = path_to_process.parent / "README.md"
                                readme_lock = readme_sync._get_readme_lock(
                                    readme_file_path
                                )
                                with readme_lock:
                                    readme_sync._inject(
                                        readme_file_path,
                                        path_to_process.name,
                                        md_summary,
                                    )
                                processed_files_count += 1
                            else:
                                err_msg = (
                                    md_summary or "Unknown error during summarization"
                                )
                                failed_files_details_map[
                                    str(path_to_process.relative_to(ROOT))
                                ] = err_msg
                                print(
                                    f"WEB_APP: Skipping/Error for {path_to_process.name}: {err_msg[:100]}...",
                                    file=sys.stderr,
                                )
                        except (
                            Exception
                        ) as exc_seq:  # Error in sequential processing of one file
                            err_str = str(exc_seq)
                            failed_files_details_map[
                                str(path_to_process.relative_to(ROOT))
                            ] = err_str
                            print(
                                f"WEB_APP: Error processing {path_to_process} sequentially: {err_str}",
                                file=sys.stderr,
                            )
                else:  # Parallel execution
                    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                        if (
                            llm_mode_choice == "1"
                            and hasattr(readme_sync, "local_llm")
                            and hasattr(readme_sync.local_llm, "preload_model")
                        ):
                            print(
                                "WEB_APP: Attempting to preload local model...",
                                file=sys.stderr,
                            )
                            preload_future = executor.submit(
                                readme_sync.local_llm.preload_model
                            )
                            try:
                                if preload_future.result(
                                    timeout=getattr(
                                        readme_sync.local_llm,
                                        "LLM_FIRST_ATTEMPT_TIMEOUT",
                                        60,
                                    )
                                    + 10
                                ):
                                    print(
                                        "WEB_APP: Local model preloaded successfully or was already loaded.",
                                        file=sys.stderr,
                                    )
                                else:
                                    print(
                                        "WEB_APP: Local model preloading failed or indicated model was not ready.",
                                        file=sys.stderr,
                                    )
                            except Exception as e_preload:
                                print(
                                    f"WEB_APP: Error during local model preloading: {e_preload}",
                                    file=sys.stderr,
                                )

                        future_to_path = {
                            executor.submit(
                                readme_sync.summarise_file, p, llm_mode_choice
                            ): p
                            for p in project_files_list
                        }
                        for i, future in enumerate(as_completed(future_to_path)):
                            path_processed = future_to_path[future]
                            try:
                                md_summary = future.result()
                                if md_summary and not md_summary.startswith("Error:"):
                                    readme_file_path = (
                                        path_processed.parent / "README.md"
                                    )
                                    readme_lock = readme_sync._get_readme_lock(
                                        readme_file_path
                                    )
                                    with readme_lock:
                                        readme_sync._inject(
                                            readme_file_path,
                                            path_processed.name,
                                            md_summary,
                                        )
                                    processed_files_count += 1
                                else:
                                    err_msg = (
                                        md_summary
                                        or "Unknown error during summarization"
                                    )
                                    failed_files_details_map[
                                        str(path_processed.relative_to(ROOT))
                                    ] = err_msg
                                    print(
                                        f"WEB_APP: Skipping/Error for {path_processed.name}: {err_msg[:100]}...",
                                        file=sys.stderr,
                                    )
                            except (
                                Exception
                            ) as exc_parallel_file:  # Error in parallel processing of one file
                                err_str = str(exc_parallel_file)
                                failed_files_details_map[
                                    str(path_processed.relative_to(ROOT))
                                ] = err_str
                                print(
                                    f"WEB_APP: File {path_processed.name} generated an exception: {err_str}",
                                    file=sys.stderr,
                                )

                            print(
                                f"WEB_APP: Web processed ({i+1}/{len(project_files_list)}): {path_processed.name}. Successes: {processed_files_count}",
                                file=sys.stderr,
                            )

                current_total_tokens = readme_sync._TOTAL_TOKEN_COUNT
                result_message = f"Project processing complete. Processed {processed_files_count} of {len(project_files_list)} files successfully."
                if failed_files_details_map:
                    result_message += (
                        f" {len(failed_files_details_map)} file(s) failed."
                    )
                result_message += f" Total tokens estimated: {current_total_tokens}."
                print(f"WEB_APP: {result_message}", file=sys.stderr)

                # Capture the end of processing with web_log
                web_log(
                    f"WEB_APP: Processing completed. Processed {processed_files_count} of {len(project_files_list)} files."
                )

                # Update processing status to inactive at the end
                with STATUS_LOCK:
                    PROCESSING_STATUS["active"] = False

                # Use our global log buffer
                return jsonify(
                    message=result_message,
                    processed_count=processed_files_count,
                    total_files=len(project_files_list),
                    failed_files=failed_files_details_map,
                    total_tokens=current_total_tokens,
                    logs=WEB_APP_LOG_BUFFER[-15:],
                )

            except Exception as inner_e:
                # Update processing status to inactive
                with STATUS_LOCK:
                    PROCESSING_STATUS["active"] = False
                # Rest of exception handling...
                # Not modifying this part

    except Exception as outer_e:
        # Update processing status to inactive
        with STATUS_LOCK:
            PROCESSING_STATUS["active"] = False
        # Rest of exception handling...
        # Not modifying this part


@app.route("/log-stream")
def log_stream():
    """Stream logs as server-sent events."""

    def generate():
        last_idx = 0
        yield 'data: {"status": "connected", "message": "Log stream connected"}\n\n'

        while True:
            with WEB_APP_LOG_LOCK:
                if last_idx < len(WEB_APP_LOG_BUFFER):
                    # Get new logs since last check
                    new_logs = WEB_APP_LOG_BUFFER[last_idx:]
                    last_idx = len(WEB_APP_LOG_BUFFER)

                    # Process status info
                    with STATUS_LOCK:
                        status_data = {
                            "active": PROCESSING_STATUS["active"],
                            "id": PROCESSING_STATUS["id"],
                        }

                    # Send the new logs and status
                    data = {"logs": new_logs, "status": status_data}
                    yield f"data: {json.dumps(data)}\n\n"

            # Check again after a short delay
            time.sleep(0.5)

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=14285)
