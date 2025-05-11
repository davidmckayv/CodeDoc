"""Tiny Flask wrapper (no htmx required client‑side JS removed)."""

from __future__ import annotations

import os
from pathlib import Path
import sys  # For stderr
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from flask import Flask, request, jsonify, render_template_string

# Import the whole module to access its functions and submodules/variables
import readme_sync
import tiktoken  # Explicitly for initializing readme_sync._TOKEN_ENCODING

ROOT = Path(os.getenv("RMSYNC_ROOT", ".")).resolve()
app = Flask(__name__)


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
    form { display: inline-block; margin-left: 10px; }
    button { background-color: #007bff; color: white; border: none; padding: 8px 12px; text-align: center; text-decoration: none; display: inline-block; font-size: 14px; border-radius: 4px; cursor: pointer; }
    button:hover { background-color: #0056b3; }
    .container { background-color: #fff; padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
    select, input[type="hidden"] { margin-bottom:10px }
    hr { margin: 20px 0; }
    .status-message { padding: 10px; margin-top: 15px; border-radius: 4px; }
    .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
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
        <form action="/generate" method="post" style="display:inline" onsubmit="attachLlmMode(event)">
          <input type="hidden" name="path" value="{{ fp }}">
          <input type="hidden" name="llm_mode" class="llm_mode_input">
          <button type="submit">Generate Summary</button>
        </form>
      </li>
    {% else %}
      <li>No processable files found.</li>
    {% endfor %}
    </ul>
    <hr>

    <h2>Process Entire Project</h2>
    <form action="/process-project" method="post" onsubmit="attachLlmMode(event)">
        <input type="hidden" name="llm_mode" class="llm_mode_input">
        <button type="submit">Summarize All Project Files</button>
    </form>
    <div id="project-status"></div>
  </div>

  <script>
    function attachLlmMode(event) {
      const selectedLlmMode = document.getElementById('llm_mode_select').value;
      // For forms submitted via button click, event.target is the form itself.
      const form = event.target;
      const llmModeInputs = form.querySelectorAll('.llm_mode_input');
      llmModeInputs.forEach(input => {
        input.value = selectedLlmMode;
      });
    }

    // Optional: Handle form submissions with Fetch API for better UX
    // This is a more advanced addition if you want to avoid page reloads
    // Example for process-project:
    const projectForm = document.querySelector('form[action="/process-project"]');
    if (projectForm) {
        projectForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            attachLlmMode(event); // Ensure LLM mode is attached

            const formData = new FormData(projectForm);
            const statusDiv = document.getElementById('project-status');
            statusDiv.className = 'status-message'; // Reset class
            statusDiv.textContent = 'Processing project... please wait.';
            statusDiv.classList.add('info');


            try {
                const response = await fetch('/process-project', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                if (response.ok) {
                    statusDiv.textContent = result.message || 'Project processing completed.';
                    statusDiv.classList.remove('info', 'error');
                    statusDiv.classList.add('success');
                } else {
                    statusDiv.textContent = 'Error: ' + (result.error || result.message || 'Unknown error');
                    statusDiv.classList.remove('info', 'success');
                    statusDiv.classList.add('error');
                }
            } catch (error) {
                statusDiv.textContent = 'Network error or server unavailable: ' + error.toString();
                statusDiv.classList.remove('info', 'success');
                statusDiv.classList.add('error');
            }
        });
    }
    // Similar logic could be applied to individual file generation forms
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
    ensure_readme_sync_tokenizer_initialized()
    rel_path = request.form.get("path")
    llm_mode_choice = request.form.get("llm_mode", "1")

    if not rel_path:
        return jsonify(error="No path provided"), 400

    path = (ROOT / rel_path).resolve()
    if not path.is_file() or not path.exists():
        return jsonify(error=f"File not found: {path}"), 404

    if llm_mode_choice == "2" and not readme_sync.remote_llm.TOGETHER_API_KEY:
        return (
            jsonify(error="Remote LLM mode selected, but TOGETHER_API_KEY is not set."),
            500,
        )

    print(
        f"Generating summary for {path} using LLM mode {llm_mode_choice}",
        file=sys.stderr,
    )
    md = readme_sync.summarise_file(path, llm_mode_choice=llm_mode_choice)

    if md.startswith("Error:"):
        return jsonify(error=md), 500

    readme_file_path = path.parent / "README.md"
    readme_lock = readme_sync._get_readme_lock(readme_file_path)
    with readme_lock:
        readme_sync._inject(readme_file_path, path.name, md)

    print(
        f"Successfully generated summary for {path} and injected into {readme_file_path}",
        file=sys.stderr,
    )
    return jsonify(
        summary=md,
        path=str(path.relative_to(ROOT)),
        readme_path=str(readme_file_path.relative_to(ROOT)),
    )


@app.route("/process-project", methods=["POST"])
def process_project():
    ensure_readme_sync_tokenizer_initialized()
    llm_mode_choice = request.form.get("llm_mode", "1")

    if llm_mode_choice == "2" and not readme_sync.remote_llm.TOGETHER_API_KEY:
        return (
            jsonify(error="Remote LLM mode selected, but TOGETHER_API_KEY is not set."),
            500,
        )

    all_project_files = get_project_files(ROOT)

    if not all_project_files:
        return (
            jsonify(
                message="No files found to process in the project.",
                processed_count=0,
                total_files=0,
                failed_files=[],
                total_tokens=0,
            ),
            200,
        )

    # Reset global token count in readme_sync for this run
    with readme_sync._TOKEN_COUNT_LOCK:
        readme_sync._TOTAL_TOKEN_COUNT = 0

    # --- Pre-summarization cleanup ---
    readme_dirs_to_check = set(p.parent for p in all_project_files)
    print(
        f"Starting pre-summarization cleanup for READMEs in {len(readme_dirs_to_check)} directories.",
        file=sys.stderr,
    )
    for readme_dir in readme_dirs_to_check:
        readme_path = readme_dir / "README.md"
        if readme_path.exists() and readme_path.is_file():
            try:
                current_content = readme_path.read_text(encoding="utf-8")
                original_content = current_content
                summarized_fnames_in_readme = (
                    readme_sync._get_summarized_fnames_from_readme(current_content)
                )
                actual_fnames_in_dir_and_valid = {
                    f.name for f in all_project_files if f.parent == readme_dir
                }
                fnames_to_remove_summary_for = [
                    fn
                    for fn in summarized_fnames_in_readme
                    if fn not in actual_fnames_in_dir_and_valid
                ]

                if fnames_to_remove_summary_for:
                    modified_readme_content = current_content
                    for fname_to_remove in fnames_to_remove_summary_for:
                        modified_readme_content = (
                            readme_sync._remove_summary_from_readme(
                                modified_readme_content, fname_to_remove
                            )
                        )
                    if modified_readme_content != original_content:
                        readme_lock = readme_sync._get_readme_lock(readme_path)
                        with readme_lock:
                            readme_path.write_text(
                                modified_readme_content, encoding="utf-8"
                            )
            except Exception as e:
                print(
                    f"Error during pre-summarization cleanup of {readme_path}: {e}",
                    file=sys.stderr,
                )

    # --- Token counting for all eligible files before processing ---
    if readme_sync._TOKEN_ENCODING:
        for p in all_project_files:
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                token_count = len(
                    readme_sync._TOKEN_ENCODING.encode(content, disallowed_special=())
                )
                with readme_sync._TOKEN_COUNT_LOCK:
                    readme_sync._TOTAL_TOKEN_COUNT += token_count
            except Exception as e:
                print(
                    f"Warning: Could not count tokens for {p} in web_app process_project: {e}",
                    file=sys.stderr,
                )
    initial_total_tokens = readme_sync._TOTAL_TOKEN_COUNT
    print(
        f"Total estimated tokens for {len(all_project_files)} files: {initial_total_tokens}",
        file=sys.stderr,
    )

    # --- Setup MAX_WORKERS ---
    if llm_mode_choice == "1":
        MAX_WORKERS = int(os.getenv("LOCAL_MAX_WORKERS", "2"))
    elif llm_mode_choice == "2":
        MAX_WORKERS = int(os.getenv("REMOTE_MAX_WORKERS", "4"))
    else:  # Should not happen
        MAX_WORKERS = 1

    print(
        f"Starting summarization for {len(all_project_files)} files using up to {MAX_WORKERS} workers (mode: {llm_mode_choice})...",
        file=sys.stderr,
    )

    processed_files_count = 0
    failed_files_details = {}  # Store path and error

    # --- Parallel Summarization and Injection ---
    if MAX_WORKERS <= 0:  # Sequential execution
        for path_to_process in all_project_files:
            try:
                print(
                    f"Processing (sequentially, mode: {llm_mode_choice}): {path_to_process}",
                    file=sys.stderr,
                )
                md_summary = readme_sync.summarise_file(
                    path_to_process, llm_mode_choice
                )
                if md_summary and not md_summary.startswith("Error:"):
                    readme_file_path = path_to_process.parent / "README.md"
                    readme_lock = readme_sync._get_readme_lock(readme_file_path)
                    with readme_lock:
                        readme_sync._inject(
                            readme_file_path, path_to_process.name, md_summary
                        )
                    processed_files_count += 1
                else:
                    failed_files_details[str(path_to_process.relative_to(ROOT))] = (
                        md_summary or "Unknown error during summarization"
                    )
                    print(
                        f"Skipping/Error for {path_to_process.name}: {md_summary[:100]}...",
                        file=sys.stderr,
                    )
            except Exception as exc:
                err_str = str(exc)
                failed_files_details[str(path_to_process.relative_to(ROOT))] = err_str
                print(
                    f"Error processing {path_to_process} sequentially: {err_str}",
                    file=sys.stderr,
                )
    else:  # Parallel execution
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Optional: Local LLM Preloading (adapted from readme_sync.py)
            if (
                llm_mode_choice == "1"
                and MAX_WORKERS > 0
                and hasattr(readme_sync, "local_llm")
                and hasattr(readme_sync.local_llm, "preload_model")
            ):
                print(
                    "Attempting to preload local model via executor...", file=sys.stderr
                )
                preload_future = executor.submit(readme_sync.local_llm.preload_model)
                try:
                    # Give it a reasonable timeout, but don't block indefinitely
                    if preload_future.result(
                        timeout=getattr(
                            readme_sync.local_llm, "LLM_FIRST_ATTEMPT_TIMEOUT", 60
                        )
                        + 10
                    ):
                        print(
                            "Local model preloaded successfully or was already loaded.",
                            file=sys.stderr,
                        )
                    else:
                        print(
                            "Local model preloading failed or indicated model was not ready.",
                            file=sys.stderr,
                        )
                except Exception as e:
                    print(
                        f"Error during local model preloading via executor: {e}",
                        file=sys.stderr,
                    )

            future_to_path = {
                executor.submit(readme_sync.summarise_file, p, llm_mode_choice): p
                for p in all_project_files
            }
            for i, future in enumerate(as_completed(future_to_path)):
                path_processed = future_to_path[future]
                try:
                    md_summary = future.result()
                    if md_summary and not md_summary.startswith("Error:"):
                        readme_file_path = path_processed.parent / "README.md"
                        readme_lock = readme_sync._get_readme_lock(readme_file_path)
                        with readme_lock:
                            readme_sync._inject(
                                readme_file_path, path_processed.name, md_summary
                            )
                        processed_files_count += 1
                    else:
                        failed_files_details[str(path_processed.relative_to(ROOT))] = (
                            md_summary or "Unknown error during summarization"
                        )
                        print(
                            f"Skipping/Error for {path_processed.name}: {md_summary[:100]}...",
                            file=sys.stderr,
                        )
                except Exception as exc:
                    err_str = str(exc)
                    failed_files_details[str(path_processed.relative_to(ROOT))] = (
                        err_str
                    )
                    print(
                        f"File {path_processed.name} generated an exception: {err_str}",
                        file=sys.stderr,
                    )

                # Print progress to server log
                print(
                    f"Web processed ({i+1}/{len(all_project_files)}): {path_processed.name}. Successes: {processed_files_count}",
                    file=sys.stderr,
                )

    final_token_count = readme_sync._TOTAL_TOKEN_COUNT
    result_message = f"Project processing complete. Processed {processed_files_count} of {len(all_project_files)} files successfully."
    if failed_files_details:
        result_message += f" {len(failed_files_details)} file(s) failed."
    result_message += f" Total tokens estimated for processed files: {final_token_count} (initial scan: {initial_total_tokens})."

    print(result_message, file=sys.stderr)

    return jsonify(
        message=result_message,
        processed_count=processed_files_count,
        total_files=len(all_project_files),
        failed_files=failed_files_details,  # Changed to dict for more detail
        total_tokens=final_token_count,
    )


if __name__ == "__main__":
    app.run(debug=True)
