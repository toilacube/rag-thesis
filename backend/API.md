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
