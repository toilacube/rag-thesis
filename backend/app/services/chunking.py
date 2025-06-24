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
    split_level: int = 3,
    max_chunk_size: int = 1000,
    chunk_overlap: int = 50,
    source_document: Optional[str] = None # This is document_id as string
) -> List[Dict]:
    code_block_pattern = re.compile(r"(^```.*?^```)", re.MULTILINE | re.DOTALL)
    code_blocks = {}
    placeholder_template = "CODEBLOCK_PLACEHOLDER_{}"

    def replace_code_block(match):
        block_id = str(uuid.uuid4())
        placeholder = placeholder_template.format(block_id)
        code_blocks[placeholder] = match.group(1)
        return placeholder

    processed_text = code_block_pattern.sub(replace_code_block, markdown_text)
    primary_chunks = _split_markdown_by_headers(processed_text, split_level)
    final_chunks = []
    chunk_seq_id = 0

    for headers, text_block in primary_chunks:
        if not text_block.strip():
            continue

        base_metadata = {"headers": {f"h{k}": v for k, v in headers.items() if v}}
        if source_document:
            base_metadata["source_document_id"] = source_document # Store original doc_id here
            base_metadata["chunk_sequence"] = chunk_seq_id # Store sequence here

        # Re-insert code blocks before further splitting or finalizing
        # This needs to happen before _split_text_recursive if text_block is large
        # and before final_chunks.append if text_block is small.
        
        # Temporarily restore code blocks for accurate length check and splitting
        temp_restored_text_block = text_block
        for placeholder, code in code_blocks.items():
            if placeholder in temp_restored_text_block:
                temp_restored_text_block = temp_restored_text_block.replace(placeholder, code)

        if len(temp_restored_text_block) <= max_chunk_size:
            final_text = temp_restored_text_block # Already restored
            
            chunk_metadata = base_metadata.copy()
            # --- MODIFICATION FOR QDRANT POINT ID ---
            # Generate a UUID for the chunk_id (which will be DocumentChunk.id and Qdrant point ID)
            chunk_metadata["chunk_id"] = str(uuid.uuid4())
            # --- END MODIFICATION ---
            
            final_chunks.append({"text": final_text, "metadata": chunk_metadata})
            chunk_seq_id += 1
        else:
            # If splitting recursively, pass the text_block *without* code blocks restored yet,
            # as _split_text_recursive works on plain text.
            separators = ["\n\n", "\n", ". ", "! ", "? ", " ", ""]
            sub_chunks_text_only = _split_text_recursive(
                text_block, max_chunk_size, separators, chunk_overlap # Pass original text_block with placeholders
            )

            for sub_chunk_text_placeholder in sub_chunks_text_only:
                # Restore code blocks into the sub-chunk
                final_sub_text = sub_chunk_text_placeholder
                for placeholder, code in code_blocks.items():
                    if placeholder in final_sub_text:
                        final_sub_text = final_sub_text.replace(placeholder, code)

                chunk_metadata = base_metadata.copy()
                # --- MODIFICATION FOR QDRANT POINT ID ---
                chunk_metadata["chunk_id"] = str(uuid.uuid4()) # New UUID for each sub-chunk
                # Update sequence for sub-chunks if needed, or rely on order
                chunk_metadata["sub_chunk_sequence_within_block"] = chunk_seq_id # Or a more granular sequence
                # --- END MODIFICATION ---

                final_chunks.append({"text": final_sub_text, "metadata": chunk_metadata})
                chunk_seq_id += 1 # Increment for each sub-chunk or manage sequence differently

    # Final pass to ensure no placeholders remain (should be handled above)
    # for chunk in final_chunks:
    #      for placeholder, code in code_blocks.items():
    #          if placeholder in chunk["text"]:
    #              chunk["text"] = chunk["text"].replace(placeholder, code)
    return final_chunks


def save_chunks_to_database(
    db: Session,
    chunks: List[Dict],
    document_id: int,
    project_id: int,
    file_name: str,
    file_hash: str # This is the original file_hash
) -> List[str]: # Returns list of DocumentChunk.id (which are now UUIDs)
    saved_chunk_ids = []
    
    for chunk_data in chunks:
        # The chunk_id is now a UUID generated in chunk_markdown
        chunk_id = chunk_data["metadata"].get("chunk_id")
        if not chunk_id:
            # This should not happen if chunk_markdown always assigns a UUID
            # As a fallback, generate one here, but it's better if chunk_markdown is robust
            chunk_id = str(uuid.uuid4())
            chunk_data["metadata"]["chunk_id"] = chunk_id # Ensure it's in metadata for consistency
        
        # Create a new database record
        db_chunk = DocumentChunk(
            id=chunk_id, # This is now a UUID string
            project_id=project_id,
            document_id=document_id,
            file_name=file_name,
            hash=file_hash, # Store the original file's hash for reference
            chunk_metadata=chunk_data["metadata"] # This includes source_document_id, chunk_sequence etc.
        )
        
        # Add the chunk text directly to the metadata for storage in DocumentChunk
        # This is already part of the design.
        # db_chunk.chunk_metadata["content"] = chunk_data["text"] # This is redundant if text is in Qdrant payload

        # The actual text of the chunk is in chunk_data["text"]
        # It will be put into the Qdrant payload by the consumer.
        # The DocumentChunk.chunk_metadata will store the metadata from chunk_markdown.
        
        db.add(db_chunk)
        saved_chunk_ids.append(chunk_id)
    
    db.commit() # Commit all chunks for this document in a single transaction
    
    return saved_chunk_ids
