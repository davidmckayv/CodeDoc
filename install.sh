#!/usr/bin/env bash
# CodeDoc Installation Script
# This script sets up CodeDoc with options for documentation only or with GitHub hooks

set -euo pipefail

# Colors for prettier output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}CodeDoc Installation Script${NC}"
echo "------------------------------"

# Function to check if we're in a git repository
check_git_repo() {
    if ! git rev-parse --is-inside-work-tree &> /dev/null; then
        echo -e "${YELLOW}Warning: Not inside a Git repository.${NC}"
        echo "CodeDoc works best inside a Git repository, especially if you want to use the Git hooks feature."
        
        read -p "Do you want to continue anyway? (y/n): " continue_choice
        if [[ "$continue_choice" != "y" && "$continue_choice" != "Y" ]]; then
            echo "Installation aborted."
            exit 0
        fi
        
        # If continuing without git, set a fallback for REPO_ROOT
        REPO_ROOT="$(pwd)"
    else
        REPO_ROOT="$(git rev-parse --show-toplevel)"
        echo -e "${GREEN}Git repository detected at: $REPO_ROOT${NC}"
    fi
}

# Check for required files
check_required_files() {
    echo -e "${BLUE}Checking for required files...${NC}"
    
    MISSING_FILES=false
    
    if [ ! -f "$REPO_ROOT/readme_sync.py" ]; then
        echo -e "${RED}Error: readme_sync.py not found in $REPO_ROOT${NC}"
        MISSING_FILES=true
    else
        echo -e "${GREEN}readme_sync.py found${NC}"
    fi
    
    if [ ! -f "$REPO_ROOT/requirements.txt" ]; then
        echo -e "${RED}Error: requirements.txt not found in $REPO_ROOT${NC}"
        MISSING_FILES=true
    else
        echo -e "${GREEN}requirements.txt found${NC}"
    fi
    
    if [ ! -f "$REPO_ROOT/install_hook.sh" ]; then
        echo -e "${YELLOW}Warning: install_hook.sh not found in $REPO_ROOT${NC}"
        echo "Git hook installation will not be available."
    else
        echo -e "${GREEN}install_hook.sh found${NC}"
    fi
    
    if [ "$MISSING_FILES" = true ]; then
        echo -e "${RED}Some required files are missing. CodeDoc may not work correctly.${NC}"
        read -p "Do you want to continue anyway? (y/n): " continue_choice
        if [[ "$continue_choice" != "y" && "$continue_choice" != "Y" ]]; then
            echo "Installation aborted."
            exit 1
        fi
    fi
}

# Function to install Python dependencies
install_dependencies() {
    echo -e "${BLUE}Setting up Python virtual environment...${NC}"
    
    # Check if python3 is installed and get version
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: python3 is not installed. Please install Python 3.8 or higher.${NC}"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo -e "${GREEN}Found Python $PYTHON_VERSION${NC}"
    
    # Check Python version (ensure it's 3.8+)
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        echo -e "${RED}Error: Python 3.8+ is required, but you have $PYTHON_VERSION${NC}"
        read -p "Do you want to continue anyway? This might cause compatibility issues (y/n): " continue_choice
        if [[ "$continue_choice" != "y" && "$continue_choice" != "Y" ]]; then
            echo "Installation aborted."
            exit 1
        fi
    fi
    
    # Define virtual environment directory
    VENV_DIR="$REPO_ROOT/.venv"
    
    # Check if virtual environment exists
    if [ -d "$VENV_DIR" ]; then
        echo "Virtual environment already exists at $VENV_DIR"
        read -p "Do you want to use the existing environment? (y) or create a new one? (n): " use_existing
        if [[ "$use_existing" == "n" || "$use_existing" == "N" ]]; then
            echo "Removing existing virtual environment..."
            rm -rf "$VENV_DIR"
            echo "Creating new virtual environment in $VENV_DIR"
            python3 -m venv "$VENV_DIR"
        else
            echo "Using existing virtual environment"
        fi
    else
        echo "Creating new virtual environment in $VENV_DIR"
        python3 -m venv "$VENV_DIR"
    fi
    
    # Activate virtual environment
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    echo "Installing dependencies from requirements.txt"
    pip install --upgrade pip
    if ! pip install -r "$REPO_ROOT/requirements.txt"; then
        echo -e "${RED}Error installing dependencies. Check requirements.txt and try again.${NC}"
        read -p "Do you want to continue anyway? (y/n): " continue_choice
        if [[ "$continue_choice" != "y" && "$continue_choice" != "Y" ]]; then
            echo "Installation aborted."
            exit 1
        fi
    else
        echo -e "${GREEN}Dependencies installed successfully.${NC}"
    fi
}

# Function to set up environment variables
setup_environment() {
    echo -e "${BLUE}Setting up environment variables...${NC}"
    
    # Check if .envrc exists, create if not
    if [ ! -f "$REPO_ROOT/.envrc" ]; then
        echo "Creating .envrc file for API key storage"
        echo "The Together.ai API key is required for remote LLM processing."
        echo "If you don't have one, you can get it at https://together.ai/"
        echo -e "${YELLOW}Note: Without this key, only local LLM processing will work.${NC}"
        
        read -p "Enter your Together.ai API key (or press enter to skip): " API_KEY
        
        if [ -n "$API_KEY" ]; then
            echo "export TOGETHER_API_KEY=$API_KEY" > "$REPO_ROOT/.envrc"
            echo -e "${GREEN}API key saved to .envrc${NC}"
            
            # Inform about direnv if it's not installed
            if ! command -v direnv &> /dev/null; then
                echo -e "${YELLOW}Note: For automatic loading of environment variables, consider installing direnv:${NC}"
                echo "  https://direnv.net/"
                echo "Without direnv, you'll need to manually load the variables with:"
                echo "  source $REPO_ROOT/.envrc"
            else
                echo -e "${GREEN}direnv detected. Run 'direnv allow' to enable automatic loading of .envrc${NC}"
            fi
        else
            echo "# Add your Together AI API key here" > "$REPO_ROOT/.envrc"
            echo "export TOGETHER_API_KEY=your_api_key_here" >> "$REPO_ROOT/.envrc"
            echo -e "${YELLOW}No API key provided. You'll need to edit .envrc manually later.${NC}"
        fi
    else
        echo ".envrc file already exists."
        read -p "Do you want to update your API key? (y/n): " update_key
        if [[ "$update_key" == "y" || "$update_key" == "Y" ]]; then
            read -p "Enter your Together.ai API key: " API_KEY
            if [ -n "$API_KEY" ]; then
                # Preserve other environment variables in the file
                if grep -q "TOGETHER_API_KEY" "$REPO_ROOT/.envrc"; then
                    sed -i.bak "s/export TOGETHER_API_KEY=.*/export TOGETHER_API_KEY=$API_KEY/" "$REPO_ROOT/.envrc"
                    rm -f "$REPO_ROOT/.envrc.bak"
                else
                    echo "export TOGETHER_API_KEY=$API_KEY" >> "$REPO_ROOT/.envrc"
                fi
                echo -e "${GREEN}API key updated in .envrc${NC}"
            else
                echo -e "${YELLOW}No API key provided. No changes made to .envrc${NC}"
            fi
        fi
    fi
    
    # Load environment variables for the current session
    source "$REPO_ROOT/.envrc"
    
    echo -e "${GREEN}Environment setup complete.${NC}"
}

# Function to install git hook
install_git_hook() {
    echo -e "${BLUE}Installing Git hook...${NC}"
    
    # Check if the current directory is a git repository
    if ! git rev-parse --is-inside-work-tree &> /dev/null; then
        echo -e "${RED}Error: Not inside a Git repository. Git hook can't be installed.${NC}"
        echo "If you want to use the Git hook feature, please initialize a Git repository first:"
        echo "  git init"
        return 1
    fi
    
    # Check if install_hook.sh exists
    if [ ! -f "$REPO_ROOT/install_hook.sh" ]; then
        echo -e "${RED}Error: install_hook.sh not found in $REPO_ROOT${NC}"
        return 1
    fi
    
    # Run the hook installer script
    echo "Running hook installer..."
    if ! bash "$REPO_ROOT/install_hook.sh"; then
        echo -e "${RED}Error: Failed to install Git hook.${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Git hook installed successfully.${NC}"
    return 0
}

# Function to test that everything works
test_installation() {
    echo -e "${BLUE}Testing installation...${NC}"
    
    # Activate virtual environment
    source "$REPO_ROOT/.venv/bin/activate"
    
    # Try to run readme_sync in non-interactive mode with --help
    echo "Running a test with readme_sync.py to verify it works..."
    if ! python "$REPO_ROOT/readme_sync.py" --help > /dev/null 2>&1; then
        echo -e "${RED}Installation test failed. Please check for errors.${NC}"
        
        # Show more detailed error for debugging
        echo -e "${YELLOW}Detailed error output:${NC}"
        python "$REPO_ROOT/readme_sync.py" --help
        
        read -p "Continue despite test failure? (y/n): " continue_choice
        if [[ "$continue_choice" != "y" && "$continue_choice" != "Y" ]]; then
            echo "Installation aborted."
            exit 1
        fi
    else
        echo -e "${GREEN}Installation test successful!${NC}"
        echo "readme_sync.py is working correctly."
    fi
}

# Display instructions for usage
show_usage_instructions() {
    echo -e "${BLUE}Usage Instructions:${NC}"
    echo "------------------------------"
    echo "To use CodeDoc:"
    echo ""
    echo "1. Activate the virtual environment:"
    echo "   source $REPO_ROOT/.venv/bin/activate"
    echo ""
    echo "2. Run readme_sync.py to generate documentation:"
    echo "   python $REPO_ROOT/readme_sync.py [options] [paths]"
    echo ""
    echo "3. Common options include:"
    echo "   --non-interactive    Run without prompts"
    echo "   --llm-mode local     Use local LLM (slower but free)"
    echo "   --llm-mode remote    Use remote API (faster, requires API key)"
    echo ""
    
    if git rev-parse --is-inside-work-tree &> /dev/null; then
        echo "4. Git hook information:"
        echo "   - The Git hook is installed to run after each commit"
        echo "   - It will automatically update documentation for files changed in the commit"
        echo "   - Check $REPO_ROOT/.git/post_commit_hook.log for hook execution details"
        echo ""
    fi
    
    echo "For full documentation, run:"
    echo "  python $REPO_ROOT/readme_sync.py --help"
    echo ""
}

# Main installation flow
main() {
    # Welcome message with clear explanation
    echo -e "${BLUE}Welcome to CodeDoc installation${NC}"
    echo "------------------------------"
    echo "CodeDoc is a tool that automatically generates documentation for your code files"
    echo "and injects it into README.md files in each directory."
    echo ""
    echo "This installer will:"
    echo "  1. Check your environment for required components"
    echo "  2. Set up a Python virtual environment and install dependencies"
    echo "  3. Configure API keys for LLM processing"
    echo "  4. Optionally install a Git hook for automatic documentation updates"
    echo ""
    
    # Check if in a Git repository
    check_git_repo
    
    # Check for required files
    check_required_files
    
    # Installation options
    echo -e "${BLUE}Installation Options:${NC}"
    echo "1) Install documentation tools only"
    echo "2) Install documentation tools with Git hooks (requires Git repository)"
    echo "3) Exit"
    echo ""
    
    read -p "Select an option (1-3): " choice
    
    case $choice in
        1)
            echo -e "${BLUE}Installing documentation tools only...${NC}"
            install_dependencies
            setup_environment
            test_installation
            show_usage_instructions
            ;;
        2)
            echo -e "${BLUE}Installing documentation tools with Git hooks...${NC}"
            if ! git rev-parse --is-inside-work-tree &> /dev/null; then
                echo -e "${RED}Error: Not inside a Git repository. Git hook can't be installed.${NC}"
                read -p "Do you want to proceed with documentation tools only? (y/n): " fallback_choice
                if [[ "$fallback_choice" != "y" && "$fallback_choice" != "Y" ]]; then
                    echo "Installation aborted."
                    exit 0
                fi
                install_dependencies
                setup_environment
                test_installation
            else
                install_dependencies
                setup_environment
                install_git_hook
                test_installation
            fi
            show_usage_instructions
            ;;
        3)
            echo "Exiting installation."
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option. Please run the script again.${NC}"
            exit 1
            ;;
    esac
    
    echo ""
    echo -e "${GREEN}CodeDoc installation completed!${NC}"
    echo "------------------------------"
}

# Run the main function
main 