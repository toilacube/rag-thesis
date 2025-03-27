## Please add a curl example for each endpoint to be able to quickly testing

## API

**- All the api will have a prefix /api - http://localhost:8000/api**


**- Api response**

Check the `app/core/api_reponse.py` file.

Example usage:

```python
from app.core.api_reponse import api_response

@app.get("/")
async def root():
    return api_response(
        data = {
            "message": "Welcome to the FastAPI application!"
        },
        message = "Root endpoint"
    )

```

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
curl -X POST "http://localhost:8000/api/auth/login" \
-H "Content-Type: application/json" \
-d '{
  "username": "your_username",
  "password": "your_password"
}'
```

2. Register

`/auth/register`

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
-H "Content-Type: application/json" \
-d '{
  "username": "new_user",
  "email": "new_user@example.com",
  "password": "secure_password"
}'
```