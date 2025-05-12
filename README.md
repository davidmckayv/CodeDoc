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
This software component is designed to manage and process project files, generate summaries, and maintain a log of events. It's like having a personal assistant that keeps track of project details, helps in understanding the project's structure, and monitors its progress in real-time. This is useful for project maintainers and users who need to stay updated on the project's status and understand its components.

**PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:**
The primary purpose of this file is to provide a set of functionalities that enable project file management, summarization, and real-time logging. It is designed to be used in a web application context, where users can interact with it through a user interface or API.

**KEY USER-FACING COMPONENTS AND USAGE:**
- **`web_log` function**: Logs messages with timestamps, useful for understanding the application's activities and troubleshooting. Example: `web_log("User logged in successfully")`
- **`capture_stderr_globally` function**: Captures error messages while still displaying them to the user, useful for logging and debugging purposes.
- **`get_project_files` function**: Retrieves a list of project files based on specified criteria, useful for bulk processing or analysis. Example: `get_project_files(project_root_directory)`
- **`index` function**: Generates the main page of the web application, listing project files for the user. It's called when a user navigates to the root URL.
- **`generate` function**: Generates a summary for a given file and updates the corresponding README.md file. Example: `generate(file_path, llm_mode="2")`
- **`process_project` function**: Processes a project by summarizing its files and updating the README.md. Example: `process_project(llm_mode="2")`
- **`log_stream` function**: Provides a continuous stream of log updates and status information to the user, useful for real-time monitoring.
<!-- END summary: web_app.py -->

<!-- BEGIN summary: local_llm.py -->
## local_llm.py

**For Non-Technical Readers:**
This software component is designed to interact with a language model, a type of artificial intelligence, to generate responses to user queries. It's like having a knowledgeable assistant that can answer questions or provide information on a wide range of topics. The component is made up of two main parts: one that sends requests to the language model and gets responses back, and another that prepares the language model for use by loading it into the computer's memory. This ensures that the model is ready to provide fast and accurate responses when needed.

PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
The primary role of this file is to facilitate interaction with a language model by providing a reliable way to send requests and get responses, as well as to preload the model into memory for efficient use. This is crucial for applications that rely on the language model for their core functionality, such as chatbots or conversational interfaces.

KEY USER-FACING COMPONENTS AND USAGE:
- **`llm_call` (Function)**: This function is used to send a prompt or question to the language model and retrieve a response. It is designed to be reliable, with features like caching responses to avoid redundant requests, retrying failed requests, and logging attempts for debugging. A user can call this function with a specific question or prompt, such as `llm_call("What is the capital of France?")`, to get a response from the language model.
- **`preload_model` (Function)**: This function is used to load the language model into memory before it's actually needed, ensuring it's ready for use without delay. It's particularly useful for initializing a system or application that relies on the language model. A developer might call `preload_model()` at the start of their application to preload the model. The function returns a boolean value indicating whether the preloading was successful.
<!-- END summary: local_llm.py -->

<!-- BEGIN summary: remote_llm.py -->
## remote_llm.py

**For Non-Technical Readers:**
This file provides a set of tools that help applications interact with AI services, log important events, and track when these events happen. Imagine having a personal assistant that not only helps you with tasks but also keeps a record of everything that's happening, including the time it happens. It's useful for making applications more informative, efficient, and reliable.

**PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:**
The file is primarily responsible for facilitating interactions with AI models, logging messages with timestamps, and generating timestamps. It acts as a bridge between the application and external services like OpenAI, while also providing essential logging and timestamping functionalities.

**KEY USER-FACING COMPONENTS AND USAGE:**
- **`get_timestamp`**: Generates the current date and time in a human-readable format. It's used for logging, data tracking, or displaying the current time to users. Example: `timestamp = get_timestamp(); print(f"Event logged at: {timestamp}")`
- **`log_message`**: Logs messages with timestamps. It's typically used for recording events or errors in an application. Example: `log_message("An error occurred while processing the request.")`
- **`get_openai_client`**: Creates and returns a client object to interact with OpenAI services. It's used for generating text, answering questions, or other AI-related tasks. Example: `client = get_openai_client(); response = client.completions.create(...)`
- **`llm_call_remote`**: Sends a prompt to a remote AI model and receives a response. It's useful for generating content, describing technical concepts, or creating examples. Example: `response = llm_call_remote("Describe the purpose of this code.")`
<!-- END summary: remote_llm.py -->

<!-- BEGIN summary: prompts.py -->
## prompts.py

**For Non-Technical Readers:**
This file contains a collection of functions designed to generate summaries and documentation for code files in a user-friendly format. It's like having a tool that helps explain complex code in simple terms, making it easier for both technical and non-technical users to understand the code's purpose and functionality.

PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
The primary purpose of this file is to provide a set of functions that generate Markdown summaries and documentation templates for code files, focusing on user-facing aspects and making complex code more accessible.

KEY USER-FACING COMPONENTS AND USAGE:
- **`get_llm_extract_generic_units_prompt`**: Generates a prompt to help a system understand and extract important code structures from a given piece of source code. It guides the system to identify top-level code units such as functions, classes, or methods.
- **`get_python_syntax_error_prompt`**: Creates a Markdown-formatted report for a Python code snippet with syntax errors, helping users understand what's wrong and how to fix it.
- **`get_python_module_prompt`**: Generates a Markdown summary for a Python module, explaining its purpose, key features, and typical usage scenarios.
- **`get_python_class_prompt`**: Creates a Markdown template for documenting a Python class, including its purpose, key attributes, inheritance, public methods, and primary use cases.
- **`get_python_function_prompt`**: Generates a Markdown summary for a Python function or method, detailing its purpose, parameters, return values, and typical use cases.
- **`get_generic_unit_prompt`**: Creates a Markdown template for documenting a code unit (like a function, class, or script) in a user-friendly way, adjusting its output based on the type of code unit.
- **`get_file_chunk_prompt`**: Generates a structured prompt for summarizing a specific part of a code file, focusing on its main tasks and how it fits into the larger file.
- **`get_default_file_summary_prompt`**: Creates a structured Markdown overview for a README.md file, focusing on aspects relevant to users or integrators.
- **`get_rollup_prompt`**: Generates a comprehensive Markdown summary of a software file based on provided text blurbs, focusing on user-facing aspects.
- **`get_direct_summary_retry_prompt`**: Creates a structured prompt for summarizing a code file, highlighting its main technical purpose and user-facing components.
<!-- END summary: prompts.py -->

<!-- BEGIN summary: readme_sync.py -->
## readme_sync.py

**For Non-Technical Readers:**
This software helps manage and document code files within a project by generating summaries and updating a README file. It's like having an assistant that keeps track of what each part of your project does and ensures the documentation is up-to-date. This is useful for developers working on large projects, as it makes it easier to understand the project's structure and components.

PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
The primary purpose of this code is to process files within a project, generate summaries of their content, and update a README file with these summaries. It is designed to be flexible, allowing users to choose between different modes of operation (interactive or non-interactive) and different methods for generating summaries (local or remote Large Language Models).

KEY USER-FACING COMPONENTS AND USAGE:
- **`process_paths`**: This function processes a list of file or directory paths, summarizing eligible files and updating README files accordingly. It's useful for batch processing multiple files or directories.
  - Example: `process_paths([Path("file1.py"), Path("dir1")], Path("/project/root"), False, "local")`
- **`process_single_file`**: This function generates a summary for a single specified file and updates the corresponding README.md file. It's useful for automating the documentation process for individual files.
  - Example: `process_single_file(Path("script.py"), "local")`
- **`main`**: This is the entry point for the command-line tool, allowing users to configure how they want to process their codebase's README files. It supports various parameters for customizing the processing behavior.
  - Example: `main(["--root", "/path/to/codebase"])` or `main(["--single-file-mode", "/path/to/file1"])`

These components work together to provide a flexible and automated way to keep project documentation up-to-date and accurate.
<!-- END summary: readme_sync.py -->