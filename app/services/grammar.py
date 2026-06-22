"""Grammar correction service using Gemini AI."""
from typing import Optional
from google import genai
from app.models import GrammarOutput
from app.config import GEMINI_API_KEY


client = genai.Client(api_key=GEMINI_API_KEY)


def get_grammar_correction(
    text: str,
    context: Optional[str] = None,
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

    if context:
        prompt = f"""Fix the grammar and spelling of the following text.
{format_preservation}
Use this context to improve the correction: {context}
{style_instruction}
{custom_instruction}

{format_instruction}

Original text: \"\"\"{text}\"\"\""""
    else:
        prompt = f"""Fix the grammar and spelling of the following text.
{format_preservation}
{style_instruction}
{custom_instruction}

{format_instruction}

Original text: \"\"\"{text}\"\"\""""

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
