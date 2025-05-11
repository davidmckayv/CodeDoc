#!/usr/bin/env bash
# Run this installer from anywhere inside your Git repository. It creates
# a post-commit hook that regenerates README summaries for all files
# and stages the updated READMEs.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOK_DIR="$REPO_ROOT/.git/hooks"
HOOK_FILE="$HOOK_DIR/post-commit"
LOG_FILE_PATH_IN_HOOK="$REPO_ROOT/.git/post_commit_hook.log" # Define log file path

# Ensure the hooks directory exists
mkdir -p "$HOOK_DIR"

# Create the post-commit hook
cat > "$HOOK_FILE" <<EOF
#!/usr/bin/env bash
# post-commit: refresh README summaries (runs readme_sync.py in background)
LOG_FILE="${LOG_FILE_PATH_IN_HOOK}"

log_message() {
  echo "\$(date +'%Y-%m-%d %H:%M:%S') - HOOK_DEBUG: \$1" >> "\$LOG_FILE"
}

echo "\$(date +'%Y-%m-%d %H:%M:%S') - HOOK_DEBUG: post-commit hook script STARTING..." > "\$LOG_FILE"

set -euo pipefail
log_message "set -euo pipefail activated."

REPO_ROOT=\$(git rev-parse --show-toplevel)
log_message "HOOK SCRIPT: REPO_ROOT is \$REPO_ROOT"

PROJECT_ENVRC_FILE="\$REPO_ROOT/.envrc"
if [ -f "\$PROJECT_ENVRC_FILE" ]; then
  log_message "HOOK SCRIPT: Sourcing environment variables from \$PROJECT_ENVRC_FILE"
  set +o nounset
  source "\$PROJECT_ENVRC_FILE"
  set -o nounset
else
  log_message "HOOK SCRIPT: Project .envrc file not found at \$PROJECT_ENVRC_FILE"
fi

VENV_ACTIVATE="\$REPO_ROOT/.venv/bin/activate"
log_message "HOOK SCRIPT: VENV_ACTIVATE is \$VENV_ACTIVATE"
if [ -f "\$VENV_ACTIVATE" ]; then
  log_message "HOOK SCRIPT: Activating virtual environment..."
  source "\$VENV_ACTIVATE"
  log_message "HOOK SCRIPT: Virtual environment activated."
else
  log_message "HOOK SCRIPT: Warning: Virtual environment activation script not found at \$VENV_ACTIVATE"
fi

PYTHON_SCRIPT_PATH="\$REPO_ROOT/readme_sync.py"
log_message "HOOK SCRIPT: Checking for readme_sync.py at \$PYTHON_SCRIPT_PATH..."

if [ -f "\$PYTHON_SCRIPT_PATH" ]; then
  log_message "HOOK SCRIPT: readme_sync.py found. Executing in BACKGROUND: python \$PYTHON_SCRIPT_PATH --root \$REPO_ROOT --non-interactive --llm-mode remote"
  log_message "HOOK SCRIPT: --- readme_sync.py output (stdout & stderr) will be appended directly to this log (without line-by-line timestamps from hook) ---"
  
  nohup python "\$PYTHON_SCRIPT_PATH" --root "\$REPO_ROOT" --non-interactive --llm-mode remote >> "\$LOG_FILE" 2>&1 & disown
  PYTHON_BACKGROUND_PID=\$!
  log_message "HOOK SCRIPT: readme_sync.py launched in background with PID \$PYTHON_BACKGROUND_PID. It will continue to log here."

else
  log_message "HOOK SCRIPT: Error: readme_sync.py not found at \$PYTHON_SCRIPT_PATH"
  echo "POST-COMMIT HOOK ERROR: readme_sync.py not found at \$PYTHON_SCRIPT_PATH. Check \$LOG_FILE for details." >&2
  exit 1
fi

log_message "HOOK SCRIPT: post-commit hook FINISHED (readme_sync.py may still be running in background)."
echo "Post-commit hook finished (readme_sync.py launched in background). Details in: \$LOG_FILE"
EOF

# Make the hook executable
chmod +x "$HOOK_FILE"

echo "Git post-commit hook installer finished."
echo "Installed hook at: $HOOK_FILE"
echo "The hook will log its operations to: $LOG_FILE_PATH_IN_HOOK"
echo "The hook will run readme_sync.py in the background."
echo "The hook will NOT automatically stage README.md changes."
echo "The hook will attempt to source TOGETHER_API_KEY from: $REPO_ROOT/.envrc (if it exists)"
echo "Make sure readme_sync.py is present at $REPO_ROOT/readme_sync.py"
  