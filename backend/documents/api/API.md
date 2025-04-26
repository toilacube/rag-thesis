## Please add a curl example for each endpoint to be able to quickly testing

## API

**- All the api will have a prefix /api - http://localhost:8000/api**

**- Exception handler**

Example usage:

```python
@router.get("/logout")
async def logout():
    raise HTTPException(status_code = 401, detail = "Unauthorized")
```

**- Health check**

`/health`

```bash
curl -X GET "http://localhost:8000/api/health"
```

**- Auth**

API prefix: `auth`

1. Login

`/auth/login`

```bash
  curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test"
  }'
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNzQ1NjgwMTM4fQ.sVlSs38POa9XYTh4V2BxpyT_spXQ_-xrsxaqeEPXhfk"
}
```

2. Register

`/auth/register`

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "test",
    "password": "test"
  }'
```

Response:

```json
{
  "email": "test@example.com",
  "username": "test",
  "is_active": true,
  "is_superuser": false,
  "id": 2,
  "created_at": "2025-03-27T07:47:00",
  "updated_at": "2025-03-27T07:47:00"
}
```

## Project API Documentation

### Base URL

All endpoints are prefixed with `/api`. For example, `http://localhost:8000/api/project`.

### Endpoints

#### 1. Create a Project

**POST** `/project`

**Request Body:**

```json
{
  "project_name": "My Project",
  "description": "This is a sample project."
}
```

**Curl Example:**

```bash
curl -X POST http://localhost:8000/api/project \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "My Project",
    "description": "This is a sample project."
  }'
```

**Response:**

```json
{
  "id": 1,
  "project_name": "My Project",
  "description": "This is a sample project."
}
```

---

#### 2. Get All Projects

**GET** `/project`

**Curl Example:**

```bash
curl -X GET http://localhost:8000/api/project
```

**Response:**

```json
[
  {
    "id": 1,
    "project_name": "My Project",
    "description": "This is a sample project."
  }
]
```

---

#### 3. Get a Project by ID

**GET** `/project/{project_id}`

**Curl Example:**

```bash
curl -X GET http://localhost:8000/api/project/1
```

**Response:**

```json
{
  "id": 1,
  "project_name": "My Project",
  "description": "This is a sample project."
}
```

---

#### 4. Update a Project

**PUT** `/project/{project_id}`

**Request Body:**

```json
{
  "project_name": "Updated Project",
  "description": "This is an updated project description."
}
```

**Curl Example:**

```bash
curl -X PUT http://localhost:8000/api/project/1 \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "Updated Project",
    "description": "This is an updated project description."
  }'
```

**Response:**

```json
{
  "id": 1,
  "project_name": "Updated Project",
  "description": "This is an updated project description."
}
```

---

#### 5. Delete a Project

**DELETE** `/project/{project_id}`

**Curl Example:**

```bash
curl -X DELETE http://localhost:8000/api/project/1
```

**Response:**

```json
{
  "message": "Project deleted successfully",
  "project_id": 1
}
```

---

#### 6. Get Projects for Current User

**GET** `/project/user/me`

**Description:** Retrieve all projects associated with the currently authenticated user, without needing to specify a user ID. If the user is a superuser (is_superuser=true), this endpoint will return all projects in the system regardless of permissions.

**Curl Example:**

```bash
curl -X GET http://localhost:8000/api/project/user/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**

```json
[
  {
    "id": 1,
    "project_name": "My Project A",
    "description": "First project for current user."
  },
  {
    "id": 3,
    "project_name": "My Project B",
    "description": "Second project for current user."
  }
]
```

**Error Response (Unauthorized):**

- Status Code: `401 Unauthorized`

```json
{
  "detail": "Could not validate credentials"
}
```
