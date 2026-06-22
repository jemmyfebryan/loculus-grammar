"""Grammar correction service using Gemini AI."""
from typing import Optional, List
from google import genai
from app.models import GrammarOutput
from app.config import GEMINI_API_KEY


client = genai.Client(api_key=GEMINI_API_KEY)


def word_level_levenshtein(text1: str, text2: str) -> int:
    """Calculate word-level Levenshtein distance between two texts.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Word-level edit distance
    """
    words1 = text1.split()
    words2 = text2.split()

    m, n = len(words1), len(words2)

    # Create distance matrix
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Initialize base cases
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    # Fill the matrix
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if words1[i - 1] == words2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j],      # deletion
                                   dp[i][j - 1],      # insertion
                                   dp[i - 1][j - 1])  # substitution

    return dp[m][n]


def get_similar_texts(user_id: str, library_id: str, input_text: str, top_n: int = 3) -> List[str]:
    """Get top N most similar texts from a library using word-level Levenshtein.

    Args:
        user_id: User ID
        library_id: Library ID
        input_text: The text to compare against
        top_n: Number of top similar texts to return

    Returns:
        List of top N most similar text contents
    """
    from app.services.library import get_texts

    # Get all texts from the library
    library_texts = get_texts(user_id, library_id)

    if not library_texts:
        return []

    # Calculate distances and sort
    text_distances = []
    for text_obj in library_texts:
        distance = word_level_levenshtein(input_text, text_obj.content)
        # Normalize by length for fair comparison
        normalized_distance = distance / max(len(input_text.split()), len(text_obj.content.split()), 1)
        text_distances.append((normalized_distance, text_obj.content))

    # Sort by distance (ascending - smaller distance = more similar)
    text_distances.sort(key=lambda x: x[0])

    # Return top N texts
    return [text for _, text in text_distances[:top_n]]


def get_grammar_correction(
    text: str,
    context: Optional[str] = None,
    library_id: Optional[str] = None,
    user_id: Optional[str] = None,
    keep_writing_style: bool = False,
    preserve_formatting: bool = True,
    custom_instructions: Optional[str] = None,
    show_explanations: bool = False,
    multiple_outputs: int = 1
) -> dict:
    """Get grammar correction using Gemini AI."""

    # Base instruction to preserve formatting (optional)
    if preserve_formatting:
        format_preservation = "IMPORTANT: Preserve all original formatting including line breaks, paragraph structure, and spacing. Only fix grammar, spelling, and punctuation errors."
    else:
        format_preservation = ""

    if keep_writing_style:
        style_instruction = "Maintain the original writing style, tone, and voice. Only fix grammar and spelling errors."
    else:
        style_instruction = ""

    if custom_instructions:
        custom_instruction = f"Additional instructions: {custom_instructions}"
    else:
        custom_instruction = ""

    # Get similar texts from library if provided
    library_examples = ""
    if library_id and user_id:
        similar_texts = get_similar_texts(user_id, library_id, text, top_n=3)
        if similar_texts:
            library_examples = "\n\nReference examples of similar writing:\n"
            for i, example in enumerate(similar_texts, 1):
                library_examples += f"Example {i}: {example}\n"

    if multiple_outputs > 1:
        if show_explanations:
            format_instruction = f"""Provide exactly {multiple_outputs} different corrected versions as a JSON array.
Each element must have:
- "text": the corrected text
- "explanation": brief explanation of changes

Response format:
[
  {{"text": "corrected version 1", "explanation": "explanation 1"}},
  {{"text": "corrected version 2", "explanation": "explanation 2"}}
]
Only output the JSON array, nothing else."""
        else:
            format_instruction = f"""Provide exactly {multiple_outputs} different corrected versions as a JSON array.
Each element must have:
- "text": the corrected text

Response format:
[
  {{"text": "corrected version 1"}},
  {{"text": "corrected version 2"}}
]
Only output the JSON array, nothing else."""
    elif show_explanations:
        format_instruction = """Provide the corrected text as JSON with:
- "text": the corrected text
- "explanation": brief explanation of changes

Response format:
{"text": "corrected text", "explanation": "explanation"}
Only output the JSON object, nothing else."""
    else:
        format_instruction = """Provide only the corrected text as plain JSON.
Response format:
{"text": "corrected text"}
Only output the JSON object, nothing else."""

    # Build the prompt with all available context
    prompt_parts = ["Fix the grammar and spelling of the following text."]

    if format_preservation:
        prompt_parts.append(format_preservation)

    if library_examples:
        prompt_parts.append(library_examples)

    if context:
        prompt_parts.append(f"Use this context to improve the correction: {context}")

    if style_instruction:
        prompt_parts.append(style_instruction)

    if custom_instruction:
        prompt_parts.append(custom_instruction)

    prompt_parts.append(format_instruction)
    prompt_parts.append(f'\nOriginal text: """{text}"""')

    prompt = "\n\n".join(prompt_parts)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    result = response.text.strip()

    # Parse JSON response
    try:
        # Remove markdown code blocks if present
        result = result.strip()
        if result.startswith('```'):
            result = '\n'.join(result.split('\n')[1:-1])
            result = result.strip()
        # Remove json prefix if present
        if result.lower().startswith('json'):
            result = result[4:].strip()

        import json
        data = json.loads(result)

        if multiple_outputs > 1:
            outputs = []
            for item in data:
                if isinstance(item, dict):
                    text = item.get('text', '')
                    explanation = item.get('explanation')
                    outputs.append(GrammarOutput(text=text, explanation=explanation))
            return {"outputs": outputs}
        elif show_explanations:
            return {"corrected": data.get('text', result), "explanation": data.get('explanation')}
        else:
            return {"corrected": data.get('text', result)}
    except (json.JSONDecodeError, KeyError, TypeError):
        # Fallback to plain text if JSON parsing fails
        if multiple_outputs > 1 or show_explanations:
            return {"corrected": result, "error": "Failed to parse structured output"}
        else:
            return {"corrected": result}
