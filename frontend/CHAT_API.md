
```markdown
# Chat API Documentation

**- All API endpoints have a prefix `/api` - e.g., `http://localhost:8000/api/chat`**
**- All requests requiring authentication must include an `Authorization: Bearer YOUR_ACCESS_TOKEN` header.**

## Overview

This API allows users to create chat sessions, send messages, and receive responses from an AI assistant. The assistant can use a knowledge base (linked to a project) to provide contextually relevant answers (Retrieval Augmented Generation - RAG). Responses for new messages are **streamed** to the client for a real-time experience.

## Data Transfer Objects (DTOs) Reference

### ChatResponse
Represents a chat session.
```json
{
  "title": "string", // Title of the chat session
  "id": "integer",   // Unique ID of the chat session
  "user_id": "integer", // ID of the user who owns the chat
  "project_id": "integer", // ID of the project this chat is linked to for RAG
  "created_at": "datetime (ISO 8601 string, e.g., 2025-05-19T10:00:00Z)",
  "updated_at": "datetime (ISO 8601 string, e.g., 2025-05-19T10:05:00Z)",
  "messages": [
    // Array of MessageResponse objects, ordered by creation time
  ]
}
```

### MessageResponse
Represents a single message within a chat session.
```json
{
  "content": "string", // Text content of the message
  "role": "string ('user' or 'assistant')", // Sender of the message
  "id": "integer",   // Unique ID of the message
  "chat_id": "integer", // ID of the chat session this message belongs to
  "created_at": "datetime (ISO 8601 string)",
  "updated_at": "datetime (ISO 8601 string)"
}
```

### ChatCreate (Request for POST /chat/)
Used to create a new chat session.
```json
{
  "title": "string (required)",
  "project_id": "integer (required)" // ID of the project to link this chat to
}
```

### MessageCreate (Request for POST /chat/{chat_id}/message)
Used by the user to send a new message.
```json
{
  "content": "string (required)",
  "role": "string (required, must be 'user')"
}
```

## Chat Session Endpoints

### 1. Get All Chat Sessions for Current User

Retrieves a list of all chat sessions initiated by the currently authenticated user, ordered by the most recently updated.

*   **Endpoint:** `GET /chat/`
*   **Method:** `GET`
*   **Authentication:** Required.
*   **Response:** `200 OK` with a JSON array of `ChatResponse` objects.

**Success Response (`200 OK`):**
```json
[
  {
    "title": "Support query about billing",
    "id": 1,
    "user_id": 123,
    "project_id": 1,
    "created_at": "2025-05-18T10:00:00Z",
    "updated_at": "2025-05-18T10:05:00Z",
    "messages": [
      {
        "content": "Hello, I have a question about my last invoice.",
        "role": "user",
        "id": 1,
        "chat_id": 1,
        "created_at": "2025-05-18T10:00:00Z",
        "updated_at": "2025-05-18T10:00:00Z"
      },
      {
        "content": "Sure, I can help with that. Could you please provide the invoice number?",
        "role": "assistant",
        "id": 2,
        "chat_id": 1,
        "created_at": "2025-05-18T10:01:00Z",
        "updated_at": "2025-05-18T10:01:00Z"
      }
    ]
  },
  {
    "title": "Technical question on API integration",
    "id": 2,
    "user_id": 123,
    "project_id": 2,
    "created_at": "2025-05-17T15:30:00Z",
    "updated_at": "2025-05-17T15:30:00Z",
    "messages": []
  }
]
```

**cURL Example:**
```bash
curl -X GET 'http://localhost:8000/api/chat/' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

---

### 2. Create a New Chat Session

Creates a new chat session. Each chat session must be linked to a specific project, which will be used as the context for potential RAG operations.

*   **Endpoint:** `POST /chat/`
*   **Method:** `POST`
*   **Authentication:** Required.
*   **Request Body:** `ChatCreate` schema (see DTOs reference).
*   **Response:** `201 Created` with the created `ChatResponse` object.

**Request Body Example:**
```json
{
  "title": "Inquiry about product documentation",
  "project_id": 1
}
```

**Success Response (`201 Created`):**
```json
{
  "title": "Inquiry about product documentation",
  "id": 3,
  "user_id": 123,
  "project_id": 1,
  "created_at": "2025-05-18T11:00:00Z",
  "updated_at": "2025-05-18T11:00:00Z",
  "messages": []
}
```

**Error Responses:**
*   `404 Not Found`: If the specified `project_id` does not exist.
    ```json
    {
      "status": "error", // Or "detail" depending on global error handler
      "code": 404,
      "message": "Project with ID 1 not found"
    }
    ```

**cURL Example:**
```bash
curl -X POST 'http://localhost:8000/api/chat/' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Inquiry about product documentation",
    "project_id": 1
  }'
```

---

### 3. Get a Specific Chat Session

Retrieves the details of a specific chat session, including all its messages (ordered by creation time), if it belongs to the currently authenticated user.

*   **Endpoint:** `GET /chat/{chat_id}`
*   **Method:** `GET`
*   **Path Parameter:**
    *   `chat_id` (integer, required): The ID of the chat session to retrieve.
*   **Authentication:** Required.
*   **Response:** `200 OK` with the `ChatResponse` object.

**Success Response (`200 OK`):**
(See example response in "Get All Chat Sessions" for a populated chat)

**Error Responses:**
*   `404 Not Found`: If the chat session with the given `chat_id` does not exist or does not belong to the current user.
    ```json
    {
      "status": "error",
      "code": 404,
      "message": "Chat not found or access denied."
    }
    ```

**cURL Example:**
```bash
curl -X GET 'http://localhost:8000/api/chat/1' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

---

## Message Endpoints

### 4. Send a Message and Stream Response

Sends a new message from the user to an existing chat session. The system first saves the user's message. Then, it generates an assistant's response, which is **streamed back to the client as Server-Sent Events (SSE)**. After the full assistant response is generated, it's saved to the database, and a final event confirming this is sent.

*   **Endpoint:** `POST /chat/{chat_id}/message`
*   **Method:** `POST`
*   **Path Parameter:**
    *   `chat_id` (integer, required): The ID of the chat session to send the message to.
*   **Authentication:** Required.
*   **Request Body:** `MessageCreate` schema (see DTOs reference). `role` must be `"user"`.
*   **Response:** `200 OK` with `Content-Type: text/event-stream`. The response body will be a stream of Server-Sent Events.

**Request Body Example:**
```json
{
  "content": "What are the key features of the new billing system?",
  "role": "user"
}
```

#### Streaming Response Details (Server-Sent Events - SSE)

The client should use the `EventSource` API (or an equivalent library) to connect to this endpoint. The server will send a sequence of events. Each event has the format:
`data: <JSON_string>\n\n`

The client needs to parse the `<JSON_string>` for each event. The JSON object will have a `type` field indicating the kind of event.

**Possible Event Types:**

1.  **`user_message_saved`**:
    *   Sent **once** at the beginning of the stream, immediately after the user's message has been successfully saved to the database.
    *   **JSON Data Structure:**
        ```json
        {
          "type": "user_message_saved",
          "message": { /* MessageResponse DTO for the user's message */ }
        }
        ```
    *   **Example `data` line:**
        `data: {"type": "user_message_saved", "message": {"content": "What about feature X?", "role": "user", "id": 10, "chat_id": 1, "created_at": "...", "updated_at": "..."}}\n\n`

2.  **`delta`**:
    *   Sent **multiple times** as the AI assistant generates its response. Each `delta` event contains a small chunk (token or group of tokens) of the assistant's response text.
    *   The client should append these `content` chunks together to form the complete assistant message in the UI.
    *   **JSON Data Structure:**
        ```json
        {
          "type": "delta",
          "content": "string" // A chunk of the assistant's response
        }
        ```
    *   **Example `data` lines (multiple such events will be sent):**
        `data: {"type": "delta", "content": "The key features "}\n\n`
        `data: {"type": "delta", "content": "are: automated "}\n\n`
        `data: {"type": "delta", "content": "invoicing, "}\n\n`
        `data: {"type": "delta", "content": "support for..."}\n\n`

3.  **`assistant_message_saved`**:
    *   Sent **once** after all `delta` events for the assistant's current response have been sent AND the complete assistant message has been successfully saved to the database.
    *   This provides the client with the full, persisted `MessageResponse` DTO for the assistant's message, including its ID and timestamps.
    *   **JSON Data Structure:**
        ```json
        {
          "type": "assistant_message_saved",
          "message": { /* MessageResponse DTO for the assistant's complete message */ }
        }
        ```
    *   **Example `data` line:**
        `data: {"type": "assistant_message_saved", "message": {"content": "The key features are: automated invoicing, support for...", "role": "assistant", "id": 11, "chat_id": 1, "created_at": "...", "updated_at": "..."}}\n\n`

4.  **`error`**:
    *   Sent if an error occurs during the stream generation *after* the initial user message has been saved (e.g., LLM error, RAG error).
    *   **JSON Data Structure:**
        ```json
        {
          "type": "error",
          "detail": "string", // Error message
          "status_code": "integer" // Optional HTTP-like status code for the error
        }
        ```
    *   **Example `data` line:**
        `data: {"type": "error", "detail": "An unexpected error occurred while generating the response."}\n\n`

5.  **`stream_end`**:
    *   Sent **once** as the very last event to signal that the server has finished sending all data for this request (including any `assistant_message_saved` or `error` events).
    *   The client can use this to know when to finalize UI updates or close the `EventSource` connection if desired (though `EventSource` typically handles connection closure on server end).
    *   **JSON Data Structure:**
        ```json
        {
          "type": "stream_end"
        }
        ```
    *   **Example `data` line:**
        `data: {"type": "stream_end"}\n\n`

**Order of Events for a Successful Interaction:**
1.  `user_message_saved`
2.  Multiple `delta` events
3.  `assistant_message_saved`
4.  `stream_end`

**Order of Events if an Error Occurs During Assistant Response Generation:**
1.  `user_message_saved`
2.  (Potentially some `delta` events if the error happened mid-stream)
3.  `error`
4.  `stream_end`

**Error Responses (Non-Streaming, before the stream starts):**
*   `400 Bad Request`: If the `role` in the request body is not "user".
    ```json
    { "status": "error", "code": 400, "message": "Message role must be 'user'." }
    ```
*   `400 Bad Request`: If the chat session is not linked to a project.
    ```json
    { "status": "error", "code": 400, "message": "Chat session is not linked to a project, RAG cannot be performed." }
    ```
*   `404 Not Found`: If the chat session with the given `chat_id` does not exist or does not belong to the current user.
    ```json
    { "status": "error", "code": 404, "message": "Chat session not found or access denied." }
    ```
*   `500 Internal Server Error`: If there's an issue saving the initial user message before the stream can even begin.
    ```json
    { "status": "error", "code": 500, "message": "Failed to save user message: [details]" }
    ```

**cURL Example (Note: `curl` is not ideal for SSE, but shows the request):**
`curl` will show the raw SSE stream. For proper handling, use JavaScript's `EventSource` or a library in your frontend.
```bash
curl -N -X POST 'http://localhost:8000/api/chat/1/message' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -H 'Accept: text/event-stream' \
  -d '{
    "content": "Tell me about vector databases.",
    "role": "user"
  }'
```
**Expected Raw Output from cURL (Illustrative):**
```
data: {"type": "user_message_saved", "message": {"content": "Tell me about vector databases.", "role": "user", "id": 12, "chat_id": 1, "created_at": "...", "updated_at": "..."}}

data: {"type": "delta", "content": "Vector "}

data: {"type": "delta", "content": "databases are "}

data: {"type": "delta", "content": "specialized "}

data: {"type": "delta", "content": "systems designed to..."}

data: {"type": "delta", "content": " efficiently store and query high-dimensional vectors."}

data: {"type": "assistant_message_saved", "message": {"content": "Vector databases are specialized systems designed to efficiently store and query high-dimensional vectors.", "role": "assistant", "id": 13, "chat_id": 1, "created_at": "...", "updated_at": "..."}}

data: {"type": "stream_end"}

```

**Frontend Implementation Hint (JavaScript `EventSource`):**
```javascript
const eventSource = new EventSource(`http://localhost:8000/api/chat/${chatId}/message`, {
  method: 'POST', // EventSource typically uses GET, so this is a simplified view.
                  // For POST with EventSource, you might need a library or a workaround
                  // like initiating with GET and passing data via query params (less ideal for message content)
                  // OR, more commonly, the POST request is standard, and the server *responds* with SSE.
                  // The FastAPI setup handles POST correctly and responds with text/event-stream.
  headers: {
    'Authorization': `Bearer ${yourAccessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ content: "Your message", role: "user" })
});

// This conceptual example assumes EventSource can POST directly like this.
// In practice, you make a POST request using fetch/axios, and if the server
// responds with Content-Type: text/event-stream, you then handle that stream.
// However, FastAPI's StreamingResponse works directly with a normal POST.

// Assuming the POST request itself returns the stream:
// (Using fetch for the POST, then interpreting the response as a stream)

async function sendMessageAndHandleStream(chatId, messageContent, accessToken) {
  const response = await fetch(`http://localhost:8000/api/chat/${chatId}/message`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream' // Important to tell the server we can handle SSE
    },
    body: JSON.stringify({ content: messageContent, role: "user" })
  });

  if (!response.ok) {
    // Handle non-streaming errors (e.g., 400, 401, 404 before stream starts)
    const errorData = await response.json();
    console.error("Error sending message:", errorData);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      console.log("Stream finished by server.");
      break;
    }
    buffer += decoder.decode(value, { stream: true });

    // Process buffer line by line for SSE events
    let eolIndex;
    while ((eolIndex = buffer.indexOf('\n\n')) >= 0) {
      const eventString = buffer.substring(0, eolIndex).trim();
      buffer = buffer.substring(eolIndex + 2);

      if (eventString.startsWith("data: ")) {
        try {
          const jsonData = JSON.parse(eventString.substring(6)); // Skip "data: "
          console.log("Received event:", jsonData);

          if (jsonData.type === "user_message_saved") {
            // Add user's message to UI, mark as saved
            // jsonData.message contains the MessageResponse DTO
          } else if (jsonData.type === "delta") {
            // Append jsonData.content to the assistant's message in UI
          } else if (jsonData.type === "assistant_message_saved") {
            // Finalize assistant's message in UI, update with ID from jsonData.message
          } else if (jsonData.type === "error") {
            // Display error to user
            console.error("Stream error:", jsonData.detail);
          } else if (jsonData.type === "stream_end") {
            console.log("Explicit stream end event received.");
            // Perform any final cleanup
            return; // Exit the read loop
          }
        } catch (e) {
          console.error("Error parsing SSE JSON:", e, "Raw event:", eventString);
        }
      }
    }
  }
}
```
The JavaScript example above using `fetch` and manually parsing the stream is more robust for handling POST requests that return SSE. `EventSource` has limitations with POST and custom headers.

This detailed documentation should give your frontend developer a clear understanding of how to interact with the chat API, especially the streaming message endpoint.
```