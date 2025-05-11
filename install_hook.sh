#!/usr/bin/env bash
# Run this installer from anywhere inside your Git repository. It creates
# a post‑commit hook that regenerates README summaries for each file
# touched in the commit and stages the updated READMEs.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOK="$REPO_ROOT/.git/hooks/post-commit"

cat > "$HOOK" <<'EOF'
#!/usr/bin/env bash
# post‑commit: refresh README summaries for changed files
set -euo pipefail

# Determine the repository root
REPO_ROOT=$(git rev-parse --show-toplevel)

# Activate virtual environment if it exists
VENV_ACTIVATE="$REPO_ROOT/.venv/bin/activate"
if [ -f "$VENV_ACTIVATE" ]; then
  source "$VENV_ACTIVATE"
else
  echo "Warning: Virtual environment activation script not found at $VENV_ACTIVATE" >&2
fi

changed_files=$(git diff-tree --no-commit-id --name-only -r HEAD)

for file in $changed_files; do
  # Ensure readme_sync.py is called with an absolute path if needed, or ensure it's in PATH
  # Assuming readme_sync.py is at the repo root for simplicity here.
  if [ -f "$REPO_ROOT/readme_sync.py" ]; then
    python "$REPO_ROOT/readme_sync.py" "$file"
    dir=$(dirname "$file")
    # Add README.md if it exists or was created.
    if [ -f "$dir/README.md" ]; then
      git add "$dir/README.md"
    fi
  else
    echo "Error: readme_sync.py not found at $REPO_ROOT/readme_sync.py" >&2
  fi
done
EOF

chmod +x "$HOOK"
echo "Git post-commit hook installed at $HOOK"
  