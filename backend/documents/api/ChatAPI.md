# Chat API Documentation

**- All API endpoints have a prefix `/api` - e.g., `http://localhost:8000/api/chat`**
**- All requests requiring authentication must include an `Authorization: Bearer YOUR_ACCESS_TOKEN` header.**

## Chat Session Endpoints

### 1. Get All Chat Sessions for Current User

Retrieves a list of all chat sessions initiated by the currently authenticated user.

*   **Endpoint:** `GET /chat/`
*   **Method:** `GET`
*   **Authentication:** Required.
*   **Response:** `200 OK` with a list of `ChatResponse` objects.

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

Creates a new chat session. Each chat session must be linked to a specific project, which will be used as the context for potential RAG (Retrieval Augmented Generation) operations.

*   **Endpoint:** `POST /chat/`
*   **Method:** `POST`
*   **Authentication:** Required.
*   **Request Body:** `ChatCreate` schema.
    *   `title` (string, required): A title for the chat session (e.g., "Question about feature X").
    *   `project_id` (integer, required): The ID of the project this chat session is associated with.
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
      "detail": "Project with ID 1 not found"
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

Retrieves the details of a specific chat session, including all its messages, if it belongs to the currently authenticated user.

*   **Endpoint:** `GET /chat/{chat_id}`
*   **Method:** `GET`
*   **Path Parameter:**
    *   `chat_id` (integer, required): The ID of the chat session to retrieve.
*   **Authentication:** Required.
*   **Response:** `200 OK` with the `ChatResponse` object.

**Success Response (`200 OK`):**
```json
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
    // ... more messages
  ]
}
```

**Error Responses:**
*   `404 Not Found`: If the chat session with the given `chat_id` does not exist or does not belong to the current user.
    ```json
    {
      "detail": "Chat not found or access denied."
    }
    ```

**cURL Example:**
```bash
curl -X GET 'http://localhost:8000/api/chat/1' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

---

## Message Endpoints

### 4. Send a Message to a Chat Session

Sends a new message from the user to an existing chat session. The system will save the user's message and then generate and save an assistant's response. The assistant's response may involve RAG if the system determines it's necessary based on the conversation and the user's query.

*   **Endpoint:** `POST /chat/{chat_id}/message`
*   **Method:** `POST`
*   **Path Parameter:**
    *   `chat_id` (integer, required): The ID of the chat session to send the message to.
*   **Authentication:** Required.
*   **Request Body:** `MessageCreate` schema.
    *   `content` (string, required): The text content of the user's message.
    *   `role` (string, required, **must be "user"**): The role of the message sender. For this endpoint, it must always be "user".
*   **Response:** `200 OK` with a tuple (list in JSON) containing two `MessageResponse` objects:
    1.  The saved user message.
    2.  The generated and saved assistant's message.

**Request Body Example:**
```json
{
  "content": "What are the key features of the new billing system?",
  "role": "user"
}
```

**Success Response (`200 OK`):**
```json
[
  {
    "content": "What are the key features of the new billing system?",
    "role": "user",
    "id": 3,
    "chat_id": 1,
    "created_at": "2025-05-18T11:05:00Z",
    "updated_at": "2025-05-18T11:05:00Z"
  },
  {
    "content": "The new billing system includes automated invoicing, support for multiple payment gateways, and detailed financial reporting. You can find more details in the 'Billing System Overview.pdf' document.",
    "role": "assistant",
    "id": 4,
    "chat_id": 1,
    "created_at": "2025-05-18T11:05:05Z",
    "updated_at": "2025-05-18T11:05:05Z"
  }
]
```

**Error Responses:**
*   `400 Bad Request`: If the `role` in the request body is not "user".
    ```json
    {
      "detail": "Message role must be 'user'."
    }
    ```
*   `400 Bad Request`: If the chat session is not linked to a project (should not happen with proper chat creation).
    ```json
    {
        "detail": "Chat session is not linked to a project, RAG cannot be performed."
    }
    ```
*   `404 Not Found`: If the chat session with the given `chat_id` does not exist or does not belong to the current user.
    ```json
    {
      "detail": "Chat session not found or access denied."
    }
    ```
*   `500 Internal Server Error`: If there's an issue processing the message or generating an assistant response.
    ```json
    {
      "detail": "Failed to process message."
    }
    ```

**cURL Example 1 (Simple query, might not trigger RAG):**
```bash
curl -X POST 'http://localhost:8000/api/chat/1/message' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "content": "Hello, how are you today?",
    "role": "user"
  }'
```

**cURL Example 2 (Query likely to trigger RAG if project documents are relevant):**
```bash
curl -X POST 'http://localhost:8000/api/chat/1/message' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "content": "Can you summarize the main points from the Q2 financial report document?",
    "role": "user"
  }'
```

## Data Transfer Objects (DTOs) Reference

### ChatResponse
```json
{
  "title": "string",
  "id": "integer",
  "user_id": "integer",
  "project_id": "integer", // ID of the project this chat is linked to
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)",
  "messages": [
    // Array of MessageResponse objects
  ]
}
```

### MessageResponse
```json
{
  "content": "string",
  "role": "string ('user' or 'assistant')",
  "id": "integer",
  "chat_id": "integer",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)"
}
```

### ChatCreate (Request for POST /chat/)
```json
{
  "title": "string (required)",
  "project_id": "integer (required)"
}
```

### MessageCreate (Request for POST /chat/{chat_id}/message)
```json
{
  "content": "string (required)",
  "role": "string (required, must be 'user')"
}
```
