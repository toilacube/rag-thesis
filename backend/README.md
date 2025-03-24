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

**3. Database migration**

```bash
alembic upgrade head  
```







## Typical workflow of RAG

1. User input question.
2. Vectorize the question and then retrieve the most similar document slices.
3. The retrieved context is concatenated with the question and then input into LLM.
4. LLM outputs answers with citation information.
5. The front-end renders the answer, optionally displaying the reference details in a visual interface.
