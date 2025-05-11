# ==> README.md <==
# readme-sync: Your Automatic Code Explainer for IDE RAG!

**`readme-sync` is designed to enhance your IDE experience by automatically generating and maintaining contextual README files within your codebase, perfect for powering in-IDE Retrieval Augmented Generation (RAG) and providing instant, relevant documentation where you code.**

Ever wished code could explain itself in plain English? `readme-sync` helps do just that! It reads through software code and automatically writes simple explanations (summaries) into special notes files (called READMEs) in each code folder. This makes it easier for anyone to understand what different parts of a software project are for.

**Main Features:**
*   Reads Python, JavaScript, TypeScript, Go, and Ruby code.
*   Uses AI (a local Ollama model by default, or configured remote OpenAI-compatible APIs) to generate code explanations.
*   Creates easy-to-understand summaries in `README.md` files within each relevant code folder.
*   Offers manual operation via a simple Web UI or a Command Line Interface (CLI).
*   Supports automatic updates of documentation via Git hooks for users of Git.

## Before You Start: Key Setup

1.  **Python Needs to Be on Your Computer:**
    *   `readme-sync` is written in Python. If you don\'t have Python installed, you\'ll need to get it. You can download it from [python.org](https://www.python.org/downloads/).
    *   During installation, make sure to check the box that says "Add Python to PATH" or similar.

2.  **Ollama: The Smart Assistant Behind the Scenes:**
    *   This tool needs another free program called **Ollama** to be running on your computer. Ollama is what actually understands the code and helps write the plain English summaries.
    *   **Download and Install Ollama:** Go to [ollama.com](https://ollama.com) and follow their instructions to install it on your computer.
    *   **Get a Model for Ollama:** Once Ollama is installed, it needs a "model" (like a specific brain for a task). `readme-sync` tries to use one called `qwen2.5-coder:3b` by default. To get this model, open your computer\'s command line or terminal application and type:
        ```
        ollama pull qwen2.5-coder:3b
        ```
        Press Enter and wait for it to download. You only need to do this once.
    *   **Keep Ollama Running:** When you want to use `readme-sync`, make sure the Ollama application is running.

3.  **Using Remote LLMs (Optional):**
    *   Besides the default local Ollama setup, `readme-sync` can also connect to remote LLMs that are compatible with the OpenAI API (e.g., for use with services like Together AI or others).
    *   To use a remote LLM, you will typically need to configure API keys and an API endpoint, usually via environment variables. Please refer to the tool's configuration options (e.g., environment variables, or CLI arguments like `python readme_sync.py --help`) for specific details on setting this up.

## How to Install `readme-sync`

These steps involve using your computer\'s **command line** or **terminal**. If you\'re not familiar with it, it\'s an application that lets you type commands directly to your computer.

1.  **Open Your Terminal:**
    *   On Windows, search for "Command Prompt" or "PowerShell".
    *   On Mac, search for "Terminal".
    *   On Linux, it\'s usually just "Terminal".

2.  **Create a Project Folder (Optional, but Recommended):**
    *   It\'s good practice to keep tools organized. You can make a folder for `readme-sync`. In your terminal, type:
        ```bash
        mkdir readme-sync-tool
        cd readme-sync-tool
        ```
    *   This creates a folder named `readme-sync-tool` and then moves you inside it.

3.  **Download `readme-sync`:**
    *   You\'ll need to get the `readme-sync.py` file, `web_app.py`, `requirements.txt`, and `install_hook.sh` from where you obtained this tool (e.g., download them into the folder you just created).

4.  **Set Up a "Virtual Environment" (A Clean Space for the Tool):**
    *   This step creates an isolated space for `readme-sync` so it doesn\'t interfere with other Python tools on your system.
        ```bash
        python -m venv .venv
        ```
    *   Now, activate it:
        *   On Windows:
            ```bash
            .venv\\Scripts\\activate
            ```
        *   On Mac/Linux:
            ```bash
            source .venv/bin/activate
            ```
        You should see `(.venv)` appear at the start of your terminal line.

5.  **Install Required Helper Tools:**
    *   `readme-sync` needs a couple of helper Python packages.
        ```bash
        pip install -r requirements.txt
        ```
    *   `pip` is Python\'s tool for installing packages, and `requirements.txt` is a list of the ones needed.

You\'re all set up! When you\'re done using `readme-sync` and want to leave the virtual environment, just type `deactivate` in the terminal and press Enter.

## How to Use `readme-sync`

Make sure Ollama is running before you use `readme-sync`.

### Option 1: The Easy Web Page (Recommended)

This is the simplest way to tell `readme-sync` to explain the code in a specific folder.

1.  **Open Your Terminal** (if it\'s not already open).
2.  **Navigate to the `readme-sync` Folder:** If you created a `readme-sync-tool` folder and downloaded the files there, `cd` into it.
    ```bash
    cd path/to/your/readme-sync-tool 
    ```
3.  **Activate the Virtual Environment** (if not already active):
    *   Windows: `.venv\\Scripts\\activate`
    *   Mac/Linux: `source .venv/bin/activate`
4.  **Start the Web App:**
    ```bash
    python web_app.py
    ```
5.  **Open Your Web Browser:** Go to [http://localhost:5000](http://localhost:5000).
6.  You\'ll see a list of code files from the folder where `web_app.py` is running (or a configured root folder). Click "Generate" next to a file to create its summary. The summary will be saved in a `README.md` file in the same folder as the code file. The web interface may also allow you to select your preferred LLM (local Ollama or a configured remote model) for generation, if multiple options are available and set up.

    *To make it scan a *different* codebase (not the folder where `readme-sync` itself is), you can tell it where your main code folder is by setting an environment variable `RMSYNC_ROOT` before running `web_app.py`. This is a bit more advanced, so for starting out, you can copy `web_app.py` and `readme_sync.py` into the root of the codebase you want to document.*

### Option 2: Using the Command Line (For Specific Folders)

This lets you tell `readme-sync` to process a specific folder (or even the whole codebase).

1.  **Open Your Terminal** and **activate the virtual environment** as described above.
2.  **Navigate to the `readme-sync` folder.**
3.  **Run the Command:**
    To explain all supported code files in a specific project folder, use:
    ```bash
    python readme_sync.py --root /full/path/to/your/codebase
    ```
    *   Replace `/full/path/to/your/codebase` with the actual full path to the main folder of the code you want to explain. For example, `C:\\Users\\YourName\\Documents\\MyProject` on Windows or `/Users/YourName/Projects/MyProject` on Mac. You may also be able to specify your preferred LLM (local Ollama or a configured remote model) and other settings via command-line arguments. Use `python readme_sync.py --help` to see all available options.

    This will find all relevant files inside that codebase, generate summaries, and save them into `README.md` files in each subfolder.

## Automatic Updates (For More Technical Users)

If you use Git (a system for tracking changes in code) and want the READMEs to update automatically every time you save changes to your code, there\'s a way to do that.

1.  Make sure you\'re in the main folder of *your own codebase* (the one you want to auto-document) in your terminal.
2.  Make sure the `install_hook.sh` file (that came with `readme-sync`) is also in that main folder.
3.  Run:
    ```bash
    ./install_hook.sh
    ```
This installs a "post-commit hook" that runs `readme-sync` on changed files after you "commit" (save) them in Git.

---

Let us know if this tool helps you understand your codebases better!

```bash
# 1. create venv and install deps
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2a. run once (CLI)
python readme_sync.py --root /path/to/codebase

# 2b. OR launch the web UI
python web_app.py  # then open http://localhost:5000

# 3. install the post‑commit hook to auto‑doc changed files
./install_hook.sh
```

> **Note**: The backend expects **Ollama** running locally (default
> endpoint `http://localhost:11434/api/generate`).

---

<!-- BEGIN summary: web_app.py -->
## web_app.py

PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
This file provides functionality for processing project files, generating summaries, and updating README.md files. It is primarily used through a web interface where users can initiate project processing and view the results.

KEY USER-FACING COMPONENTS AND USAGE:
- **`get_project_files`**: Retrieves a list of project files from a specified root directory, filtering by supported file extensions and exclusion rules. Users can call this function to gather files for further processing or analysis by providing a `root_path`.
- **`index`**: Generates and returns an HTML response listing project files relative to the root directory. Users interact with this function indirectly through a web interface.
- **`generate`**: Generates a summary for a specified file and injects it into the corresponding README.md file. Users can call this function by providing a file `path` and optionally specifying an `llm_mode`.
- **`process_project`**: Processes project files, generates summaries, and updates README.md files. Users typically initiate this function through a web interface, optionally specifying an `llm_mode`.
<!-- END summary: web_app.py -->

<!-- BEGIN summary: readme_sync.py -->
## readme_sync.py

PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
This file provides a set of functionalities for processing and summarizing code files, primarily through the use of Large Language Models (LLMs) and Abstract Syntax Tree (AST) analysis. It enables users to analyze codebases, generate technical summaries, and manage README files.

KEY USER-FACING COMPONENTS AND USAGE:
- **`extract_code_units`**: Extracts code units (functions, classes, etc.) from a given file based on its type and size. It handles chunking for large files and uses different extraction methods for various file extensions.
- **`summarise_file`**: Generates a technical summary of a given file by analyzing its content and utilizing a Large Language Model (LLM). Users can call this function to obtain a concise summary of a file's primary technical responsibility and key components.
- **`process_paths`**: Processes a list of file or directory paths to identify files for summarization, cleans up existing README files, and then summarizes the identified files using a chosen LLM mode. Users interact with this function by providing initial paths and responding to prompts.
- **`main`**: Serves as the entry point for a command-line interface (CLI) tool that scans a codebase for specific files to process based on user-provided paths or a root directory. It allows users to specify file paths or directories to process, filtering based on file extensions and exclusion patterns.
<!-- END summary: readme_sync.py -->

<!-- BEGIN summary: local_llm.py -->
## local_llm.py

PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
This file provides functionality for interacting with a local Ollama model via HTTP, allowing users to make calls to the model and preload it into memory for efficient processing.

KEY USER-FACING COMPONENTS AND USAGE:
- **`llm_call` Function**: Enables users to send a prompt to the Ollama model and receive a response. It handles caching, retries, and error management internally, making it a straightforward interface for integrating AI model responses into applications.
- **`preload_model` Function**: Allows users to preload the Ollama model into memory before starting processing tasks, ensuring it's ready for use and avoiding potential delays or errors during concurrent processing.
<!-- END summary: local_llm.py -->

<!-- BEGIN summary: remote_llm.py -->
## remote_llm.py

PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
This file provides functionality to interact with the OpenAI API using the Together API key and base URL, enabling users to make API requests and obtain responses from a remote LLM model. It handles client initialization, API calls, caching, and error handling.

KEY USER-FACING COMPONENTS AND USAGE:
- **`get_openai_client()`**: Initializes and returns an OpenAI client instance configured with the Together API key and base URL. Users call this function before making API requests to ensure proper client configuration.
- **`llm_call_remote(prompt, model_name=None)`**: Makes a blocking call to the Together AI API with the given prompt and model name, providing a cached response or an error message after retrying on failures. Users utilize this function to obtain responses from a remote LLM model.
<!-- END summary: remote_llm.py -->

<!-- BEGIN summary: prompts.py -->
## prompts.py

PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
This file provides a set of functions for generating Markdown summaries and prompts for documenting code units, files, and modules, primarily for README.md files, focusing on user-facing aspects and integration.

KEY USER-FACING COMPONENTS AND USAGE:
- **`get_llm_extract_generic_units_prompt`**: Generates a prompt for extracting top-level code units from a source code snippet. Users can call it with the language name, file path, extension, and source code snippet to obtain a structured prompt.
- **`get_python_syntax_error_prompt`**: Creates a Markdown assessment for a Python file with syntax errors. Users can call it with the file name, language extension, and code snippet to get a formatted README.md section.
- **`get_python_module_prompt`**: Generates a Markdown summary for a Python module. Users can call it with the module kind, name, language extension, and code snippet to obtain a structured summary.
- **`get_python_class_prompt`**: Creates a Markdown template for documenting a Python class. Users can call it with the class kind, name, language extension, and code snippet to get a summary.
- **`get_python_function_prompt`**: Generates a Markdown summary for a Python function or method. Users can call it with the function kind, name, language extension, and code snippet to obtain a standardized summary.
- **`get_generic_unit_prompt`**: Creates a Markdown template for documenting a generic code unit. Users can call it with the language extension, unit kind, name, and code snippet to get a structured summary.
- **`get_file_chunk_prompt`**: Generates a prompt for summarizing a code segment from a file. Users can call it with the file path, code chunk name, language extension, and code snippet to obtain a tailored prompt.
- **`get_default_file_summary_prompt`**: Creates a structured Markdown prompt for summarizing a source code file. Users can call it with the file name, language extension, and code snippet to get a formatted prompt.
- **`get_rollup_prompt`**: Generates a concise Markdown summary of a software file based on provided text blurbs. Users can call it with a list of blurbs to obtain a summary focusing on user-facing aspects.
- **`get_direct_summary_retry_prompt`**: Creates a prompt for retrying the generation of a concise Markdown summary of a code file. Users can call it with the file path, extension, and file content snippet to improve the initial summary.
<!-- END summary: prompts.py -->