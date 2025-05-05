import re
import uuid
import hashlib
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.models import DocumentChunk, Document

def _split_text_recursive(
    text: str, max_chunk_size: int, separators: List[str], chunk_overlap: int = 50
) -> List[str]:
    """
    Recursively splits text trying different separators.
    Starts with the coarsest separator, then finer ones if chunks are still too large.
    Applies a final character-level split if needed.
    """
    final_chunks = []
    # Start with the full text
    remaining_text = text.strip()
    if not remaining_text:
        return []

    # Base case: If the text is already small enough
    if len(remaining_text) <= max_chunk_size:
        return [remaining_text]

    current_separator = separators[0] if separators else ""

    # Try splitting with the current separator
    if current_separator:
        split_using_separator = remaining_text.split(current_separator)
    else:
        # If no separators left, split by character
        split_using_separator = list(remaining_text) # Effectively character split prep

    current_chunk = ""
    for i, part in enumerate(split_using_separator):
        # Add separator back if it wasn't the final character split
        part_to_add = part
        if current_separator and i > 0:
             part_to_add = current_separator + part

        # If adding the next part doesn't exceed the max size
        if not current_chunk or len(current_chunk) + len(part_to_add) <= max_chunk_size:
            current_chunk += part_to_add
        else:
            # Chunk is full. Need to process this chunk.
            # If the chunk itself is too large even after splitting by the current separator
            if len(current_chunk) > max_chunk_size:
                # Recurse with finer separators
                finer_separators = separators[1:]
                recursive_chunks = _split_text_recursive(
                    current_chunk, max_chunk_size, finer_separators, chunk_overlap
                )
                final_chunks.extend(recursive_chunks)
            else:
                 # Chunk is within size limits
                 final_chunks.append(current_chunk)

            # Start a new chunk with the current part, adding overlap from the previous chunk
            overlap = final_chunks[-1][-chunk_overlap:] if final_chunks and chunk_overlap > 0 else ""
            current_chunk = overlap + part_to_add

            # Check if the new chunk (with overlap) is already too large
            if len(current_chunk) > max_chunk_size:
                 # If the part itself is too large, recurse on it directly
                 finer_separators = separators[1:]
                 recursive_chunks = _split_text_recursive(
                    part_to_add, max_chunk_size, finer_separators, chunk_overlap
                 )
                 final_chunks.extend(recursive_chunks)
                 current_chunk = "" # Reset chunk as it was handled recursively

    # Add the last remaining chunk
    if current_chunk:
        if len(current_chunk) > max_chunk_size:
            finer_separators = separators[1:]
            recursive_chunks = _split_text_recursive(
                current_chunk, max_chunk_size, finer_separators, chunk_overlap
            )
            final_chunks.extend(recursive_chunks)
        else:
            final_chunks.append(current_chunk)

    # Filter out potential empty chunks from splitting
    return [chunk for chunk in final_chunks if chunk.strip()]


def _split_markdown_by_headers(
    markdown_text: str, split_level: int
) -> List[Tuple[Dict[str, Optional[str]], str]]:
    """
    Splits markdown text based on headers of a specified level.
    Returns a list of tuples, each containing metadata (header hierarchy) and the text block.
    """
    lines = markdown_text.splitlines()
    chunks = []
    current_chunk_lines = []
    current_headers = {i: None for i in range(1, 7)}
    header_pattern = re.compile(r"^(#{1,6})\s+(.*)")

    for line in lines:
        header_match = header_pattern.match(line)
        if header_match:
            level = len(header_match.group(1))
            title = header_match.group(2).strip()

            # If we encounter a header at or above the split level,
            # finalize the previous chunk (if any)
            if level <= split_level and current_chunk_lines:
                text_block = "\n".join(current_chunk_lines).strip()
                if text_block:
                    chunks.append(
                        (current_headers.copy(), text_block)
                    )
                current_chunk_lines = [] # Start new chunk

            # Update header hierarchy for the *next* chunk
            current_headers[level] = title
            # Clear lower-level headers
            for i in range(level + 1, 7):
                current_headers[i] = None

            # Include the header line itself in the new chunk *unless* it's the primary split level
            if level > split_level:
               current_chunk_lines.append(line)
            # Option: always include header line: uncomment below
            # current_chunk_lines.append(line)

        else:
            current_chunk_lines.append(line)

    # Add the last chunk
    if current_chunk_lines:
        text_block = "\n".join(current_chunk_lines).strip()
        if text_block:
            chunks.append((current_headers.copy(), text_block))

    return chunks

def chunk_markdown(
    markdown_text: str,
    split_level: int = 2, # e.g., 2 for ##
    max_chunk_size: int = 1000,
    chunk_overlap: int = 50, # Overlap for recursive fallback
    source_document: Optional[str] = None
) -> List[Dict]:
    """
    Chunks a Markdown document with header awareness and size control.

    Args:
        markdown_text: The input Markdown string.
        split_level: The header level to split by (e.g., 1 for #, 2 for ##).
        max_chunk_size: The maximum character length for a chunk.
        chunk_overlap: Character overlap for recursive splitting fallback.
        source_document: Optional identifier for the source document.

    Returns:
        A list of dictionaries, where each dict represents a chunk
        with 'text' and 'metadata' keys.
    """
    # 1. Preserve Atomic Units (Code Blocks)
    code_block_pattern = re.compile(r"(^```.*?^```)", re.MULTILINE | re.DOTALL)
    code_blocks = {}
    placeholder_template = "CODEBLOCK_PLACEHOLDER_{}"

    def replace_code_block(match):
        block_id = str(uuid.uuid4())
        placeholder = placeholder_template.format(block_id)
        code_blocks[placeholder] = match.group(1)
        return placeholder

    processed_text = code_block_pattern.sub(replace_code_block, markdown_text)

    # 2. Primary Split by Headers
    primary_chunks = _split_markdown_by_headers(processed_text, split_level)

    final_chunks = []
    chunk_seq_id = 0

    # 3. Secondary Split / Size Control Fallback
    for headers, text_block in primary_chunks:
        if not text_block.strip():
            continue

        base_metadata = {"headers": {f"h{k}": v for k, v in headers.items() if v}}
        if source_document:
            base_metadata["source_document"] = source_document

        # Check if the primary chunk needs further splitting
        if len(text_block) <= max_chunk_size:
             # Re-insert code blocks before adding
             final_text = text_block
             for placeholder, code in code_blocks.items():
                 if placeholder in final_text:
                     final_text = final_text.replace(placeholder, code)

             chunk_metadata = base_metadata.copy()
             chunk_metadata["chunk_id"] = f"{source_document or 'doc'}_{chunk_seq_id}"
             final_chunks.append({"text": final_text, "metadata": chunk_metadata})
             chunk_seq_id += 1
        else:
            # Apply recursive splitting with fallback separators
            # Prioritize paragraphs, then lines, then recursive character split
            separators = ["\n\n", "\n", ". ", "! ", "? ", " ", ""] # Include common sentence enders and space
            sub_chunks = _split_text_recursive(
                text_block, max_chunk_size, separators, chunk_overlap
            )

            for sub_chunk_text in sub_chunks:
                # Re-insert code blocks into the sub-chunk
                final_sub_text = sub_chunk_text
                for placeholder, code in code_blocks.items():
                     if placeholder in final_sub_text:
                         final_sub_text = final_sub_text.replace(placeholder, code)

                chunk_metadata = base_metadata.copy()
                chunk_metadata["chunk_id"] = f"{source_document or 'doc'}_{chunk_seq_id}"
                final_chunks.append({"text": final_sub_text, "metadata": chunk_metadata})
                chunk_seq_id += 1

    # Final pass to ensure no placeholders remain (e.g., if a code block was the only content)
    # This is less likely with the current logic but good for robustness
    for chunk in final_chunks:
         for placeholder, code in code_blocks.items():
             if placeholder in chunk["text"]:
                 chunk["text"] = chunk["text"].replace(placeholder, code)

    return final_chunks

def save_chunks_to_database(
    db: Session,
    chunks: List[Dict],
    document_id: int,
    project_id: int,
    file_name: str,
    file_hash: str
) -> List[str]:
    """
    Saves document chunks to the database.
    
    Args:
        db: SQLAlchemy database session
        chunks: List of chunk dictionaries from chunk_markdown function
        document_id: ID of the document these chunks belong to
        project_id: ID of the project these chunks belong to
        file_name: Name of the source file
        file_hash: Hash of the source file
        
    Returns:
        List of chunk IDs that were saved to the database
    """
    saved_chunk_ids = []
    
    for chunk in chunks:
        # Generate a unique chunk ID if not already present
        chunk_id = chunk["metadata"].get("chunk_id")
        if not chunk_id:
            # Create a deterministic ID based on content and document
            content_hash = hashlib.sha256(chunk["text"].encode()).hexdigest()[:16]
            chunk_id = f"{file_hash[:8]}_{content_hash}"
            chunk["metadata"]["chunk_id"] = chunk_id
        
        # Create a new database record
        db_chunk = DocumentChunk(
            id=chunk_id,
            project_id=project_id,
            document_id=document_id,
            file_name=file_name,
            hash=file_hash,
            chunk_metadata=chunk["metadata"]
        )
        
        # Add the chunk text directly to the metadata for storage
        # This assumes the metadata field can store the text content
        db_chunk.chunk_metadata["content"] = chunk["text"]
        
        # Add to session and commit
        db.add(db_chunk)
        saved_chunk_ids.append(chunk_id)
    
    # Commit all chunks in a single transaction
    db.commit()
    
    return saved_chunk_ids

