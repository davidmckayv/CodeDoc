<!-- BEGIN summary: main.js -->
## main.js

PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:
This file is designed to handle various aspects of user interaction and data presentation within a web application, focusing on security, real-time updates, and form management. It includes functionalities for escaping HTML to prevent XSS attacks, displaying log messages, synchronizing form input fields, and establishing a real-time log stream connection.

KEY USER-FACING COMPONENTS AND USAGE:
- **`escapeHtml(unsafe)`**: This function takes a string input and returns its HTML-escaped equivalent, preventing XSS attacks by ensuring user-inputted data is safely displayed within HTML content. It replaces special characters with their corresponding HTML entities.
- **`displayLogs(logsArray, targetElement)`**: Displays an array of log messages within a specified HTML element on a web page. It formats the log messages into HTML, escaping any HTML characters, and appends them to the target element. The function returns a boolean indicating whether the logs were successfully displayed.
- **`attachLlmMode(event)`**: Synchronizes the value of a selected LLM mode across multiple input fields within a form when triggered by an event. It updates the value of all elements with the class `llm_mode_input` to match the value selected in the `llm_mode_select` element.
- **`setupLogStream()`**: Establishes a real-time log stream connection to the server, displaying log updates and system status changes in the UI. It automatically attempts to reconnect upon connection loss and updates the log display and system status indicator accordingly.
<!-- END summary: main.js -->