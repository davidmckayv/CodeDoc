"""Local LLM (Ollama) interaction module."""

import os
import sys
import time
import threading
import random

import httpx

# ------------------ config ------------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_TAG = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b")
CTX = int(os.getenv("OLLAMA_CTX", "32768"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "5"))
LLM_RETRY_DELAY = int(os.getenv("LLM_RETRY_DELAY", "5"))  # seconds
# Set longer client timeout to handle model loading
LLM_FIRST_ATTEMPT_TIMEOUT = float(
    os.getenv("LLM_FIRST_ATTEMPT_TIMEOUT", "600.0")
)  # 10 minutes
LLM_CLIENT_TIMEOUT = float(os.getenv("LLM_CLIENT_TIMEOUT", "300.0"))  # 5 minutes
# Simple prompt to use for preloading model
LLM_PRELOAD_PROMPT = os.getenv("LLM_PRELOAD_PROMPT", "Hello, world!")

_CACHE: dict[str, str] = {}
_CACHE_LOCK = threading.Lock()


# ------------------ helpers ------------------
def llm_call(prompt: str) -> str:
    """Blocking call to local Ollama via httpx, with thread-safe caching and retries."""
    with _CACHE_LOCK:
        if prompt in _CACHE:
            return _CACHE[prompt]

    payload = {
        "model": MODEL_TAG,
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": CTX},
    }
    response_text = "Error: Max retries reached for Ollama call."
    last_error: Exception | None = (
        None  # Store the most recent error for backoff calculation
    )

    for attempt in range(LLM_MAX_RETRIES):
        try:
            prompt_snippet = prompt[:50].replace("\n", " ").replace("'", "\\'")
            thread_id = threading.get_ident()
            print(
                f"[Thread-{thread_id}] DEBUG_LLM: Attempt {attempt + 1}/{LLM_MAX_RETRIES} for prompt starting with '{prompt_snippet}...'",
                file=sys.stderr,
            )

            # Use longer timeout to handle model loading
            timeout = LLM_FIRST_ATTEMPT_TIMEOUT if attempt == 0 else LLM_CLIENT_TIMEOUT
            print(
                f"[Thread-{thread_id}] Using timeout of {timeout:.1f} seconds for attempt {attempt + 1}",
                file=sys.stderr,
            )
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(OLLAMA_URL, json=payload)
                resp.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses
                response_json = resp.json()
                response_text = response_json.get("response", "").strip()
                if not response_text and "error" in response_json:
                    response_text = (
                        f"Error: Ollama returned an error - {response_json['error']}"
                    )
                elif not response_text:
                    response_text = (
                        "Error: Ollama returned empty response with no error message."
                    )

                # Successful call, break retry loop
                last_error = None  # Clear the error tracker on success
                break

        except httpx.TimeoutException as e:
            last_error = e
            response_text = f"Error: Ollama call timed out - {e}"
            print(
                f"Warning: Ollama call timed out (attempt {attempt + 1}/{LLM_MAX_RETRIES}): {e}",
                file=sys.stderr,
            )
        except httpx.HTTPStatusError as e:
            last_error = e
            response_text = f"Error: Ollama call failed with HTTP status {e.response.status_code} - {e.response.text}"
            # Retry only on 5xx server errors
            if 500 <= e.response.status_code < 600:
                print(
                    f"Warning: Ollama call failed with HTTP status {e.response.status_code} (attempt {attempt + 1}/{LLM_MAX_RETRIES}). Retrying...",
                    file=sys.stderr,
                )
            else:
                # For 4xx errors, don't retry, just report.
                print(
                    f"Error: Ollama call failed with HTTP status {e.response.status_code}. Not retrying.",
                    file=sys.stderr,
                )
                break  # Do not retry client errors (4xx)
        except httpx.RequestError as e:  # Catches ConnectError and other network issues
            last_error = e
            response_text = f"Error: Ollama request failed - {e}"
            print(
                f"Warning: Ollama request failed (attempt {attempt + 1}/{LLM_MAX_RETRIES}): {e}",
                file=sys.stderr,
            )
        except (
            Exception
        ) as e:  # Catch other unexpected errors like JSON parsing if response is not JSON
            last_error = e
            response_text = f"Error: Unexpected error during Ollama call - {e}"
            print(
                f"Warning: Unexpected error in llm_call (attempt {attempt + 1}/{LLM_MAX_RETRIES}): {e}",
                file=sys.stderr,
            )
            # Depending on the error, you might choose to break or continue retrying.
            # For safety, let's break on unexpected errors for now.
            break

        if attempt < LLM_MAX_RETRIES - 1:
            # Apply exponential backoff for HTTP 500 errors
            if (
                isinstance(last_error, httpx.HTTPStatusError)
                and 500 <= last_error.response.status_code < 600
            ):
                # Check for model loading errors
                if (
                    "client connection closed before server finished loading"
                    in last_error.response.text
                ):
                    # Extra long delay for model loading errors
                    backoff_delay = LLM_RETRY_DELAY * (
                        4**attempt
                    )  # Even more aggressive backoff
                    print(
                        f"Model loading error detected. Using extra long delay of {backoff_delay} seconds...",
                        file=sys.stderr,
                    )
                    time.sleep(backoff_delay)
                else:
                    # Exponential backoff: delay_s = base_delay * (2^attempt) with 20% random jitter
                    backoff_delay = LLM_RETRY_DELAY * (2**attempt)
                    # Add jitter (±20%)
                    jitter = backoff_delay * 0.2 * (random.random() * 2 - 1)
                    actual_delay = max(
                        1, backoff_delay + jitter
                    )  # Ensure minimum 1s delay
                    print(
                        f"Waiting {actual_delay:.1f} seconds before next retry (exponential backoff for 500 error)...",
                        file=sys.stderr,
                    )
                    time.sleep(actual_delay)
            else:
                # Standard fixed delay for other errors
                print(
                    f"Waiting {LLM_RETRY_DELAY} seconds before next retry...",
                    file=sys.stderr,
                )
                time.sleep(LLM_RETRY_DELAY)
        else:  # Last attempt failed
            print(
                f"Error: All {LLM_MAX_RETRIES} retry attempts failed for Ollama call.",
                file=sys.stderr,
            )

    # Cache the final result (even if it's an error message, to prevent re-hitting a failing prompt)
    with _CACHE_LOCK:
        _CACHE[prompt] = response_text

    # Log the final result
    prompt_snippet_for_final_debug = (
        prompt[:50].replace("\n", " ").replace("'", "\\'")
    )  # Clean for printing
    final_debug_msg_prefix = f"DEBUG_LLM: Final status for prompt starting with '{prompt_snippet_for_final_debug}...'"
    if response_text.startswith("Error:"):
        # For errors, the response_text can be long, so truncate it more aggressively for the log too.
        error_snippet = response_text[:150].replace("\n", " ").replace("'", "\\'")
        print(
            f"{final_debug_msg_prefix} resulted in error: '{error_snippet}...'",
            file=sys.stderr,
        )
    else:
        # For successful responses, also truncate.
        success_snippet = response_text[:100].replace("\n", " ").replace("'", "\\'")
        print(
            f"{final_debug_msg_prefix} returned: '{success_snippet}...'",
            file=sys.stderr,
        )

    return response_text


def preload_model() -> bool:
    """
    Preload the model before starting any processing.
    This ensures the model is loaded into memory before parallel processing begins.

    Returns:
        bool: True if preloading succeeded, False otherwise
    """
    print(f"Preloading model {MODEL_TAG}...", file=sys.stderr)

    max_preload_attempts = 3
    payload = {
        "model": MODEL_TAG,
        "prompt": LLM_PRELOAD_PROMPT,
        "stream": False,
        "options": {"num_ctx": CTX},
    }

    for attempt in range(max_preload_attempts):
        try:
            print(
                f"Preload attempt {attempt+1}/{max_preload_attempts}", file=sys.stderr
            )
            # Use a very long timeout for preloading
            with httpx.Client(timeout=LLM_FIRST_ATTEMPT_TIMEOUT) as client:
                resp = client.post(OLLAMA_URL, json=payload)
                resp.raise_for_status()

                print(f"Model {MODEL_TAG} successfully preloaded!", file=sys.stderr)
                return True

        except httpx.HTTPStatusError as e:
            # Specifically handle 500 errors which might indicate model loading issues
            if 500 <= e.response.status_code < 600:
                print(
                    f"Model loading error during preload (attempt {attempt+1}): {e}",
                    file=sys.stderr,
                )

                # If the error text suggests the model is still loading
                if (
                    "client connection closed before server finished loading"
                    in e.response.text
                ):
                    delay = LLM_RETRY_DELAY * (4 ** (attempt))
                    print(
                        f"Model still loading, waiting {delay} seconds before retry...",
                        file=sys.stderr,
                    )
                    time.sleep(delay)
                else:
                    delay = LLM_RETRY_DELAY * (2 ** (attempt))
                    print(
                        f"Server error, waiting {delay} seconds before retry...",
                        file=sys.stderr,
                    )
                    time.sleep(delay)
            else:
                print(f"HTTP error during model preload: {e}", file=sys.stderr)
                return False

        except httpx.TimeoutException as e:
            print(
                f"Timeout during model preload (attempt {attempt+1}): {e}",
                file=sys.stderr,
            )
            # Try again with longer delay between attempts
            time.sleep(LLM_RETRY_DELAY * (2 ** (attempt)))

        except Exception as e:
            print(f"Error during model preload: {e}", file=sys.stderr)
            return False

    print(
        f"Failed to preload model {MODEL_TAG} after {max_preload_attempts} attempts",
        file=sys.stderr,
    )
    return False
