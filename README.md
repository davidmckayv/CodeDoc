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

## PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
The file appears to be a part of a web application responsible for managing and processing project files, generating summaries, and updating README.md files. It provides a user interface for interacting with the application's functionality, including logging, file processing, and real-time log monitoring.

## KEY USER-FACING COMPONENTS AND USAGE:
- **`web_log` function**: Logs messages with timestamps for both server logging and UI display. Users can utilize this function to record significant events or errors within the application. Example: `web_log("Server started successfully.")`
- **`capture_stderr_globally` function**: A context manager that captures stderr output while still printing it to the actual stderr, allowing users to inspect or log stderr output. Example: `with capture_stderr_globally() as buffer: some_function_that_writes_to_stderr()`
- **`ensure_readme_sync_tokenizer_initialized` function**: Initializes the `readme_sync._TOKEN_ENCODING` variable if not already set, ensuring the tokenizer is ready for use. Users can call this function to guarantee tokenizer initialization. Example: `ensure_readme_sync_tokenizer_initialized()`
- **`get_project_files` function**: Retrieves a list of project files from a specified root directory, filtering by file extensions and exclusion rules. Example: `get_project_files(Path("/path/to/project"))`
- **`index` function**: Handles user requests to the root path, listing project files and rendering an HTML template. 
- **`generate` function**: A web application endpoint that generates a summary for a specified file and injects it into the corresponding README.md file. Users can call this endpoint with a valid file path and optionally select the LLM mode. Example: `generate(path="/path/to/file", llm_mode="1")`
- **`process_project` function**: Processes a project by summarizing its files and updating README.md files. Users can call this function via a web request, influencing execution with the `llm_mode` parameter. Example: `process_project(llm_mode="1")`
- **`log_stream` function**: Provides a server-sent event stream for real-time log monitoring, sending new log entries and processing status updates to connected clients.
<!-- END summary: web_app.py -->

<!-- BEGIN summary: local_llm.py -->
## local_llm.py

# File Summary

## PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
This file is primarily responsible for integrating with an Ollama LLM server, enabling users to interact with language models through a command-line interface. The main function, `llm_call`, is designed to process prompts and return responses, while the `preload_model` function ensures that necessary models are pre-loaded before processing tasks.

## KEY USER-FACING COMPONENTS AND USAGE:
### **llm_call (function, Python)**
- **Purpose:** This function makes a blocking HTTP POST request to an Ollama server using the `httpx` library. It caches responses for repeated prompts and includes error handling and retries with exponential backoff.
- **Key Actions/Logic:**
  - **Caching:** Responses are cached globally to improve performance.
  - **Retries:** The function retries up to a specified number of times, applying an exponential backoff strategy to handle transient issues. Special delays are applied for model loading errors.
  - **Error Handling:** Comprehensive error handling is implemented for network errors, HTTP status codes, and unexpected exceptions, with detailed logging.

- **Usage Patterns:**
  - **Basic Usage:** Call `llm_call` with a prompt to get a response from the Ollama server.
    ```python
    response = llm_call("What is the capital of France?")
    print(response)
    ```
  - **Error Handling:** Use a try-except block to handle potential errors gracefully.
    ```python
    try:
        result = llm_call("Invalid command")
    except Exception as e:
        print(f"Error: {e}")
    ```

### **preload_model (function, Python)**
- **Purpose:** This function ensures that specific language models are pre-loaded before starting any parallel processing tasks.
- **Key Actions/Logic:**
  - **Retries:** The function attempts to preload the model multiple times with increasing delays between attempts. It handles various exceptions such as HTTP errors and timeouts.
  - **Error Handling:** Detailed logging is provided to help developers monitor the progress of the preload process and troubleshoot any issues.

- **Usage Patterns:**
  - **Preloading Models:** Call `preload_model` once to ensure all necessary models are available for processing tasks.
    ```python
    if not preload_model():
        print("Model pre-loading failed")
    ```

### Additional Notes:
- The function uses the `httpx` library to communicate with the Ollama server for model loading and request handling.
- It includes robust error handling mechanisms to manage timeouts and retry logic based on specific error codes, ensuring reliable interaction with the LLM server.
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
This file provides a suite of functions designed to generate Markdown summaries and prompts for documenting various aspects of source code files, particularly focusing on user-facing components and integration. The primary technical responsibility is to facilitate the creation of comprehensive README.md files that highlight the main purpose, key functionalities, and usage patterns of code units such as functions, classes, and modules.

KEY USER-FACING COMPONENTS AND USAGE:
- **`get_llm_extract_generic_units_prompt`**: Generates a prompt for a Large Language Model to extract top-level code units from a given source code snippet. Users provide the programming language, file path, file extension, and source code snippet to receive a formatted prompt.
- **`get_python_syntax_error_prompt`**: Creates a Markdown-formatted prompt for assessing Python code snippets with syntax errors. Users input the file name, language extension, and code snippet to generate a structured assessment template.
- **`get_python_module_prompt`**: Generates a Markdown template for documenting a Python module, focusing on its purpose, key features, and typical usage. Users provide the module name, language extension, and source code snippet.
- **`get_python_class_prompt`**: Produces a Markdown template for documenting a Python class, emphasizing its public API and user interaction. Users input the class name, language extension, and source code snippet.
- **`get_python_function_prompt`**: Creates a Markdown summary for a Python function or method, detailing its purpose, parameters, return value, and primary use cases. Users provide the function/method name, kind (function/method), language extension, and source code snippet.
- **`get_generic_unit_prompt`**: Generates a Markdown template for documenting a generic code unit, focusing on its public API and user interaction. Users input the language extension, kind of code unit, unit name, and source code snippet.
- **`get_file_chunk_prompt`**: Creates a prompt for summarizing a given code segment from a file, focusing on its primary purpose and key operations. Users provide the file path, code chunk identifier, language extension, and source code snippet.
- **`get_default_file_summary_prompt`**: Generates a default prompt for summarizing a source code file, focusing on user-facing aspects. Users input the file name, language extension, and source code snippet.
- **`get_rollup_prompt`**: Consolidates input text blurbs into a structured Markdown summary suitable for README.md files, focusing on the file's primary technical responsibility and key user-facing components. Users provide a list of text blurbs describing different parts of a file.
- **`get_direct_summary_retry_prompt`**: Generates a prompt for retrying the creation of a comprehensive Markdown summary of a source code file, focusing on user-facing aspects. Users input the file path, file extension, and a snippet of the file content.
<!-- END summary: prompts.py -->

<!-- BEGIN summary: readme_sync.py -->
## readme_sync.py

PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
This file provides functionality for generating and updating README.md files by summarizing the content of various files using a Large Language Model (LLM). It includes features for processing single files, multiple paths, and directories, as well as handling different LLM modes and interactive or non-interactive processing.

KEY USER-FACING COMPONENTS AND USAGE:
- **`process_paths`**: Processes a list of file or directory paths to update corresponding README.md files by summarizing eligible files using a chosen LLM mode. It handles token counting, cleanup of stale entries, and parallel summarization.
  - Example: `process_paths([Path("file1.py"), Path("dir1")], Path("root_dir"), False, "local")`
- **`process_single_file`**: Generates a README.md summary for a specified file without interactive prompts, suitable for automated environments. It processes the file based on its extension and the specified LLM mode.
  - Example: `process_single_file(Path("script.py"), "local")`
- **`summarise_file`**: Generates a technical summary of a given file using a specified LLM mode. It analyzes the file's content, breaks it down into processable chunks, and creates a concise summary.
  - Example: `summarise_file(Path("example.py"), "1")`
- **`extract_code_units`**: Extracts code units from a given file based on its type and content. It reads the file, determines the appropriate extraction method, and returns a list of code units.
  - Example: `extract_code_units(Path("example.py"), "py", "1")`
- **`main`**: Serves as the entry point for the "readme-sync CLI" tool, processing files based on user-provided paths or scanning a specified root directory to generate or update README.md files.
  - Example: `main(["--root", "/path/to/codebase"])`
<!-- END summary: readme_sync.py -->