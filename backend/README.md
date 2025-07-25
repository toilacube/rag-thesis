## Stack

- FastAPI
- MySQL

## Setup

**1. Make sure you are in the ./backend directory**

```bash
cd backend/
```

**2. Create and install python libraries for backend**

```bash
python -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

**3. Database setup using Docker**

1. Ensure Docker is installed and running on your system.
2. Start the database service and other services using the `docker-compose.yml` file:
   ```bash
   docker-compose up -d 
   ```
3. Verify that the database is running:
   ```bash
   docker ps
   ```

**4. Database migration**

```bash
alembic upgrade head
```

**5. Run the app**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**6. Open another terminal in backend/ and run the upload_file consumer**

```bash
python run_consumer.py
```

**- Health check**

`/health`

```bash
curl -X GET "http://localhost:8000/api/health"
```

## Typical workflow of RAG

1. User input question.
2. Vectorize the question and then retrieve the most similar document slices.
3. The retrieved context is concatenated with the question and then input into LLM.
4. LLM outputs answers with citation information.
5. The front-end renders the answer, optionally displaying the reference details in a visual interface.
