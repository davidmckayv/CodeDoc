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
This file provides logging, file processing, and project summarization functionalities for a web application, enabling users to generate summaries for project files and view real-time log updates.

KEY USER-FACING COMPONENTS AND USAGE:
- **`web_log`**: Logs messages to both the standard error stream and an internal buffer for potential UI display, providing a timestamp for each log entry. Users can call this function to log important events or messages during web application execution.
- **`capture_stderr_globally`**: Captures the stderr output of a code block while still displaying it on the actual stderr, allowing users to both log and inspect stderr messages. It is typically used within a `with` statement.
- **`index`**: Generates and returns an HTML response listing project files relative to the root directory, serving as the primary entry point for users. Users interact with this function indirectly by accessing the root path of the application.
- **`generate`**: Generates a summary for a specified file and injects it into the corresponding README.md file. It is typically called via a web request to process a file with a chosen LLM mode.
- **`process_project`**: Processes project files by summarizing them and updating the corresponding README.md files. It is typically called when a user initiates project processing through a web application interface.
- **`log_stream`**: Provides a stream of logs and status updates as server-sent events, allowing users to receive real-time updates on the application's logs and processing status. Users can call this function to establish a continuous log stream.
<!-- END summary: web_app.py -->

<!-- BEGIN summary: local_llm.py -->
## local_llm.py

PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
This file provides functionality for interacting with a local Ollama model via HTTP, allowing users to make calls to the model and preload it into memory for later use. It handles retries, caching, and error handling to provide a robust interface.

KEY USER-FACING COMPONENTS AND USAGE:
- **`llm_call` function**: Makes a blocking call to the Ollama model with a given prompt, handling retries and caching internally. Users can call this function with a simple query or complex prompt to receive a response from the model.
- **`preload_model` function**: Preloads the Ollama model into memory before it's needed, ensuring it's ready for parallel processing tasks. Users can call this function to initialize the model as a preparatory step in their workflow or pipeline.
<!-- END summary: local_llm.py -->

<!-- BEGIN summary: remote_llm.py -->
## remote_llm.py

PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
This file provides utility functions for logging, timestamping, and interacting with the OpenAI API or a compatible endpoint through a configured client instance. It enables users to log messages, retrieve the current timestamp, and make calls to a remote LLM model.

KEY USER-FACING COMPONENTS AND USAGE:
- **`get_timestamp()`**: Retrieves the current date and time in a human-readable format. Users can call this function to get the current timestamp for logging or displaying purposes.
- **`log_message(message, file=sys.stderr)`**: Logs a message with a timestamp prefix to the standard error stream or a specified file. Users can utilize this function for tracking events or errors in their application.
- **`get_openai_client()`**: Returns a configured OpenAI client instance. Users need to call this function to obtain a client instance before making API requests to the OpenAI API or a compatible endpoint.
- **`llm_call_remote(prompt, model_name=None)`**: Makes a blocking call to the Together AI API to get a response to a given prompt from a remote LLM model. Users can use this function to get responses from the LLM model for their input prompts.
<!-- END summary: remote_llm.py -->

<!-- BEGIN summary: prompts.py -->
## prompts.py

PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
This file provides a set of functions for generating Markdown summaries and prompts for documenting code files, focusing on user-facing aspects and integration. The primary role is to aid users in creating concise technical summaries for README.md files.

KEY USER-FACING COMPONENTS AND USAGE:
- **`get_llm_extract_generic_units_prompt`**: Generates a prompt for extracting top-level code units from a given source code snippet. Users call this function by providing the language name, file path, file extension, and source code snippet to create a structured prompt for code analysis tasks.
- **`get_python_syntax_error_prompt`**: Creates a Markdown assessment for a Python file with syntax errors. Users utilize this function by passing the file name, language extension, and the Python code snippet to obtain a formatted report.
- **`get_python_module_prompt`**: Generates a Markdown template for documenting a Python module. Users call this function with the module's kind, name, language extension, and source code snippet to create a summary for a README.md file.
- **`get_python_class_prompt`**: Produces a Markdown template for documenting a Python class. Users can call this function with the class's kind, name, language extension, and source code snippet to generate a summary focusing on user interaction and public API.
- **`get_python_function_prompt`**: Creates a Markdown summary for a Python function or method. Users utilize this function by providing the kind, name, language extension, and source code snippet to document their Python code.
- **`get_generic_unit_prompt`**: Generates a Markdown template for documenting a generic code unit. Users can call this function with the language extension, kind, name, and source code snippet to create README.md summaries for various code units.
- **`get_file_chunk_prompt`**: Generates a prompt for summarizing a given code segment from a file. Users call this function with the file path, code chunk identifier, language extension, and source code snippet to aid in creating concise technical summaries.
- **`get_default_file_summary_prompt`**: Produces a structured Markdown prompt for creating a file overview in a README.md. Users utilize this function by providing the file name, language extension, and source code snippet to obtain a template for summarizing a source code file's purpose and key functionalities.
- **`get_rollup_prompt`**: Generates a concise Markdown summary of a software file based on provided text blurbs. Users call this function with a list of blurbs describing different parts of a file to create a README.md summary focusing on user-facing aspects.
- **`get_direct_summary_retry_prompt`**: Creates a prompt for generating a concise Markdown summary of a code file, particularly for retry attempts. Users or automated systems call this function with the file path, extension, and file content snippet to retry generating a summary after an initial failure.
<!-- END summary: prompts.py -->

<!-- BEGIN summary: readme_sync.py -->
## readme_sync.py

PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
This file is primarily responsible for processing files or directories to generate and update README content with summaries of the files' content and technical responsibilities. It provides a command-line interface (CLI) for users to interact with.

KEY USER-FACING COMPONENTS AND USAGE:
- **`main`**: The entry point of the application, allowing users to process specific files or scan a codebase root directory for files to synchronize README content. Users can provide command-line arguments to specify files, directories, or configuration options.
- **`process_paths`**: Processes a list of file or directory paths to identify files for summarization, clean up existing README files, and generate new summaries using a chosen LLM mode. Users can run this function in interactive or non-interactive mode.
- **`summarise_file`**: Generates a summary of a given file by breaking it into chunks, analyzing each chunk using a Large Language Model (LLM), and then rolling up the results into a final summary. Users can call this function to obtain a technical overview of a file's content and structure.
- **`extract_code_units`**: Extracts code units from a given file based on its type and size, handling large files by chunking them into smaller parts. Users can call this function to process various file types for further analysis or processing.
- **`log_message`**: Allows users to log messages with a timestamp prefix, typically for tracking events or debugging purposes. Users can call this function to output messages to the standard error stream or a specified file.
- **`get_timestamp`**: Retrieves the current date and time in a human-readable format. Users can call this function to obtain a timestamp for logging, recording events, or displaying the current time in their application.
<!-- END summary: readme_sync.py -->