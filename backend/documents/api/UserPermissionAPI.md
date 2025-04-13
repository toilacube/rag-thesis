# User Permission API Documentation

**- All the api will have a prefix /api - http://localhost:8000/api**

## User Permission API

### Base URL

All endpoints are prefixed with `/api`. For example, `http://localhost:8000/api/users`.

### Endpoints

#### 1. Add User to Project

**POST** `/users/project/{project_id}/users`

Adds a user to a project with specified permissions. The user must already exist in the system.

**Path Parameters:**

- `project_id`: ID of the project

**Request Body:**

```json
{
  "email": "user@example.com",
  "permissions": ["view_project", "add_document", "edit_document"]
}
```

**Curl Example:**

```bash
curl -X POST http://localhost:8000/api/users/project/1/users \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "permissions": ["view_project", "add_document", "edit_document"]
  }'
```

**Response:**

```json
{
  "user_id": 2,
  "email": "user@example.com",
  "username": "johndoe",
  "project_id": 1,
  "permissions": ["view_project", "add_document", "edit_document"]
}
```

---

#### 2. Get Project Users

**GET** `/users/project/{project_id}/users`

Retrieves all users and their permissions for a specific project.

**Path Parameters:**

- `project_id`: ID of the project

**Curl Example:**

```bash
curl -X GET http://localhost:8000/api/users/project/1/users \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**

```json
[
  {
    "user_id": 1,
    "email": "admin@example.com",
    "username": "admin",
    "project_id": 1,
    "permissions": [
      "admin",
      "manage_user",
      "view_project",
      "edit_project",
      "delete_project",
      "add_document",
      "edit_document",
      "delete_document",
      "manage_api_keys"
    ]
  },
  {
    "user_id": 2,
    "email": "user@example.com",
    "username": "johndoe",
    "project_id": 1,
    "permissions": ["view_project", "add_document", "edit_document"]
  }
]
```

---

#### 3. Update User Permissions

**PUT** `/users/project/{project_id}/user/{user_id}/permissions`

Updates the permissions of a user for a specific project. This replaces all existing permissions with the new set provided.

**Path Parameters:**

- `project_id`: ID of the project
- `user_id`: ID of the user

**Request Body:**

```json
["view_project", "add_document"]
```

**Curl Example:**

```bash
curl -X PUT http://localhost:8000/api/users/project/1/user/2/permissions \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '["view_project", "add_document"]'
```

**Response:**

```json
{
  "status": "success",
  "code": 200,
  "data": {
    "user_id": 2,
    "project_id": 1,
    "permissions": ["view_project", "add_document"]
  },
  "message": "User permissions updated successfully"
}
```

---

#### 4. Remove User from Project

**DELETE** `/users/project/{project_id}/user/{user_id}`

Removes a user from a project by deleting all their permissions for that project.

**Path Parameters:**

- `project_id`: ID of the project
- `user_id`: ID of the user

**Curl Example:**

```bash
curl -X DELETE http://localhost:8000/api/users/project/1/user/2 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**

```json
{
  "status": "success",
  "code": 200,
  "data": null,
  "message": "User user@example.com removed from project 1"
}
```

### Available Permissions

The following permissions can be assigned to users for projects:

| Permission Name   | Description                                            |
| ----------------- | ------------------------------------------------------ |
| `view_project`    | Can view project details and content                   |
| `edit_project`    | Can edit project settings and metadata                 |
| `delete_project`  | Can delete the project                                 |
| `add_document`    | Can add documents to the project                       |
| `edit_document`   | Can edit documents in the project                      |
| `delete_document` | Can delete documents from the project                  |
| `manage_api_keys` | Can create and manage API keys for the project         |
| `manage_user`     | Can add users to projects and manage their permissions |
| `admin`           | Has all permissions for the project                    |

### Permission Requirements

- To add, update, or remove users from a project, the current user must have the `manage_user` permission or be a superuser.
- To view users for a project, the current user must have the `view_project` permission or be a superuser.
- Superusers have access to all projects and can manage permissions for all projects regardless of their specific permissions.

### Error Responses

**400 Bad Request**

- When trying to assign invalid permissions
- When trying to remove yourself from a project
- When required request body is invalid

**403 Forbidden**

- When the user doesn't have sufficient permissions to perform the action

**404 Not Found**

- When the specified user, project, or permission cannot be found

**500 Internal Server Error**

- When an unexpected error occurs during the operation
