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
This file provides logging, project file management, and README.md generation functionalities, enabling users to monitor and document their projects effectively.

KEY USER-FACING COMPONENTS AND USAGE:
- **`web_log`**: Logs messages to both the standard error stream and an internal buffer for potential UI display, allowing users to record significant events or errors.
- **`capture_stderr_globally`**: Captures stderr output globally while still displaying it on the actual stderr, enabling users to inspect or log the output as needed within a `with` statement.
- **`get_project_files`**: Retrieves a list of project files from a specified root directory based on supported file extensions and exclusion rules, useful for tasks like documentation generation or code analysis.
- **`index`**: Generates and returns an HTML response displaying a list of project files, typically called when a user accesses the root path of the application.
- **`generate`**: Generates a summary for a specified file and injects it into the corresponding README.md file, usually called via a web request with the file path and desired LLM mode.
- **`process_project`**: Processes project files, generating summaries and updating README.md files accordingly, typically initiated via a web request.
- **`log_stream`**: Provides a stream of logs as server-sent events, allowing users to receive real-time updates on logs and processing status.
<!-- END summary: web_app.py -->

<!-- BEGIN summary: local_llm.py -->
## local_llm.py

PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
This file provides functionality for interacting with a local Ollama model, enabling users to send prompts and receive responses, as well as preload the model for efficient parallel processing.

KEY USER-FACING COMPONENTS AND USAGE:
- **`llm_call` function**: Sends a prompt to the Ollama model and returns its response. Users can utilize this function to query the model with specific prompts and handle the returned responses or error messages.
- **`preload_model` function**: Preloads the Ollama model into memory to ensure it's ready for use. Users can call this function to initialize the model before performing other operations and check its success status.
<!-- END summary: local_llm.py -->

<!-- BEGIN summary: remote_llm.py -->
## remote_llm.py

PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
This file provides functionality for logging, timestamping, and interacting with the OpenAI API using the Together API settings, enabling users to log messages, generate timestamps, and create content using AI models.

KEY USER-FACING COMPONENTS AND USAGE:
- **`get_timestamp()`**: Retrieves the current date and time in a human-readable format ("YYYY-MM-DD HH:MM:SS"), useful for logging or displaying the current time to users. Users can call this function to get the current timestamp.
- **`log_message(message, file=sys.stderr)`**: Logs a message with a timestamp prefix to the standard error stream or a specified file, typically for tracking events or debugging purposes. Users can call this function to log messages.
- **`get_openai_client()`**: Retrieves an OpenAI client instance configured with the Together API settings, allowing users to interact with the OpenAI API. Users typically call this function to initialize the OpenAI client for making API requests.
- **`llm_call_remote(prompt, model_name=None)`**: Makes a blocking call to the Together AI API to generate content based on a given prompt, utilizing caching and retries. Users can call this function to obtain generated content for their specific prompts.
<!-- END summary: remote_llm.py -->

<!-- BEGIN summary: prompts.py -->
## prompts.py

PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
This file provides a set of functions for generating Markdown summaries and prompts for documenting various code units and files, primarily focusing on user-facing aspects for README.md files.

KEY USER-FACING COMPONENTS AND USAGE:
- **`get_llm_extract_generic_units_prompt`**: Generates a prompt for extracting top-level code units from a given source code snippet. Users can call this function with the language name, file path, file extension, and source code snippet to obtain a formatted prompt.
- **`get_python_syntax_error_prompt`**: Creates a Markdown-formatted assessment prompt for a Python code snippet with syntax errors. Users can utilize this function by providing the file name, language extension, and the errored Python code snippet.
- **`get_python_module_prompt`**: Generates a Markdown template for documenting a Python module. Users can call this function with the module's kind, name, language extension, and source code snippet to create a summary.
- **`get_python_class_prompt`**: Produces a Markdown template for documenting a Python class, focusing on user interaction and public API. Users can use this function by passing the class's kind, name, language extension, and source code snippet.
- **`get_python_function_prompt`**: Creates a concise Markdown summary for a Python function or method. Users can call this function with the code snippet's kind, name, language extension, and source code to generate a summary.
- **`get_generic_unit_prompt`**: Generates a Markdown template for documenting a generic code unit. Users can utilize this function by providing the language extension, kind, name, and source code snippet of the code unit.
- **`get_file_chunk_prompt`**: Generates a prompt for summarizing a specific code segment from a file. Users can call this function with the file path, name for the prompt, language extension, and source code snippet to create a summary prompt.
- **`get_default_file_summary_prompt`**: Creates a default prompt for summarizing a file's content in a structured Markdown format. Users can use this function by providing the file name, language extension, and source code snippet.
- **`get_rollup_prompt`**: Generates a concise Markdown summary of a software file for README.md, focusing on user-facing aspects. Users can call this function with a list of text blurbs describing different parts of the file.
- **`get_direct_summary_retry_prompt`**: Generates a prompt for creating a concise Markdown summary of a code file, particularly for retry attempts. Users can utilize this function by providing the file path, extension, and a snippet of the file's content.
<!-- END summary: prompts.py -->

<!-- BEGIN summary: readme_sync.py -->
## readme_sync.py

PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
This file provides functionality for generating and managing README.md summaries for code files using Large Language Models (LLMs), enabling users to understand codebases more efficiently.

KEY USER-FACING COMPONENTS AND USAGE:
- **`process_single_file`**: Generates a README.md summary for a specified file using a chosen LLM mode (local or remote). Example: `process_single_file(Path("path/to/file.py"), "local")`.
- **`process_paths`**: Processes a list of file or directory paths to identify files for summarization, cleans up existing README files, and generates summaries using a chosen LLM mode. Example: `process_paths([Path("file1.py"), Path("dir1")], Path("root_dir"), False, "local")`.
- **`log_message`**: Logs messages with a timestamp prefix to the standard error stream or a specified file. Example: `log_message("User logged in successfully")`.
- **`get_timestamp`**: Retrieves the current date and time in a human-readable format. Example: `print(f"Event occurred at: {get_timestamp()}")`.
- **`summarise_file`**: Generates a summary of a given file based on its content and the chosen LLM mode. Example: `summarise_file(Path("example.py"), "1")`.
- **`extract_code_units`**: Extracts code units from a given file based on its type and size, adapting to different LLM modes. Example: `extract_code_units(Path("example.py"), "py", "1")`.
<!-- END summary: readme_sync.py -->