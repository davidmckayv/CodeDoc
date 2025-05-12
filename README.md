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

**For Non-Technical Readers:**
This software component is designed to manage and process project files, generate summaries, and update README.md files. It provides real-time log streaming and monitoring capabilities, making it easier for users to track project status and understand file contents without manually reviewing each file. The component is useful for project management, debugging, and documentation purposes.

**PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:**
The primary technical responsibility of this component is to provide a user-friendly interface for processing project files, generating summaries, and updating README.md files. It also offers real-time log streaming and monitoring, enabling users to track project status and file contents efficiently.

**KEY USER-FACING COMPONENTS AND USAGE:**
- **`web_log` (function)**: Logs messages visible to users and recorded in server logs for debugging and tracking purposes. Users can utilize this function to log important events or errors.
- **`capture_stderr_globally` (function)**: Captures standard error output while displaying it to the user in real-time. This is useful for logging or debugging purposes.
- **`index` (function)**: Generates a webpage listing project files. Users can access this function by visiting the project's root URL.
- **`generate` (function)**: Generates a summary for a given file and updates the corresponding README.md file. Users can call this function via a web application interface to summarize specific files.
- **`process_project` (function)**: Processes a project by summarizing its files and updating README.md files. Users can initiate this function through a web interface to process entire projects.
- **`log_stream` (function)**: Streams log updates and server status as events to the client. This is useful for real-time monitoring and debugging purposes.

These components work together to provide a comprehensive project management and documentation solution, enhancing user experience through efficient file processing, summarization, and real-time monitoring.
<!-- END summary: web_app.py -->

<!-- BEGIN summary: local_llm.py -->
## local_llm.py

**For Non-Technical Readers:**
This software component is designed to interact with a language model, a type of AI that can understand and generate human-like text. It includes two main functionalities: sending requests to the language model and getting responses, and preloading the language model into the computer's memory for efficient use. These features are useful for automating tasks that involve text understanding or generation, such as answering questions, summarizing content, or creating text. By preloading the model, the system ensures quick responses when needed.

**PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:**
The primary technical responsibility of this file is to facilitate interaction with a language model through two main functions: sending requests and receiving responses, and preloading the model for efficient use. This involves handling the communication between the user's application and the language model, ensuring robustness and efficiency.

**KEY USER-FACING COMPONENTS AND USAGE:**
- **`llm_call` function**: This function sends a request to the language model and returns a response. It takes a text prompt and optionally a file path as input. Users can utilize this function to ask questions, request text summarization, or generate text. The function includes features like request retrying and caching to ensure robustness.
- **`preload_model` function**: This function preloads the language model into memory, ensuring it's ready for use when needed. It doesn't require any input parameters and returns a boolean indicating whether the preloading was successful. Users can call this function before starting tasks that rely on the language model to avoid initial delays.
<!-- END summary: local_llm.py -->

<!-- BEGIN summary: remote_llm.py -->
## remote_llm.py

**For Non-Technical Readers:**
This file contains functions that help with logging events, generating timestamps, and interacting with AI models to generate text or answer questions. It's like having a toolkit that includes a clock for tracking time, a notepad for logging events, and a super-smart assistant for generating content or answering questions. These tools are useful for building applications that need to track events, display the current time, or leverage AI for various tasks.

PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
The file is primarily responsible for providing utility functions that enable applications to log messages with timestamps, interact with OpenAI's services for AI-related tasks, and generate timestamps for various uses.

KEY USER-FACING COMPONENTS AND USAGE:
- **`get_timestamp`**: Generates a human-readable timestamp representing the current date and time. It's used for logging events, displaying the current time, or recording when actions occur. Example: `timestamp = get_timestamp(); print(f"Event logged at: {timestamp}")`
- **`log_message`**: Logs a message with a timestamp to a specified destination, such as the standard error stream or a file. It's useful for tracking events or debugging. Example: `log_message("User logged in successfully")`
- **`get_openai_client`**: Establishes a connection to OpenAI's services using predefined settings and credentials. It's necessary for applications that need to interact with OpenAI's AI models. Example: `client = get_openai_client(); response = client.chat.completions.create(...)`
- **`llm_call_remote`**: Sends a prompt to a remote Large Language Model (LLM) and retrieves a response. It's useful for tasks like generating content, answering questions, or summarizing text. Example: `response = llm_call_remote("Generate a summary of this text.")`
<!-- END summary: remote_llm.py -->

<!-- BEGIN summary: prompts.py -->
## prompts.py

**For Non-Technical Readers:**
This file contains a collection of functions designed to generate summaries and documentation for code files in a human-readable format, particularly for README.md files. These functions help users understand what the code does, how to use it, and its key features, making it easier for both technical and non-technical individuals to comprehend complex codebases.

PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
The primary purpose of this file is to provide a set of functions that generate Markdown summaries and prompts for code documentation, focusing on user-facing aspects. These functions are designed to be used in generating README.md files, improving the understandability and usability of code for end-users and integrators.

KEY USER-FACING COMPONENTS AND USAGE:
- **`get_llm_extract_generic_units_prompt`**: Generates a prompt for a Large Language Model to extract top-level code units from a given source code snippet. Users provide the language name, file path, file extension, and source code snippet, and the function returns a formatted prompt.
- **`get_python_syntax_error_prompt`**: Creates a Markdown-formatted assessment for a Python code snippet with syntax errors, providing insights into the code's likely purpose and identifiable structures.
- **`get_python_module_prompt`**: Generates a Markdown summary for a Python module, including its purpose, key features, and typical usage scenarios.
- **`get_python_class_prompt`**: Produces a Markdown template for documenting a Python class, including explanations of its purpose, public attributes and methods, and usage examples.
- **`get_python_function_prompt`**: Creates a Markdown summary for a Python function or method, focusing on its purpose, parameters, return values, and typical use cases.
- **`get_generic_unit_prompt`**: Generates a Markdown template for documenting a code unit (like a function, class, or script), focusing on its purpose, public interface, and use cases.
- **`get_file_chunk_prompt`**: Creates a prompt for summarizing a specific segment of code within a file, focusing on its primary purpose and key operations.
- **`get_default_file_summary_prompt`**: Generates a structured Markdown overview for a README.md file, focusing on user-facing aspects and integration points.
- **`get_rollup_prompt`**: Consolidates a list of text descriptions about different parts of a software file into a comprehensive Markdown summary, focusing on user-facing aspects.
- **`get_direct_summary_retry_prompt`**: Creates a Markdown prompt for summarizing a code file, focusing on its primary technical responsibility, key user-facing components, and source code snippet.

These functions are designed to be used in various scenarios, such as generating README.md summaries for code files, documenting Python modules and classes, and creating overviews for code snippets. By providing a structured and user-focused approach to code documentation, these functions aim to improve the usability and understandability of complex codebases.
<!-- END summary: prompts.py -->

<!-- BEGIN summary: readme_sync.py -->
## readme_sync.py

**For Non-Technical Readers:**
This software file is part of a tool designed to manage and document codebases by generating summaries of code files and updating a project's main documentation file (README.md). It helps developers and users understand the purpose and functionality of different parts of a project. The tool can automatically scan files, identify key components, and create concise summaries, making it easier to maintain and navigate complex projects.

PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
The file is primarily responsible for providing functionalities that enable the summarization of code files and the management of a project's README.md file. It includes functions for generating timestamps, logging messages, processing file paths, and updating the README file with summaries of code files.

KEY USER-FACING COMPONENTS AND USAGE:
- **`get_timestamp`**: Generates a human-readable timestamp representing the current date and time. Useful for logging events or displaying the current time in applications.
- **`log_message`**: Logs a message with a timestamp to a specified output stream (default is standard error). Useful for tracking events or debugging.
- **`is_path_excluded`**: Checks if a given file system path should be excluded based on predefined directory and file patterns. Useful for filtering out unwanted files or directories during processing.
- **`extract_code_units`**: Extracts meaningful code units (like functions or classes) from a given file based on its type and content. Useful for analyzing or documenting code.
- **`summarise_file`**: Generates a summary of a given file using a Large Language Model (LLM). Useful for understanding the file's purpose and key components.
- **`process_paths`**: Processes a list of file paths to identify files for summarization, generates summaries, and updates the corresponding README.md files. Useful for maintaining documentation across multiple files or directories.
- **`process_single_file`**: Processes a single file by generating a summary and updating the relevant README.md file. Useful for automated environments like CI/CD pipelines.
- **`main`**: The entry point for a command-line interface that allows users to customize how files are processed within a codebase. Useful for developers who need to manage or update multiple files within their projects.
<!-- END summary: readme_sync.py -->