"""CLI + library: crawl repo, summarise files, inject into README.md."""

import argparse
import ast
import hashlib
import os
import re
from pathlib import Path
from typing import Iterable
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import fnmatch  # Added import
import datetime  # Added for timestamps

import tiktoken  # Added import

import prompts
import local_llm  # Added for local LLM processing
import remote_llm  # Added for remote LLM processing

# ------------------ config ------------------
LOCAL_MODEL_TOTAL_CTX_TOKENS = (
    local_llm.CTX
)  # Total context window for the local model in tokens
REMOTE_MODEL_TOTAL_CTX_TOKENS = (
    256000  # Target total context for remote models (e.g., 256k tokens)
)

# Ratio of the total context window to be allocated for the input source code.
# The rest is for prompt instructions and the generated output.
INPUT_CODE_CTX_RATIO = 0.5  # Allocate 50% of total CTX to the input code snippet
# Estimate for average characters per token for source code. This is a heuristic.
# Code can be denser than natural language.
AVG_CHARS_PER_TOKEN_CODE = 3  # e.g., 1 token ~ 3 characters for code

# Default to a reasonable number of workers, os.cpu_count() can be a good starting point
# but let's cap it slightly to avoid overwhelming Ollama by default.
# User can override with OLLAMA_MAX_WORKERS.
CPU_COUNT = os.cpu_count() or 1  # Ensure CPU_COUNT is at least 1
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "5"))
LLM_RETRY_DELAY = int(os.getenv("LLM_RETRY_DELAY", "5"))  # seconds

# --- New exclusion lists definitions ---
DEFAULT_EXCLUDE_DIR_ITEMS_STR = (
    # Common across languages
    ".git,.idea,.vscode,dist,build,out,bin,obj,target,coverage,docs,temp,tmp,"
    # JavaScript/TypeScript ecosystems
    "node_modules,bower_components,jspm_packages,.npm,"
    ".yarn,.pnp,.next,public,shoelace,react,.turbo,storybook-static,"
    # Python
    ".venv,.virtualenv,venv,env,__pycache__,.pytest_cache,.tox,.mypy_cache,*.egg-info,pip-wheel-metadata,"
    ".ipynb_checkpoints,.pytype,.coverage,.eggs,migrations,"
    # Java
    ".gradle,gradle,gradlew,.m2,maven,javadocs,META-INF,"
    # C/C++
    "CMakeFiles,cmake-build*,"
    # C#/.NET
    "packages,Debug,Release,.vs,"
    # Go
    "vendor,"
    # PHP
    "vendor,"
    # Ruby - 'vendor' is general, others are specific subdirs often under vendor
    "bundle,gems,cache,.bundle"
)

# ------------------ helpers ------------------


def get_timestamp():
    """Returns a human-readable timestamp in format: YYYY-MM-DD HH:MM:SS"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_message(message, file=sys.stderr):
    """Print a message with a timestamp prefix"""
    print(f"[{get_timestamp()}] {message}", file=file)


def _resolve_exclusions(env_var_name: str, default_str_value: str) -> set[str]:
    val_from_env_or_default = os.getenv(env_var_name, default_str_value)
    # val_from_env_or_default is now guaranteed to be a string
    return set(filter(None, val_from_env_or_default.replace(" ", "").split(",")))


EXCLUDE_DIR_ITEMS = _resolve_exclusions(
    "README_SYNC_EXCLUDE_DIR_ITEMS", DEFAULT_EXCLUDE_DIR_ITEMS_STR
)

DEFAULT_EXCLUDE_FILE_ITEMS_STR = (
    # Files with extensions from INCLUDE_EXTS that should still be excluded
    "*.min.js,"
    # Test files (common conventions)
    "*.test.js,*.spec.js,*.test.jsx,*.spec.jsx,"
    "*.test.ts,*.spec.ts,*.test.tsx,*.spec.tsx,"
    "*.test.py,*_test.py,"
    "*_test.go,"
    # Generated files (common conventions)
    "*.generated.js,*_generated.py,"
    "*_pb2.py,*_pb2_grpc.py,"
    # Build/config files
    "setup.py"
)
EXCLUDE_FILE_ITEMS = _resolve_exclusions(
    "README_SYNC_EXCLUDE_FILE_ITEMS", DEFAULT_EXCLUDE_FILE_ITEMS_STR
)

INCLUDE_EXTS = {
    "py",  # Python
    "js",
    "jsx",  # JavaScript, JSX (React)
    "ts",
    "tsx",  # TypeScript, TSX (React)
    "c",
    "h",  # C
    "cpp",
    "hpp",
    "cxx",
    "hxx",  # C++
    "java",  # Java
    "cs",  # C#
    "go",  # Go
    "php",  # PHP
    "rb",  # Ruby
}

MARKER_TPL = ("<!-- BEGIN summary: {fname} -->", "<!-- END summary: {fname} -->")
_CACHE: dict[str, str] = {}
_CACHE_LOCK = Lock()
_README_LOCKS: dict[Path, Lock] = {}
_README_LOCKS_ACCESS_LOCK = Lock()  # To protect access to _README_LOCKS dictionary
_TOKEN_ENCODING: tiktoken.Encoding | None = None  # Added for token counting
_TOTAL_TOKEN_COUNT: int = 0  # Added for token counting
_TOKEN_COUNT_LOCK = Lock()  # Added for token counting

# ------------------ helpers ------------------


def is_path_excluded(
    p: Path, exclude_dir_items: set[str], exclude_file_items: set[str]
) -> bool:
    """Checks if a given path should be excluded based on directory and file patterns."""
    # Check against file patterns/names
    for file_item in exclude_file_items:
        if fnmatch.fnmatch(p.name, file_item):
            # log_message(f"DEBUG: Excluding {p} (file item '{file_item}' matches name '{p.name}')")
            return True

    # Check against directory patterns/names in the parent path components
    for part in p.parent.parts:
        if not part or part == p.anchor:  # Skip empty parts or root anchor
            continue
        for dir_item in exclude_dir_items:
            if fnmatch.fnmatch(part, dir_item):
                # log_message(f"DEBUG: Excluding {p} (dir item '{dir_item}' matches part '{part}')")
                return True
    return False


def _get_readme_lock(readme_path: Path) -> Lock:
    """Gets or creates a lock for a specific README file."""
    with _README_LOCKS_ACCESS_LOCK:
        if readme_path not in _README_LOCKS:
            _README_LOCKS[readme_path] = Lock()
        return _README_LOCKS[readme_path]


def _sha1(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()


# ------------------ parsing ------------------


def _ast_extract_py_units(path: Path) -> list[tuple[str, str, str | None]]:
    """Uses Python's AST to extract units (kind, src, name). Name is function/class name or path name for module."""
    src_lines = []
    src_content = ""
    try:
        src_lines = path.read_text().splitlines()
        src_content = "\n".join(src_lines)
        tree = ast.parse(src_content, filename=str(path))
        out: list[tuple[str, str, str | None]] = []
        for n in ast.iter_child_nodes(tree):
            unit_name: str | None = getattr(n, "name", None)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if (
                    n.end_lineno is not None
                    and n.lineno > 0
                    and n.end_lineno >= n.lineno
                ):
                    body_lines = src_lines[n.lineno - 1 : n.end_lineno]
                    out.append(("function", "\n".join(body_lines), unit_name))
                else:
                    print(
                        f"Warning: Invalid line numbers for function {unit_name} in {path}. Skipping symbol.",
                        file=sys.stderr,
                    )
            elif isinstance(n, ast.ClassDef):
                if (
                    n.end_lineno is not None
                    and n.lineno > 0
                    and n.end_lineno >= n.lineno
                ):
                    body_lines = src_lines[n.lineno - 1 : n.end_lineno]
                    out.append(("class", "\n".join(body_lines), unit_name))
                else:
                    print(
                        f"Warning: Invalid line numbers for class {unit_name} in {path}. Skipping symbol.",
                        file=sys.stderr,
                    )

        if out:
            return out
        else:
            stripped_src_lines = []
            for line in src_lines:
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith("#"):
                    stripped_src_lines.append(stripped_line)
            if not stripped_src_lines:
                return [
                    ("empty_or_comment_only_module", src_content, None)
                ]  # Name not strictly needed as blurb uses path.name
            else:
                return [
                    ("module", src_content, path.name)
                ]  # Use file name as module name
    except SyntaxError as e:
        print(
            f"Warning: SyntaxError parsing Python file {path}: {e}. Summarizing file as a whole.",
            file=sys.stderr,
        )
        if not src_content:
            src_content = path.read_text()
        return [("python_syntax_error_file", src_content, path.name)]
    except Exception as e:
        print(
            f"Warning: Unexpected error processing Python file {path} with AST: {e}. Summarizing as whole file.",
            file=sys.stderr,
        )
        if not src_content:
            src_content = path.read_text()
        return [("file", src_content, path.name)]


def _llm_extract_generic_units(
    path: Path, src_content: str, ext: str, llm_mode_choice: str
) -> list[tuple[str, str, str | None]]:
    """Uses LLM to pseudo-parse various languages and extract code units (kind, src, name)."""
    language_name = ext.upper()

    total_model_ctx_tokens = (
        REMOTE_MODEL_TOTAL_CTX_TOKENS
        if llm_mode_choice == "2"
        else LOCAL_MODEL_TOTAL_CTX_TOKENS
    )
    target_input_code_tokens = total_model_ctx_tokens * INPUT_CODE_CTX_RATIO
    approx_input_char_limit = int(target_input_code_tokens * AVG_CHARS_PER_TOKEN_CODE)

    print(
        f"DEBUG_LLM_EXTRACT_UNITS: Attempting LLM-based unit extraction for {path.name} (language: {language_name}). Model CTX: {total_model_ctx_tokens} tokens. Target input code: {target_input_code_tokens:.0f} tokens (~{approx_input_char_limit} chars).",
        file=sys.stderr,
    )

    prompt = prompts.get_llm_extract_generic_units_prompt(
        language_name=language_name,
        file_path_name=path.name,
        ext=ext,
        src_content_snippet=src_content[
            :approx_input_char_limit
        ],  # Slice by approx char limit
    )

    llm_response_str = ""
    if llm_mode_choice == "1":
        llm_response_str = local_llm.llm_call(prompt)
    elif llm_mode_choice == "2":
        try:
            llm_response_str = remote_llm.llm_call_remote(prompt)
        except ValueError as e:  # Catch API key error specifically
            print(
                f"ERROR during remote LLM call in _llm_extract_generic_units: {e}",
                file=sys.stderr,
            )
            # Fallback or error indication
            return [
                ("file", src_content, path.name)
            ]  # Fallback to whole file on API key error
    else:
        print(
            f"Warning: Invalid llm_mode_choice '{llm_mode_choice}' in _llm_extract_generic_units. Defaulting to local.",
            file=sys.stderr,
        )
        llm_response_str = local_llm.llm_call(prompt)

    if llm_response_str.startswith("Error:"):
        print(
            f"Warning: LLM call for {language_name} unit extraction failed for {path.name}: {llm_response_str}. Summarizing file as a whole.",
            file=sys.stderr,
        )
        return [("file", src_content, path.name)]

    # Parse units from text format
    chunks: list[tuple[str, str, str | None]] = []
    units = re.findall(
        r"--UNIT START--\s*UNIT_KIND:\s*([^\n]+)\s*UNIT_NAME:\s*([^\n]+)\s*UNIT_CODE:\s*```[^\n]*\s*(.*?)\s*```\s*--UNIT END--",
        llm_response_str,
        re.DOTALL,
    )

    for kind, name, code in units:
        kind = kind.strip().lower()
        name = name.strip()
        code = code.strip()

        if (
            kind in ["function", "class", "method", "script", "interface"]
            and code.strip()
        ):
            unit_name_to_store = (
                name if name else (path.name if kind == "script" else None)
            )
            chunks.append((kind, code, unit_name_to_store))
        else:
            print(
                f"Warning: Invalid unit structure from LLM for {path.name} ({language_name}): Kind='{kind}', Name='{name}'. Skipping unit.",
                file=sys.stderr,
            )

    if chunks:
        print(
            f"DEBUG_LLM_EXTRACT_UNITS: Successfully extracted {len(chunks)} units for {path.name} ({language_name})",
            file=sys.stderr,
        )
        return chunks
    else:
        print(
            f"Warning: No valid units extracted by LLM for {path.name} ({language_name}) from parsed response. Fallback to whole file.",
            file=sys.stderr,
        )
        return [("file", src_content, path.name)]


def extract_code_units(
    path: Path, ext: str, llm_mode_choice: str
) -> list[tuple[str, str, str | None]]:
    """Dispatcher to extract code units based on file type (kind, src, name)."""
    src_content = ""
    try:
        src_content = path.read_text()
        if not src_content.strip():
            if path.name == "__init__.py" and ext == "py":
                return [("empty_or_comment_only_module", src_content, None)]
            else:
                print(
                    f"DEBUG_EXTRACT_UNITS: File {path.name} is empty. Returning empty chunk list.",
                    file=sys.stderr,
                )
                return [
                    ("empty_file", src_content, None)
                ]  # name is None for generic empty

        # Determine context size and character limits based on LLM mode
        total_model_ctx_tokens = (
            REMOTE_MODEL_TOTAL_CTX_TOKENS
            if llm_mode_choice == "2"
            else LOCAL_MODEL_TOTAL_CTX_TOKENS
        )
        target_input_code_tokens = total_model_ctx_tokens * INPUT_CODE_CTX_RATIO
        approx_input_char_limit_for_snippet = int(
            target_input_code_tokens * AVG_CHARS_PER_TOKEN_CODE
        )

        # MAX_CONTENT_CHUNK_SIZE is the character limit for a chunk before it's split.
        # This should also be derived from the token budget.
        # Ensure MAX_CHUNK_SIZE is at least some reasonable minimum, e.g. 1024 chars.
        MAX_CONTENT_CHUNK_SIZE = max(1024, approx_input_char_limit_for_snippet)

        if len(src_content) > MAX_CONTENT_CHUNK_SIZE:
            print(
                f"DEBUG_EXTRACT_UNITS: File {path.name} ({len(src_content)} chars) exceeds chunk size of {MAX_CONTENT_CHUNK_SIZE} chars (derived from {total_model_ctx_tokens} token model CTX, {INPUT_CODE_CTX_RATIO*100}% for code). Chunking.",
                file=sys.stderr,
            )
            chunks_data: list[tuple[str, str, str | None]] = []
            # Overlap chunks by ~10% of MAX_CONTENT_CHUNK_SIZE
            OVERLAP_SIZE = MAX_CONTENT_CHUNK_SIZE // 10
            num_chunks_approx = (
                len(src_content) + MAX_CONTENT_CHUNK_SIZE - 1
            ) // MAX_CONTENT_CHUNK_SIZE  # Ensure it covers the whole file.

            start_idx = 0
            chunk_num = 0
            while start_idx < len(src_content):
                end_idx = min(len(src_content), start_idx + MAX_CONTENT_CHUNK_SIZE)
                chunk_content = src_content[start_idx:end_idx]
                chunk_name = f"{path.name} (part {chunk_num + 1})"  # Keep track of part number, but not total, as it might adjust.

                chunks_data.append(("file_chunk", chunk_content, chunk_name))
                chunk_num += 1
                start_idx += (
                    MAX_CONTENT_CHUNK_SIZE - OVERLAP_SIZE
                )  # Advance with overlap
                if start_idx >= len(
                    src_content
                ):  # Ensure we don't create an empty chunk at the very end
                    break

            # Update chunk names to include total number of chunks
            total_chunks = len(chunks_data)
            final_chunks_data: list[tuple[str, str, str | None]] = []
            for i, (kind, content, _) in enumerate(chunks_data):
                final_chunks_data.append(
                    (kind, content, f"{path.name} (part {i + 1}/{total_chunks})")
                )

            if final_chunks_data:
                print(
                    f"DEBUG_EXTRACT_UNITS: Chunked {path.name} into {total_chunks} parts.",
                    file=sys.stderr,
                )
                return final_chunks_data
            else:  # Should not happen if src_content was > MAX_CONTENT_CHUNK_SIZE
                print(
                    f"Warning: Chunking logic for {path.name} resulted in no chunks. Fallback to whole file.",
                    file=sys.stderr,
                )
                # Fallthrough to normal processing if chunking somehow failed to produce parts

        if ext == "py":
            return _ast_extract_py_units(path)
        elif ext in (
            "js",
            "jsx",
            "ts",
            "tsx",
            "c",
            "h",
            "cpp",
            "hpp",
            "cxx",
            "hxx",
            "java",
            "cs",
            "go",
            "php",
            "rb",
        ):
            return _llm_extract_generic_units(path, src_content, ext, llm_mode_choice)
        else:
            print(
                f"DEBUG_EXTRACT_UNITS: No specific unit extractor for '.{ext}' file {path.name}. Treating as whole 'file'.",
                file=sys.stderr,
            )
            return [
                ("file", src_content, path.name)
            ]  # Use path.name for 'file' kind name

    except FileNotFoundError:
        print(f"Error: File not found during unit extraction: {path}", file=sys.stderr)
        return []  # Return empty list, which summarise_file handles
    except Exception as e:
        print(
            f"Error: Could not read or process file {path} for unit extraction: {e}",
            file=sys.stderr,
        )
        return [
            ("file", src_content if src_content else "Error reading file.", path.name)
        ]


# ------------------ summarise ------------------


def summarise_file(path: Path, llm_mode_choice: str) -> str:
    ext = path.suffix.lstrip(".")
    chunks = extract_code_units(path, ext, llm_mode_choice)  # Pass llm_mode_choice

    if not chunks:
        log_message(
            f"Warning: No processable chunks found for {path.name}. Returning empty summary."
        )
        return ""  # Or a standard message like "Could not process this file."

    blurbs: list[str] = []

    # Determine context size and character limits based on LLM mode for snippet generation
    total_model_ctx_tokens = (
        REMOTE_MODEL_TOTAL_CTX_TOKENS
        if llm_mode_choice == "2"
        else LOCAL_MODEL_TOTAL_CTX_TOKENS
    )
    target_input_code_tokens = total_model_ctx_tokens * INPUT_CODE_CTX_RATIO
    approx_input_char_limit_for_snippet = int(
        target_input_code_tokens * AVG_CHARS_PER_TOKEN_CODE
    )

    for kind, src, unit_name in chunks:
        h = _sha1(src)
        if h not in _CACHE:
            if kind == "empty_or_comment_only_module" or kind == "empty_file":
                if (
                    path.name == "__init__.py"
                    and kind == "empty_or_comment_only_module"
                ):  # Specific to empty __init__.py from Python AST path
                    _CACHE[h] = (
                        "This `__init__.py` file is empty or contains only comments. "
                        "Its presence makes this directory a Python package, allowing other Python files (modules) "
                        "within this folder to be imported and used elsewhere."
                    )
                elif kind == "empty_file":  # Generic genuinely empty file (any type)
                    _CACHE[h] = f"This file, {path.name}, is empty."
                else:  # Must be empty_or_comment_only_module for a non-__init__.py Python file
                    _CACHE[h] = (
                        "This Python file is empty or contains only comments. "
                        "It does not define any active code."
                    )
                log_message(
                    f"DEBUG_SUMMARISE_FILE: Using standard blurb for {path.name} (kind: {kind})"
                )
            else:  # Handles python_syntax_error_file, module, function, class, file (non-empty cases)
                prompt_text = ""
                name_for_prompt = unit_name if unit_name else path.name
                lang_ext_for_prompt = ext if ext else path.suffix.lstrip(".")
                # Use approx_input_char_limit_for_snippet for slicing the snippet
                src_snippet = src[
                    :approx_input_char_limit_for_snippet
                ]  # Ensure snippet respects the calculated char limit

                if kind == "python_syntax_error_file":
                    prompt_text = prompts.get_python_syntax_error_prompt(
                        name_for_prompt=name_for_prompt,
                        lang_ext_for_prompt=lang_ext_for_prompt,
                        src_snippet=src_snippet,
                    )
                elif lang_ext_for_prompt == "py" and kind == "module":
                    prompt_text = prompts.get_python_module_prompt(
                        kind=kind,
                        name_for_prompt=name_for_prompt,
                        lang_ext_for_prompt=lang_ext_for_prompt,
                        src_snippet=src_snippet,
                    )
                elif lang_ext_for_prompt == "py" and kind == "class":
                    prompt_text = prompts.get_python_class_prompt(
                        kind=kind,
                        name_for_prompt=name_for_prompt,
                        lang_ext_for_prompt=lang_ext_for_prompt,
                        src_snippet=src_snippet,
                    )
                elif lang_ext_for_prompt == "py" and kind == "function":
                    prompt_text = prompts.get_python_function_prompt(
                        kind=kind,
                        name_for_prompt=name_for_prompt,
                        lang_ext_for_prompt=lang_ext_for_prompt,
                        src_snippet=src_snippet,
                    )
                elif kind in (
                    "function",
                    "class",
                    "method",
                    "interface",
                    "script",
                ):  # Generic units from LLM extraction
                    prompt_text = prompts.get_generic_unit_prompt(
                        lang_ext_for_prompt=lang_ext_for_prompt,
                        kind=kind,
                        name_for_prompt=name_for_prompt,
                        src_snippet=src_snippet,
                    )
                elif kind == "file_chunk":  # Handle summaries for parts of large files
                    prompt_text = prompts.get_file_chunk_prompt(
                        file_path_name=path.name,  # Original full path name
                        name_for_prompt=name_for_prompt,  # Chunk name like "file.py (part 1/3)"
                        lang_ext_for_prompt=lang_ext_for_prompt,
                        src_snippet=src_snippet,
                    )
                else:  # Default for 'file' kind (whole-file summaries for non-parsed languages)
                    prompt_text = prompts.get_default_file_summary_prompt(
                        name_for_prompt=name_for_prompt,
                        lang_ext_for_prompt=lang_ext_for_prompt,
                        src_snippet=src_snippet,
                    )

                llm_response_str = ""
                if llm_mode_choice == "1":
                    llm_response_str = local_llm.llm_call(prompt_text, str(path))
                elif llm_mode_choice == "2":
                    try:
                        llm_response_str = remote_llm.llm_call_remote(
                            prompt_text, None, str(path)
                        )
                    except ValueError as e:  # Catch API key error
                        print(
                            f"ERROR during remote LLM call in summarise_file (unit summary): {e}",
                            file=sys.stderr,
                        )
                        return f"Error: Could not summarize unit due to remote LLM configuration: {e}"
                else:
                    print(
                        f"Warning: Invalid llm_mode_choice '{llm_mode_choice}' in summarise_file (unit). Defaulting to local.",
                        file=sys.stderr,
                    )
                    llm_response_str = local_llm.llm_call(prompt_text, str(path))

                # Use the raw text response as the blurb, no JSON parsing
                text_blurb_for_rollup = llm_response_str

                # Log the start of the raw blurb for debugging
                raw_blurb_snippet_log = (
                    text_blurb_for_rollup[:100].replace("\n", " ").replace("'", "\\'")
                )
                print(
                    f"DEBUG_SUMMARISE_FILE: Using raw LLM text response as blurb for {path.name} ({name_for_prompt}). Blurb starts: '{raw_blurb_snippet_log}...'",
                    file=sys.stderr,
                )

                _CACHE[h] = text_blurb_for_rollup
        blurbs.append(_CACHE[h])

    if not blurbs:
        print(
            f"Warning: No blurbs generated for {path.name} prior to rollup. Returning empty summary.",
            file=sys.stderr,
        )
        return ""

    if len(chunks) == 1 and chunks[0][0] == "empty_or_comment_only_module":
        final_summary = blurbs[0]
        cleaned_final_summary_snippet = (
            final_summary[:100].replace("\n", " ").replace("'", "\\'")
        )
        print(
            f"DEBUG_SUMMARISE_FILE: For {path.name} (single empty/comment-only chunk), using standard blurb as final summary: '{cleaned_final_summary_snippet}...'",
            file=sys.stderr,
        )
    else:
        # Refined rollup prompt to guide structure and avoid echoing instructions
        rollup_prompt_instructions = (
            "You are a senior software architect. Your sole task is to create a technical overview of a single software file. "
            "You will be given a set of detailed explanations, where each explanation describes a specific part (e.g., a function or class) of that single software file. "
            "Your overview MUST be based **exclusively** on these provided explanations. Do NOT add any information, functionality, or concepts not present in these explanations. Do not infer relationships or purposes beyond what the explanations explicitly state.\\n\\n"
            "IMPORTANT: If the provided explanations are so minimal that you cannot extract any meaningful information about the file's responsibility or components, respond with ONLY the following sentence: 'The provided explanations are insufficient to generate a technical overview.'\\n\\n"
            "Otherwise, use the following structure in your response. Only include the headers shown below if you have content for that section:\\n\\n"
            "PRIMARY TECHNICAL RESPONSIBILITY:\\n"
            "[Provide the one or two-sentence statement of the file's primary technical responsibility here, synthesized strictly from the explanations.]\\n\\n"
            "KEY TECHNICAL COMPONENTS:\\n"
            "[Provide up to 5-7 bullet points summarizing the key technical components mentioned in the explanations and their specific engineering roles or functionalities as described. Only include interactions or dependencies if they are explicitly mentioned. Start each bullet with a hyphen (-).]\\n\\n"
            "IMPORTANT: DO NOT include any of these instructions or explanatory text in your response. Your response should ONLY contain either the insufficient explanations message OR the formatted sections as described above."
        )

        rollup = prompts.get_rollup_prompt(blurbs)
        final_summary = ""
        if llm_mode_choice == "1":
            final_summary = local_llm.llm_call(rollup, str(path))
        elif llm_mode_choice == "2":
            try:
                final_summary = remote_llm.llm_call_remote(rollup, None, str(path))
            except ValueError as e:  # Catch API key error
                print(
                    f"ERROR during remote LLM call in summarise_file (rollup): {e}",
                    file=sys.stderr,
                )
                return f"Error: Could not generate rollup summary due to remote LLM configuration: {e}"
        else:
            print(
                f"Warning: Invalid llm_mode_choice '{llm_mode_choice}' in summarise_file (rollup). Defaulting to local.",
                file=sys.stderr,
            )
            final_summary = local_llm.llm_call(rollup, str(path))

        summary_snippet = final_summary[:100].replace("\n", " ").replace("'", "\\' ")
        print(
            f"DEBUG_SUMMARISE_FILE: For path {path.name}, generated final summary via rollup: '{summary_snippet}...'",
            file=sys.stderr,
        )

        # Add retry mechanism for larger files with insufficient explanations
        if (
            final_summary.strip()
            == "The provided explanations are insufficient to generate a technical overview."
        ):
            # Check if file is large enough to warrant retry (adjust threshold as needed)
            file_size = path.stat().st_size
            # Set minimum size to 1KB for retry - adjust as needed
            MIN_SIZE_FOR_RETRY = 1024

            if file_size > MIN_SIZE_FOR_RETRY:
                print(
                    f"DEBUG_SUMMARISE_FILE: Detected 'insufficient explanations' for larger file ({path.name}, size: {file_size} bytes). Attempting retry with whole file approach.",
                    file=sys.stderr,
                )

                # Read the file content (with reasonable limit)
                try:
                    file_content = path.read_text()[
                        :25000
                    ]  # Limit to avoid token issues

                    # Create a direct prompt for the whole file
                    # For retry, we also need to respect token limits for the input snippet.
                    # The prompt itself will consume some tokens.
                    retry_total_model_ctx_tokens = (
                        REMOTE_MODEL_TOTAL_CTX_TOKENS
                        if llm_mode_choice == "2"
                        else LOCAL_MODEL_TOTAL_CTX_TOKENS
                    )
                    retry_target_input_code_tokens = (
                        retry_total_model_ctx_tokens * INPUT_CODE_CTX_RATIO
                    )  # Can use same ratio or a specific one for retry
                    retry_approx_input_char_limit = int(
                        retry_target_input_code_tokens * AVG_CHARS_PER_TOKEN_CODE
                    )

                    direct_prompt = prompts.get_direct_summary_retry_prompt(
                        file_path_name=path.name,
                        ext=ext,
                        file_content_snippet=file_content[
                            :retry_approx_input_char_limit
                        ],
                    )

                    # Try direct approach
                    retry_summary = ""
                    if llm_mode_choice == "1":
                        retry_summary = local_llm.llm_call(direct_prompt, str(path))
                    elif llm_mode_choice == "2":
                        try:
                            retry_summary = remote_llm.llm_call_remote(
                                direct_prompt, None, str(path)
                            )
                        except ValueError as e:  # Catch API key error
                            print(
                                f"ERROR during remote LLM call in summarise_file (retry summary): {e}",
                                file=sys.stderr,
                            )
                            # Let the original "insufficient explanations" stand if retry fails due to config
                            pass  # Keep original final_summary
                    else:
                        print(
                            f"Warning: Invalid llm_mode_choice '{llm_mode_choice}' in summarise_file (retry). Defaulting to local.",
                            file=sys.stderr,
                        )
                        retry_summary = local_llm.llm_call(direct_prompt, str(path))

                    # Check if we got a better result
                    if (
                        retry_summary
                        and not retry_summary.strip()
                        == "The provided explanations are insufficient to generate a technical overview."
                    ):
                        print(
                            f"DEBUG_SUMMARISE_FILE: Retry successful for {path.name}. Using direct approach summary.",
                            file=sys.stderr,
                        )
                        final_summary = retry_summary
                    else:
                        print(
                            f"DEBUG_SUMMARISE_FILE: Retry also failed for {path.name}. Keeping original 'insufficient explanations' message.",
                            file=sys.stderr,
                        )
                except Exception as e:
                    print(
                        f"DEBUG_SUMMARISE_FILE: Retry attempt failed for {path.name}: {e}",
                        file=sys.stderr,
                    )

    return final_summary


# ------------------ README injection ------------------


def _get_summarized_fnames_from_readme(readme_content: str) -> list[str]:
    """Parses README content to find all filenames for which summaries exist."""
    # MARKER_TPL = ("<!-- BEGIN summary: {fname} -->", "<!-- END summary: {fname} -->")
    # Regex to find: <!-- BEGIN summary:
    # then capture: anything for fname
    # then find: -->
    # This avoids issues if {fname} in MARKER_TPL[0] has regex special chars.
    begin_marker_prefix = MARKER_TPL[0].split("{fname}")[0]
    begin_marker_suffix = MARKER_TPL[0].split("{fname}")[1]

    pattern = re.compile(
        re.escape(begin_marker_prefix) + r"(.+?)" + re.escape(begin_marker_suffix),
        re.S,
    )
    return pattern.findall(readme_content)


def _remove_summary_from_readme(readme_content: str, fname_to_remove: str) -> str:
    """Removes the summary block for a given filename from README content."""
    start_marker, end_marker = (tpl.format(fname=fname_to_remove) for tpl in MARKER_TPL)
    pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.S)
    # Replace the found pattern (including markers) with an empty string.
    # Add a newline to avoid multiple empty lines if the summary was at the end.
    new_content, num_subs = pattern.subn("", readme_content)
    if num_subs > 0:
        # Clean up potential excess newlines that might result from removal
        new_content = re.sub(r"\\n{3,}", "\\n\\n", new_content).strip()
    return new_content


def _inject(readme: Path, fname: str, md: str) -> None:
    start, end = (t.format(fname=fname) for t in MARKER_TPL)
    md_snippet = md[:50].replace("\n", " ").replace("'", "\\'")  # Clean for printing
    print(
        f"DEBUG_INJECT: Called for readme='{readme}', fname='{fname}'. Summary starts: '{md_snippet}...'",
        file=sys.stderr,
    )
    body = ""
    try:
        body = readme.read_text() if readme.exists() else ""
        print(
            f"DEBUG_INJECT: Read existing body length: {len(body)} for {readme}",
            file=sys.stderr,
        )
    except Exception as e:
        print(f"ERROR_INJECT: Failed to read {readme}: {e}", file=sys.stderr)
        # Decide if we should proceed with an empty body or just return
        body = ""  # Proceed with empty, will try to create/append

    pattern = re.compile(re.escape(start) + ".*?" + re.escape(end), re.S)
    repl = f"{start}\n## {fname}\n\n{md}\n{end}"

    new_body = ""
    if pattern.search(body):
        print(
            f"DEBUG_INJECT: Found existing summary for {fname} in {readme}. Replacing.",
            file=sys.stderr,
        )
        new_body = pattern.sub(repl, body)
    else:
        print(
            f"DEBUG_INJECT: No existing summary for {fname} in {readme}. Appending.",
            file=sys.stderr,
        )
        new_body = (
            body + ("\n\n" if body else "") + repl
        )  # Ensure newline separator if body exists

    print(
        f"DEBUG_INJECT: Attempting to write new body length: {len(new_body)} to {readme}",
        file=sys.stderr,
    )
    try:
        readme.write_text(new_body)
        print(f"DEBUG_INJECT: Successfully wrote to {readme}", file=sys.stderr)
    except Exception as e:
        print(f"ERROR_INJECT: Failed to write to {readme}: {e}", file=sys.stderr)


def process_paths(
    paths: Iterable[Path], root: Path, non_interactive: bool, llm_mode: str | None
) -> None:
    # Determine unique directories that might contain READMEs needing cleanup/updates.
    global _TOKEN_ENCODING
    global _TOTAL_TOKEN_COUNT
    global _TOKEN_COUNT_LOCK

    if _TOKEN_ENCODING is None:
        try:
            _TOKEN_ENCODING = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            log_message(
                f"Warning: Could not initialize tiktoken encoding. Token counting will be skipped. Error: {e}"
            )
            _TOKEN_ENCODING = None

    readme_dirs_to_check: set[Path] = set()
    valid_paths_for_summarization: list[Path] = []

    # First, filter paths, count tokens for eligible files, and identify directories for cleanup/summarization
    log_message(f"Scanning {len(list(paths))} initial paths provided.")
    for p in paths:  # This paths argument is the initial list of files/dirs from CLI
        if p.is_file() and p.suffix[1:] in INCLUDE_EXTS:
            if is_path_excluded(p, EXCLUDE_DIR_ITEMS, EXCLUDE_FILE_ITEMS):
                # log_message(f"DEBUG: Skipping excluded path (in process_paths initial loop): {p}")
                continue

            # If not excluded, count tokens
            if _TOKEN_ENCODING:
                try:
                    content = p.read_text(encoding="utf-8", errors="ignore")
                    token_count = len(
                        _TOKEN_ENCODING.encode(content, disallowed_special=())
                    )
                    with _TOKEN_COUNT_LOCK:
                        _TOTAL_TOKEN_COUNT += token_count
                    log_message(f"Tokens for {p}: {token_count}")
                except Exception as e:
                    log_message(f"Warning: Could not count tokens for {p}. Error: {e}")

            valid_paths_for_summarization.append(p)
            if p.parent.is_dir():
                readme_dirs_to_check.add(p.parent)
        elif (
            p.is_dir()
        ):  # If a directory is given, recursively find eligible files within it
            log_message(f"Scanning directory: {p}")
            for sub_p in p.rglob("*"):
                if sub_p.is_file() and sub_p.suffix[1:] in INCLUDE_EXTS:
                    if is_path_excluded(sub_p, EXCLUDE_DIR_ITEMS, EXCLUDE_FILE_ITEMS):
                        # log_message(f"DEBUG: Skipping excluded path (in process_paths rglob): {sub_p}")
                        continue

                    if _TOKEN_ENCODING:
                        try:
                            content = sub_p.read_text(encoding="utf-8", errors="ignore")
                            token_count = len(
                                _TOKEN_ENCODING.encode(content, disallowed_special=())
                            )
                            with _TOKEN_COUNT_LOCK:
                                _TOTAL_TOKEN_COUNT += token_count
                            log_message(f"Tokens for {sub_p}: {token_count}")
                        except Exception as e:
                            log_message(
                                f"Warning: Could not count tokens for {sub_p}. Error: {e}"
                            )

                    valid_paths_for_summarization.append(sub_p)
                    if sub_p.parent.is_dir():
                        readme_dirs_to_check.add(sub_p.parent)

    # Deduplicate valid_paths_for_summarization, as rglob might find files multiple times if symlinks or overlapping paths are given
    valid_paths_for_summarization = sorted(list(set(valid_paths_for_summarization)))
    log_message(
        f"Found {len(valid_paths_for_summarization)} unique, non-excluded files for potential processing."
    )

    # --- Sequential Cleanup Phase for READMEs that might have stale entries ---
    # This cleanup should happen based on directories that *could* have READMEs
    # It's done before summarization to ensure we don't try to update a README that has stale entries from deleted files.
    log_message(
        f"Starting pre-summarization cleanup for READMEs in {len(readme_dirs_to_check)} directories."
    )
    for readme_dir in readme_dirs_to_check:
        readme_path = readme_dir / "README.md"
        if readme_path.exists() and readme_path.is_file():
            try:
                current_content = readme_path.read_text(encoding="utf-8")
                original_content = current_content  # Keep a copy for comparison

                summarized_fnames_in_readme = _get_summarized_fnames_from_readme(
                    current_content
                )

                # Files that actually exist in this directory and are eligible
                actual_fnames_in_dir_and_valid = {
                    f.name
                    for f in valid_paths_for_summarization
                    if f.parent == readme_dir
                }

                fnames_to_remove_summary_for = [
                    fn
                    for fn in summarized_fnames_in_readme
                    if fn not in actual_fnames_in_dir_and_valid
                ]

                if fnames_to_remove_summary_for:
                    log_message(
                        f"Pre-cleanup for {readme_path}: Removing summaries for {fnames_to_remove_summary_for}"
                    )
                    modified_readme_content = current_content
                    for fname_to_remove in fnames_to_remove_summary_for:
                        modified_readme_content = _remove_summary_from_readme(
                            modified_readme_content, fname_to_remove
                        )

                    if modified_readme_content != original_content:
                        readme_lock = _get_readme_lock(readme_path)
                        with readme_lock:
                            readme_path.write_text(
                                modified_readme_content, encoding="utf-8"
                            )
            except Exception as e:
                log_message(
                    f"Error during pre-summarization cleanup of {readme_path}: {e}"
                )

    # --- Parallel Summarization and Injection Phase ---
    if not valid_paths_for_summarization:
        log_message("No valid files found for summarization.")
        if (
            _TOKEN_ENCODING
        ):  # Still print token count if any were counted and we are exiting early
            log_message(
                f"\nEstimated total tokens for all scanned files: {_TOTAL_TOKEN_COUNT}"
            )
        return

    # First, list the files
    log_message("\nThe following files are queued for LLM summarization:")
    for i, f_path in enumerate(valid_paths_for_summarization):
        log_message(f"  [{i+1}/{len(valid_paths_for_summarization)}] {f_path}")

    # Then, print cumulative total token count
    if _TOKEN_ENCODING:
        log_message(
            f"\nTotal estimated tokens for these {len(valid_paths_for_summarization)} files: {_TOTAL_TOKEN_COUNT}"
        )

    # Finally, ask for Y/N Confirmation Prompt
    if non_interactive:
        proceed = "y"
        log_message("Non-interactive mode: Defaulting to proceed with summarization.")
    else:
        proceed = input("\nProceed with LLM summarization? (Y/N): ").strip().lower()

    if proceed != "y":
        log_message("LLM summarization aborted by user.")
        return  # Exit process_paths function

    # Determine LLM mode choice
    if non_interactive:
        if llm_mode == "local":
            llm_mode_choice = "1"
            log_message("Non-interactive mode: Using LLM mode 'local' as specified.")
        elif llm_mode == "remote":
            llm_mode_choice = "2"
            log_message("Non-interactive mode: Using LLM mode 'remote' as specified.")
        else:  # llm_mode is None or an unexpected value, default to remote for non-interactive
            llm_mode_choice = "2"
            log_message("Non-interactive mode: Defaulting to LLM mode 'remote'.")
    else:
        llm_choice_prompt = (
            "\nChoose LLM processing mode:\n"
            "1. Local (runs on your machine, can be slower)\n"
            "2. Remote (uses Together AI API, faster, requires TOGETHER_API_KEY, may have costs)\n"
            "Enter choice (1 or 2): "
        )
        llm_mode_choice = input(llm_choice_prompt).strip()

    # Validate and set up based on llm_mode_choice (common for both interactive and non-interactive)
    if llm_mode_choice == "1":
        log_message("Local LLM mode selected.")
        DEFAULT_MAX_WORKERS_ACTUAL = 2
        MAX_WORKERS = int(
            os.getenv("LOCAL_MAX_WORKERS", str(DEFAULT_MAX_WORKERS_ACTUAL))
        )
    elif llm_mode_choice == "2":
        log_message("Remote LLM mode (Together AI) selected.")
        if not remote_llm.TOGETHER_API_KEY:
            log_message(
                "ERROR: Remote LLM mode selected, but TOGETHER_API_KEY environment variable is not set."
            )
            log_message(
                "Please set TOGETHER_API_KEY or choose local mode (if interactive) or ensure key is in environment (if non-interactive)."
            )
            return  # Abort if API key is missing for remote mode
        DEFAULT_MAX_WORKERS_ACTUAL = (
            6  # Increased from 4 to 6 for better performance with remote LLM
        )
        MAX_WORKERS = int(
            os.getenv("REMOTE_MAX_WORKERS", str(DEFAULT_MAX_WORKERS_ACTUAL))
        )
    else:
        log_message("Invalid choice. Defaulting to Local LLM mode.")
        llm_mode_choice = "1"  # Default to local if input is invalid
        DEFAULT_MAX_WORKERS_ACTUAL = 2  # Default to local's default
        MAX_WORKERS = int(
            os.getenv("LOCAL_MAX_WORKERS", str(DEFAULT_MAX_WORKERS_ACTUAL))
        )

    log_message(
        f"Starting summarization for {len(valid_paths_for_summarization)} files using up to {MAX_WORKERS} workers (mode: {llm_mode_choice})..."
    )

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        if llm_mode_choice == "1" and MAX_WORKERS > 0:
            log_message("Attempting to preload local model...")
            preload_future = executor.submit(local_llm.preload_model)
            try:
                if preload_future.result(
                    timeout=local_llm.LLM_FIRST_ATTEMPT_TIMEOUT + 10
                ):
                    log_message(
                        "Local model preloaded successfully or was already loaded."
                    )
                else:
                    log_message(
                        "Local model preloading failed or indicated model was not ready."
                    )
            except Exception as e:
                log_message(f"Error during local model preloading: {e}")
        elif llm_mode_choice == "2" and MAX_WORKERS > 0:
            log_message(
                "Remote LLM mode selected. Preloading is not applicable for remote APIs."
            )

        if MAX_WORKERS <= 0:
            log_message(
                f"MAX_WORKERS is {MAX_WORKERS}, running summarizations sequentially."
            )
            for path_to_process in valid_paths_for_summarization:
                try:
                    log_message(
                        f"Processing (sequentially, mode: {llm_mode_choice}): {path_to_process}"
                    )
                    md_summary = summarise_file(path_to_process, llm_mode_choice)
                    if md_summary and not md_summary.startswith("Error:"):
                        readme_file_path = path_to_process.parent / "README.md"
                        readme_lock = _get_readme_lock(readme_file_path)
                        with readme_lock:
                            _inject(readme_file_path, path_to_process.name, md_summary)
                        log_message(
                            f"Updated (sequentially): {readme_file_path} for {path_to_process.name}"
                        )
                        log_message(
                            f"************************* Completed processing: {path_to_process} *************************"
                        )
                    elif md_summary:  # Error occurred
                        log_message(
                            f"Skipping injection for {path_to_process.name} due to summarization error: {md_summary[:100]}..."
                        )
                        log_message(
                            f"************************* Failed processing: {path_to_process} *************************"
                        )
                    else:  # No summary
                        log_message(
                            f"Warning: No summary generated for {path_to_process.name}"
                        )
                        log_message(
                            f"************************* Failed processing: {path_to_process} *************************"
                        )
                except Exception as exc:
                    log_message(
                        f"Error processing {path_to_process} sequentially: {exc}"
                    )
                    log_message(
                        f"************************* Failed processing: {path_to_process} *************************"
                    )
            if _TOKEN_ENCODING:
                log_message(
                    f"\nEstimated total tokens for all scanned files: {_TOTAL_TOKEN_COUNT}"
                )
                log_message(
                    f"Estimated total tokens for all scanned files (completed run): {_TOTAL_TOKEN_COUNT}"
                )
            return

        # Submit summarization tasks for parallel execution based on mode
        log_message(
            f"Submitting tasks for LLM processing in mode: {llm_mode_choice}..."
        )
        future_to_path = {
            executor.submit(summarise_file, p, llm_mode_choice): p
            for p in valid_paths_for_summarization
        }

        processed_count = 0
        for future in as_completed(future_to_path):
            path_processed = future_to_path[future]
            try:
                md_summary = future.result()
                if md_summary and not md_summary.startswith("Error:"):
                    readme_file_path = path_processed.parent / "README.md"
                    readme_lock = _get_readme_lock(readme_file_path)
                    with readme_lock:
                        _inject(readme_file_path, path_processed.name, md_summary)
                    log_message(
                        f"Successfully updated {readme_file_path} for {path_processed.name}"
                    )
                    log_message(
                        f"************************* Completed processing: {path_processed} *************************"
                    )
                elif md_summary:  # Error occurred during summarization
                    log_message(
                        f"Skipping injection for {path_processed.name} due to summarization error: {md_summary[:100]}..."
                    )
                    log_message(
                        f"************************* Failed processing: {path_processed} *************************"
                    )
                else:  # No summary generated
                    log_message(
                        f"Warning: No summary generated (empty) for {path_processed.name}"
                    )
                    log_message(
                        f"************************* Failed processing: {path_processed} *************************"
                    )
            except Exception as exc:
                log_message(
                    f"File {path_processed.name} generated an exception during its task processing: {exc}"
                )
            processed_count += 1
            log_message(
                f"Completed processing ({processed_count}/{len(valid_paths_for_summarization)}): {path_processed.name}"
            )
            # Add separator line after each file is processed
            log_message(
                f"************************* Completed processing: {path_processed} *************************"
            )

    log_message(f"Finished processing all {len(valid_paths_for_summarization)} files.")

    # After all files are processed (summarized and injected), print the total token count
    if _TOKEN_ENCODING:
        log_message(
            f"\nEstimated total tokens for all scanned files: {_TOTAL_TOKEN_COUNT}"
        )
        log_message(
            f"Estimated total tokens for all scanned files (completed run): {_TOTAL_TOKEN_COUNT}"
        )

    # Note: The extensive cleanup logic that was previously at the very end seems to be covered
    # by the pre-summarization cleanup and the nature of _inject (which overwrites or appends).
    # If a more aggressive "remove summaries for files no longer in valid_paths_for_summarization AT ALL"
    # is needed, that would be a separate loop over all known READMEs.
    # The current pre-summarization cleanup handles files that are no longer valid *within their specific directory's README*.


def process_single_file(file_path: Path, llm_mode: str) -> bool:
    """
    Process a single file's README.md summary without any interactive prompts or directory scanning.
    Designed for efficient use in Git hooks or CI/CD pipelines.

    Args:
        file_path: Path to the single file to process
        llm_mode: "local" or "remote" for LLM processing

    Returns:
        bool: True if successful, False otherwise
    """
    if not file_path.exists() or not file_path.is_file():
        log_message(f"Error: File {file_path} does not exist or is not a file.")
        return False

    ext = file_path.suffix.lstrip(".")
    if ext not in INCLUDE_EXTS:
        log_message(f"Skipping file with unsupported extension: {file_path}")
        return False

    if is_path_excluded(file_path, EXCLUDE_DIR_ITEMS, EXCLUDE_FILE_ITEMS):
        log_message(f"Skipping excluded file: {file_path}")
        return False

    # Convert llm_mode string to the numeric choice expected by summarise_file
    llm_mode_choice = "1" if llm_mode == "local" else "2"

    try:
        log_message(f"Processing single file: {file_path}")
        md_summary = summarise_file(file_path, llm_mode_choice)

        if md_summary and not md_summary.startswith("Error:"):
            readme_file_path = file_path.parent / "README.md"
            readme_lock = _get_readme_lock(readme_file_path)
            with readme_lock:
                _inject(readme_file_path, file_path.name, md_summary)
            log_message(f"Successfully updated {readme_file_path} for {file_path.name}")
            log_message(
                f"************************* Completed processing: {file_path} *************************"
            )
            return True
        elif md_summary:  # Error occurred
            log_message(f"Error summarizing {file_path.name}: {md_summary[:100]}...")
            log_message(
                f"************************* Failed processing: {file_path} *************************"
            )
            return False
        else:  # No summary
            log_message(f"No summary generated for {file_path.name}")
            log_message(
                f"************************* Failed processing: {file_path} *************************"
            )
            return False
    except Exception as e:
        log_message(f"Error processing {file_path}: {e}")
        return False


def main(argv=None):
    ap = argparse.ArgumentParser("readme-sync CLI")
    ap.add_argument(
        "--root", default=".", help="Root directory of the codebase to scan."
    )
    ap.add_argument(
        "paths",
        nargs="*",
        help="Specific file paths to process. If not provided, scans --root.",
    )
    ap.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run in non-interactive mode, defaulting to proceed and specified/default LLM mode.",
    )
    ap.add_argument(
        "--llm-mode",
        choices=["local", "remote"],
        default=None,  # Default to None, so we can check if it was explicitly set
        help="Specify LLM mode ('local' or 'remote'). Used with --non-interactive. Defaults to 'remote' if --non-interactive is set and this is not.",
    )
    ap.add_argument(
        "--single-file-mode",
        action="store_true",
        help="Process files individually with optimized path for post-commit hooks. Implies --non-interactive.",
    )
    ns = ap.parse_args(argv)

    # If single-file-mode is used, force non-interactive mode
    if ns.single_file_mode:
        ns.non_interactive = True

    root_path = Path(ns.root).resolve()

    if not root_path.is_dir():
        log_message(
            f"Error: Root path {root_path} is not a directory or does not exist."
        )
        return

    # Set default LLM mode if not specified (prefer remote for non-interactive)
    if ns.llm_mode is None:
        ns.llm_mode = "remote" if ns.non_interactive else "local"

    if ns.single_file_mode:
        if not ns.paths:
            log_message("Error: --single-file-mode requires specifying file paths.")
            return

        success_count = 0
        for file_path_str in ns.paths:
            file_path = Path(file_path_str).resolve()
            if process_single_file(file_path, ns.llm_mode):
                success_count += 1

        log_message(
            f"Processed {success_count}/{len(ns.paths)} files in single-file mode"
        )
        return

    # Original code path for regular (non-single-file) mode
    log_message(f"DEBUG: Excluding directory items: {EXCLUDE_DIR_ITEMS}")
    log_message(f"DEBUG: Excluding file items: {EXCLUDE_FILE_ITEMS}")

    files_to_process = []
    if ns.paths:  # User specified specific paths
        for p_str in ns.paths:
            p = Path(p_str).resolve()

            if p.is_file():
                file_ext = p.suffix.lstrip(".")
                if file_ext in INCLUDE_EXTS:
                    if is_path_excluded(p, EXCLUDE_DIR_ITEMS, EXCLUDE_FILE_ITEMS):
                        log_message(
                            f"DEBUG: Skipping excluded specified file path: {p}"
                        )
                        continue
                    files_to_process.append(p)
                else:
                    log_message(
                        f"DEBUG: Skipping (due to extension not in INCLUDE_EXTS): {p}"
                    )

            elif p.is_dir():
                log_message(f"Scanning specified directory: {p}")
                is_dir_itself_excluded = False
                for (
                    dir_item
                ) in (
                    EXCLUDE_DIR_ITEMS
                ):  # Check if the directory *name* itself is an exclusion pattern
                    if fnmatch.fnmatch(p.name, dir_item):
                        is_dir_itself_excluded = True
                        break
                if is_dir_itself_excluded:
                    log_message(
                        f"DEBUG: Skipping directory scan (directory name '{p.name}' matches exclude pattern): {p}"
                    )
                    continue

                for sub_p in p.rglob("*"):
                    if sub_p.is_file():
                        file_ext = sub_p.suffix.lstrip(".")
                        if file_ext in INCLUDE_EXTS:
                            if is_path_excluded(
                                sub_p, EXCLUDE_DIR_ITEMS, EXCLUDE_FILE_ITEMS
                            ):
                                # log_message(f"DEBUG: Skipping excluded path in specified directory scan: {sub_p}")
                                continue
                            files_to_process.append(sub_p)
                        else:
                            log_message(
                                f"DEBUG: Skipping (from dir scan, extension not in INCLUDE_EXTS): {sub_p}"
                            )
            else:
                log_message(
                    f"Warning: Specified path {p_str} is not a valid file or directory. Skipping."
                )

        files_to_process = sorted(list(set(files_to_process)))  # Remove duplicates
    else:  # No specific paths, scan the root directory
        log_message(f"Scanning root directory for files: {root_path}")
        temp_files = []
        for p in root_path.rglob("*"):
            if p.is_file():
                file_ext = p.suffix.lstrip(".")
                if file_ext in INCLUDE_EXTS:
                    if is_path_excluded(p, EXCLUDE_DIR_ITEMS, EXCLUDE_FILE_ITEMS):
                        # log_message(f"DEBUG: Skipping excluded path in root scan: {p}")
                        continue
                    temp_files.append(p)
                else:
                    log_message(f"DEBUG: Skipping (extension not in INCLUDE_EXTS): {p}")
        files_to_process = sorted(temp_files)

    if not files_to_process:
        log_message(
            f"No files found to process in {root_path} (or specified paths based on INCLUDE_EXTS: {INCLUDE_EXTS})."
        )
        return

    log_message(f"Found {len(files_to_process)} files to process in total.")
    for f_idx, f_path in enumerate(files_to_process):
        log_message(f"  [{f_idx+1}/{len(files_to_process)}] {f_path}")

    process_paths(files_to_process, root_path, ns.non_interactive, ns.llm_mode)


if __name__ == "__main__":
    main()
