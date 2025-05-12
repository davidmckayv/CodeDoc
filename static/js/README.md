<!-- BEGIN summary: main.js -->
## main.js

**For Non-Technical Readers:**
This JavaScript file contains functions that help with displaying and managing content on a webpage, making it more interactive and secure. It includes tools for preventing security issues when showing user-generated content, displaying log messages in a readable format, synchronizing input fields, and setting up a live log stream. These features improve the user experience by ensuring content is displayed correctly, providing real-time updates, and simplifying form interactions.

**PRIMARY TECHNICAL RESPONSIBILITY FROM A USER PERSPECTIVE:**
The file is primarily responsible for enhancing user interaction and security on a webpage. It achieves this through four main functions: escaping HTML characters in user-generated content to prevent security vulnerabilities, displaying log messages in a user-friendly manner, synchronizing input fields within a form, and establishing a real-time log stream.

**KEY USER-FACING COMPONENTS AND USAGE:**
- **`escapeHtml(unsafe)`**: This function takes a string that may contain special characters and converts them into a safe format for display on a webpage, preventing potential security issues. It's used when displaying user-generated content.
- **`displayLogs(logsArray, targetElement)`**: Displays an array of log messages within a specified HTML element on a webpage, formatting them for readability. It's typically used after operations like data processing or network requests to provide feedback.
- **`attachLlmMode(event)`**: Synchronizes a selected mode across multiple input fields within a form when triggered by an event, simplifying user interaction by reducing repetitive input.
- **`setupLogStream()`**: Establishes a connection to a log stream server, displaying real-time log messages in a designated container and updating a status indicator based on received data. It's used for monitoring system behavior or debugging.
<!-- END summary: main.js -->