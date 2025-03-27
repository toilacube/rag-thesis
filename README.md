## To setup the backend please see README.md in ./backend directory


## TODO
- Setup backend
- Login/register jwt:
        - scope base authorization
- Document upload:
### User uploaded documents (PDF/MD/TXT/DOCX)
        1. The client initiates a document upload request
        2. The files are temporarily stored on NFS (Network File System)
        3. The system generates and returns a Job ID to the client

### Asynchronous process start
        1. Document preprocessing: extracting text and cleaning data
        2. Text segmentation: segment text according to the set strategy
        3. Vectorization: Convert text into vectors through the Embedding service
        4. Storage: Save vector data to vector database

### Status Query
        1. The client polls the task status by Job ID
        2. The system returns the current progress (Processing/Completed/Failed)
