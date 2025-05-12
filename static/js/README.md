<!-- BEGIN summary: main.js -->
## main.js

**For Non-Technical Readers:**
This JavaScript file is part of a web application that enhances user interaction on a webpage. It handles form submissions, displays processing status, and streams logs in real-time. The code ensures that user-generated content is displayed safely, preventing potential security threats. It also automates form-filling by syncing multiple fields with a selected value from a dropdown menu. Overall, this code improves the user experience by providing real-time feedback and simplifying form interactions.

**PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:**
The main purpose of this JavaScript file is to manage user interactions on a web page, including form submissions, log streaming, and automating certain form fields. It ensures that user-generated content is displayed safely and provides real-time updates on processing status and logs.

**KEY USER-FACING COMPONENTS AND USAGE:**
- **`escapeHtml(unsafe)`**: This function takes a string input that may contain HTML special characters and converts it into a safe format for display on a web page. It prevents cross-site scripting (XSS) attacks by replacing characters like `<`, `>`, `&`, `"`, and `'` with their corresponding HTML entities.
- **`displayLogs(logsArray, targetElement)`**: This function displays an array of log messages within a specified HTML element on a webpage. It formats the log messages into an HTML string, escaping any HTML characters to prevent code injection, and appends them to the target element.
- **`attachLlmMode(event)`**: This function updates all form fields with a specific class (`llm_mode_input`) to match the value selected from a dropdown menu (`llm_mode_select`). It simplifies form-filling by automating the syncing of multiple fields with the selected value.
- **`setupLogStream()`**: This function establishes a connection to a log stream server, displaying real-time log messages in a designated container on the webpage. It also updates a status indicator based on the received data and attempts to reconnect if the connection is lost.
<!-- END summary: main.js -->