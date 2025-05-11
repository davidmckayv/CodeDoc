"""Remote LLM (Together AI via OpenAI compatible API) interaction module."""

import os
import sys
import time
import threading
import openai

# ------------------ config ------------------
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
TOGETHER_BASE_URL = "https://api.together.xyz/v1"
# Default model, can be overridden in calls
DEFAULT_REMOTE_MODEL = os.getenv(
    "REMOTE_MODEL_TAG", "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
)
REMOTE_LLM_MAX_RETRIES = int(os.getenv("REMOTE_LLM_MAX_RETRIES", "3"))
REMOTE_LLM_RETRY_DELAY = int(os.getenv("REMOTE_LLM_RETRY_DELAY", "5"))  # seconds
REMOTE_LLM_TIMEOUT = float(os.getenv("REMOTE_LLM_TIMEOUT", "120.0"))  # seconds

_REMOTE_CACHE: dict[str, str] = {}
_REMOTE_CACHE_LOCK = threading.Lock()

# ------------------ helpers ------------------


def get_openai_client():
    if not TOGETHER_API_KEY:
        raise ValueError("TOGETHER_API_KEY environment variable is not set.")
    return openai.OpenAI(
        api_key=TOGETHER_API_KEY,
        base_url=TOGETHER_BASE_URL,
        timeout=REMOTE_LLM_TIMEOUT,
    )


def llm_call_remote(prompt: str, model_name: str | None = None) -> str:
    """Blocking call to Together AI API, with thread-safe caching and retries."""
    model_to_use = model_name if model_name else DEFAULT_REMOTE_MODEL
    cache_key = f"{model_to_use}:{prompt}"

    with _REMOTE_CACHE_LOCK:
        if cache_key in _REMOTE_CACHE:
            return _REMOTE_CACHE[cache_key]

    try:
        response_text = "Error: Max retries reached for Remote LLM call."

        for attempt in range(REMOTE_LLM_MAX_RETRIES):
            try:
                client = get_openai_client()
                prompt_snippet = prompt[:50].replace("\n", " ").replace("'", "\\'")
                thread_id = threading.get_ident()
                print(
                    f"[Thread-{thread_id}] DEBUG_REMOTE_LLM: Attempt {attempt + 1}/{REMOTE_LLM_MAX_RETRIES} for model '{model_to_use}' prompt starting with '{prompt_snippet}...'",
                    file=sys.stderr,
                )

                completion = client.chat.completions.create(
                    model=model_to_use,
                    messages=[
                        # Using a simple system prompt, can be customized if needed
                        {
                            "role": "system",
                            "content": """You are a specialized AI assistant. Your sole purpose is to generate content for a project's README.md file. This content is critical for improving IDE-based RAG (Retrieval Augmented Generation) systems, enabling better semantic search for both technical and non-technical users, particularly those unfamiliar with engineering lexicon.

Follow these instructions STRICTLY:
1.  Output MUST be in valid Markdown format.
2.  Focus EXCLUSIVELY on describing the provided code or content. Do NOT add any introductory, concluding, or conversational remarks.
3.  Generate clear, concise, accurate, and factual descriptions.
4.  The output should be directly usable as a section within a README.md file.""",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    # stream=False # Default is False
                )
                response_text = completion.choices[0].message.content.strip()
                if not response_text:
                    response_text = "Error: Remote LLM returned empty response."

                # Successful call, break retry loop
                break

            except openai.APIConnectionError as e:
                response_text = f"Error: Remote LLM API connection error - {e}"
                print(
                    f"Warning: Remote LLM API connection error (attempt {attempt + 1}/{REMOTE_LLM_MAX_RETRIES}): {e}",
                    file=sys.stderr,
                )
            except openai.RateLimitError as e:
                response_text = f"Error: Remote LLM API rate limit exceeded - {e}"
                print(
                    f"Warning: Remote LLM API rate limit exceeded (attempt {attempt + 1}/{REMOTE_LLM_MAX_RETRIES}): {e}",
                    file=sys.stderr,
                )
                # For rate limit errors, backing off is crucial.
                # Consider a more sophisticated backoff if this becomes common.
            except openai.APIStatusError as e:
                response_text = f"Error: Remote LLM API status error ({e.status_code}) - {e.response}"
                print(
                    f"Warning: Remote LLM API status error (attempt {attempt + 1}/{REMOTE_LLM_MAX_RETRIES}): {e}",
                    file=sys.stderr,
                )
                # Don't retry on 4xx client errors other than rate limits (handled above) or timeouts (handled by openai.APITimeoutError)
                if 400 <= e.status_code < 500 and e.status_code not in [
                    408,
                    429,
                ]:  # 408 Request Timeout, 429 Too Many Requests
                    break
            except openai.APITimeoutError as e:
                response_text = f"Error: Remote LLM API request timed out - {e}"
                print(
                    f"Warning: Remote LLM API request timed out (attempt {attempt + 1}/{REMOTE_LLM_MAX_RETRIES}): {e}",
                    file=sys.stderr,
                )
            except Exception as e:  # Catch any other unexpected errors
                response_text = f"Error: Unexpected error during Remote LLM call - {e}"
                print(
                    f"Warning: Unexpected error in llm_call_remote (attempt {attempt + 1}/{REMOTE_LLM_MAX_RETRIES}): {type(e).__name__} - {e}",
                    file=sys.stderr,
                )
                break  # Don't retry unknown errors by default

            if attempt < REMOTE_LLM_MAX_RETRIES - 1:
                print(
                    f"Waiting {REMOTE_LLM_RETRY_DELAY} seconds before next retry...",
                    file=sys.stderr,
                )
                time.sleep(REMOTE_LLM_RETRY_DELAY)
            else:  # Last attempt failed
                print(
                    f"Error: All {REMOTE_LLM_MAX_RETRIES} retry attempts failed for Remote LLM call to model '{model_to_use}'.",
                    file=sys.stderr,
                )

        # After the loop (or break from it)
        with (
            _REMOTE_CACHE_LOCK
        ):  # Cache the final outcome (success or error after retries)
            _REMOTE_CACHE[cache_key] = response_text

        # Log the final result
        prompt_snippet_for_final_debug = (
            prompt[:50].replace("\n", " ").replace("'", "\\'")
        )
        final_debug_msg_prefix = f"DEBUG_REMOTE_LLM: Final status for model '{model_to_use}' prompt starting with '{prompt_snippet_for_final_debug}...'"
        if response_text.startswith("Error:"):
            error_snippet = response_text[:150].replace("\n", " ").replace("'", "\\'")
            print(
                f"{final_debug_msg_prefix} resulted in error: '{error_snippet}...'",
                file=sys.stderr,
            )
        else:
            success_snippet = response_text[:100].replace("\n", " ").replace("'", "\\'")
            print(
                f"{final_debug_msg_prefix} returned: '{success_snippet}...'",
                file=sys.stderr,
            )

        return response_text
    finally:
        pass  # Ensure semaphore is always released (removed as semaphore is removed)


# Example usage (optional, for testing this module directly)
if __name__ == "__main__":
    print("Attempting to call remote LLM (Together AI)...")
    if not TOGETHER_API_KEY:
        print(
            "Error: TOGETHER_API_KEY environment variable is not set. Cannot run example.",
            file=sys.stderr,
        )
        sys.exit(1)

    test_prompt = "Explain the theory of relativity in simple terms."
    print(f"Test prompt: {test_prompt}")
    try:
        summary = llm_call_remote(test_prompt)
        print(f"\nResponse from {DEFAULT_REMOTE_MODEL}:\n{summary}")
    except ValueError as ve:
        print(f"Error during example: {ve}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred during the example: {e}", file=sys.stderr)

    # Test caching
    print("\nAttempting the same call again (should be cached):")
    try:
        summary_cached = llm_call_remote(test_prompt)
        print(f"\nCached response from {DEFAULT_REMOTE_MODEL}:\n{summary_cached}")
    except Exception as e:
        print(
            f"An unexpected error occurred during the cached example: {e}",
            file=sys.stderr,
        )
