import re
from typing import Optional


def clean_markdown_response(response: str) -> str:
    """
    Clean LLM markdown response by removing wrapping code block delimiters.
    
    This function handles common cases where LLMs wrap markdown content in code blocks
    like ```markdown or ``` at the beginning and end of responses.
    
    Args:
        response: Raw LLM response that may be wrapped in code blocks
        
    Returns:
        Cleaned markdown content with code block delimiters removed
        
    Examples:
        >>> clean_markdown_response("```markdown\\n# Title\\n\\nContent\\n```")
        "# Title\\n\\nContent"
        
        >>> clean_markdown_response("```\\n# Title\\n\\nContent\\n```")
        "# Title\\n\\nContent"
    """
    if not response or not isinstance(response, str):
        return response or ""
    
    cleaned = response.strip()
    
    # Remove leading code block markers (case-insensitive)
    # Patterns: ```markdown, ```md, ``` markdown, ```
    leading_patterns = [
        r'^```\s*markdown\s*\n?',
        r'^```\s*md\s*\n?', 
        r'^```\s+markdown\s*\n?',
        r'^```\s*\n?'
    ]
    
    for pattern in leading_patterns:
        if re.match(pattern, cleaned, re.IGNORECASE):
            cleaned = re.sub(pattern, '', cleaned, count=1, flags=re.IGNORECASE)
            break
    
    # Remove trailing code block markers
    # Only remove trailing ``` if it's on its own line or at the very end
    trailing_patterns = [
        r'\n```\s*$',
        r'```\s*$'
    ]
    
    for pattern in trailing_patterns:
        if re.search(pattern, cleaned):
            cleaned = re.sub(pattern, '', cleaned, count=1)
            break
    
    return cleaned.strip()


def extract_json_from_response(response: str) -> Optional[str]:
    """
    Extract JSON content from LLM response that may be wrapped in code blocks.
    
    Args:
        response: Raw LLM response that may contain JSON wrapped in code blocks
        
    Returns:
        Extracted JSON string or None if not found
    """
    if not response or not isinstance(response, str):
        return None
    
    cleaned = response.strip()
    
    # Remove leading ```json or ```
    json_patterns = [
        r'^```\s*json\s*\n?',
        r'^```\s*\n?'
    ]
    
    for pattern in json_patterns:
        if re.match(pattern, cleaned, re.IGNORECASE):
            cleaned = re.sub(pattern, '', cleaned, count=1, flags=re.IGNORECASE)
            break
    
    # Remove trailing ```
    if cleaned.endswith('```'):
        cleaned = cleaned[:-3].strip()
    
    return cleaned.strip() if cleaned.strip() else None
