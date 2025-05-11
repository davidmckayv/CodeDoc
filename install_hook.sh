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
# Unquoted EOF allows ${LOG_FILE_PATH_IN_HOOK} to expand.
# Other $ and $(...) must be escaped to be literal in the generated script.
cat > "$HOOK_FILE" <<EOF
#!/usr/bin/env bash
# post-commit: refresh README summaries
# Initialize log file path
LOG_FILE="${LOG_FILE_PATH_IN_HOOK}" # This expands when install_hook.sh runs

# Function to append messages to the log file
log_message() {
  echo "\$(date +'%Y-%m-%d %H:%M:%S') - HOOK_DEBUG: \$1" >> "\$LOG_FILE"
}

# Start logging for this hook execution
echo "\$(date +'%Y-%m-%d %H:%M:%S') - HOOK_DEBUG: post-commit hook script STARTING..." > "\$LOG_FILE"

set -euo pipefail
log_message "set -euo pipefail activated."

# Determine the repository root for the hook's execution
REPO_ROOT=\$(git rev-parse --show-toplevel)
log_message "HOOK SCRIPT: REPO_ROOT is \$REPO_ROOT"

# Source .envrc if it exists in the project root
PROJECT_ENVRC_FILE="\$REPO_ROOT/.envrc"
if [ -f "\$PROJECT_ENVRC_FILE" ]; then
  log_message "HOOK SCRIPT: Sourcing environment variables from \$PROJECT_ENVRC_FILE"
  # direnv typically uses 'export VAR=value'. Sourcing it directly might work.
  # If .envrc contains direnv-specific commands like 'dotenv', this simple source might not be enough.
  # However, if it just exports variables, this is fine.
  set +o nounset # Temporarily disable nounset for direnv, which might use unset variables
  source "\$PROJECT_ENVRC_FILE"
  set -o nounset # Re-enable nounset
else
  log_message "HOOK SCRIPT: Project .envrc file not found at \$PROJECT_ENVRC_FILE (this may be intentional)"
fi

# Activate virtual environment if it exists
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
  log_message "HOOK SCRIPT: readme_sync.py found. Executing: python \$PYTHON_SCRIPT_PATH --root \$REPO_ROOT --non-interactive --llm-mode remote"
  log_message "HOOK SCRIPT: --- readme_sync.py output (stdout & stderr) START ---"
  
  python "\$PYTHON_SCRIPT_PATH" --root "\$REPO_ROOT" --non-interactive --llm-mode remote >> "\$LOG_FILE" 2>&1
  PYTHON_EXIT_CODE=\$?
  
  log_message "HOOK SCRIPT: --- readme_sync.py output END ---"
  log_message "HOOK SCRIPT: readme_sync.py finished with exit code: \$PYTHON_EXIT_CODE"

  if [ \$PYTHON_EXIT_CODE -eq 0 ]; then
    log_message "HOOK SCRIPT: Staging potentially updated README.md files..."
    log_message "HOOK SCRIPT: Executing: find \$REPO_ROOT -type f -name README.md -print0 | xargs -0 --no-run-if-empty -t git add"
    log_message "HOOK SCRIPT: --- xargs git add output (stdout & stderr) START ---"
    find "\$REPO_ROOT" -type f -name "README.md" -print0 | xargs -0 --no-run-if-empty -t git add >> "\$LOG_FILE" 2>&1
    XARGS_EXIT_CODE=\$?
    log_message "HOOK SCRIPT: --- xargs git add output END ---"
    log_message "HOOK SCRIPT: xargs git add finished with exit code: \$XARGS_EXIT_CODE"
  else
    log_message "HOOK SCRIPT: readme_sync.py exited with error code \$PYTHON_EXIT_CODE. Skipping git add."
  fi
else
  log_message "HOOK SCRIPT: Error: readme_sync.py not found at \$PYTHON_SCRIPT_PATH"
  # Also echo to terminal for immediate feedback if script is missing
  echo "POST-COMMIT HOOK ERROR: readme_sync.py not found at \$PYTHON_SCRIPT_PATH. Check \$LOG_FILE for details." >&2
  exit 1
fi

log_message "HOOK SCRIPT: post-commit hook FINISHED successfully."
# Final message to terminal from the hook itself
echo "Post-commit hook finished. Details logged to: \$LOG_FILE"
EOF

# Make the hook executable
chmod +x "$HOOK_FILE"

echo "Git post-commit hook installer finished."
echo "Installed hook at: $HOOK_FILE"
echo "The hook will log its operations to: $LOG_FILE_PATH_IN_HOOK"
echo "The hook will attempt to source TOGETHER_API_KEY from: $REPO_ROOT/.envrc (if it exists)"
echo "Make sure readme_sync.py is present at $REPO_ROOT/readme_sync.py"
  