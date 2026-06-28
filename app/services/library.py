"""Library management service."""
import json
import uuid
from datetime import datetime
from typing import Optional
from app.config import CREDENTIALS_FILE
from app.models import Library, Text


def get_library_file_path(user_id: str) -> str:
    """Get the library file path for a user."""
    import os
    # Get the directory of the credentials file
    creds_dir = os.path.dirname(CREDENTIALS_FILE)
    return os.path.join(creds_dir, f"library_{user_id}.json")


def load_user_library_data(user_id: str) -> dict:
    """Load library data for a user."""
    file_path = get_library_file_path(user_id)
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return empty structure if file doesn't exist
        return {"libraries": [], "texts": []}
    except json.JSONDecodeError:
        return {"libraries": [], "texts": []}


def save_user_library_data(user_id: str, data: dict):
    """Save library data for a user."""
    file_path = get_library_file_path(user_id)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)


def get_libraries(user_id: str) -> list[Library]:
    """Get all libraries for a user."""
    data = load_user_library_data(user_id)
    libraries = []

    for lib_data in data.get("libraries", []):
        # Count texts in this library
        text_count = sum(1 for text in data.get("texts", []) if text.get("library_id") == lib_data.get("id"))

        libraries.append(Library(
            id=lib_data.get("id"),
            name=lib_data.get("name"),
            description=lib_data.get("description", ""),
            created_at=lib_data.get("created_at"),
            updated_at=lib_data.get("updated_at"),
            text_count=text_count
        ))

    return libraries


def create_library(user_id: str, name: str, description: str) -> Library:
    """Create a new library for a user."""
    data = load_user_library_data(user_id)

    now = datetime.utcnow().isoformat()
    library_id = str(uuid.uuid4())

    new_library = {
        "id": library_id,
        "name": name,
        "description": description,
        "created_at": now,
        "updated_at": now
    }

    data["libraries"].append(new_library)
    save_user_library_data(user_id, data)

    return Library(
        id=library_id,
        name=name,
        description=description,
        created_at=now,
        updated_at=now,
        text_count=0
    )


def update_library(user_id: str, library_id: str, name: str, description: str) -> Optional[Library]:
    """Update a library."""
    data = load_user_library_data(user_id)

    for lib in data.get("libraries", []):
        if lib.get("id") == library_id:
            lib["name"] = name
            lib["description"] = description
            lib["updated_at"] = datetime.utcnow().isoformat()

            # Count texts in this library
            text_count = sum(1 for text in data.get("texts", []) if text.get("library_id") == library_id)

            save_user_library_data(user_id, data)

            return Library(
                id=library_id,
                name=name,
                description=description,
                created_at=lib.get("created_at"),
                updated_at=lib.get("updated_at"),
                text_count=text_count
            )

    return None


def delete_library(user_id: str, library_id: str) -> bool:
    """Delete a library and all its texts."""
    data = load_user_library_data(user_id)

    # Remove the library
    original_lib_count = len(data.get("libraries", []))
    data["libraries"] = [lib for lib in data.get("libraries", []) if lib.get("id") != library_id]

    # Remove all texts in this library
    data["texts"] = [text for text in data.get("texts", []) if text.get("library_id") != library_id]

    if len(data.get("libraries", [])) < original_lib_count:
        save_user_library_data(user_id, data)
        return True

    return False


def get_texts(user_id: str, library_id: str) -> list[Text]:
    """Get all texts in a library."""
    data = load_user_library_data(user_id)
    texts = []

    for text_data in data.get("texts", []):
        if text_data.get("library_id") == library_id:
            texts.append(Text(
                id=text_data.get("id"),
                library_id=text_data.get("library_id"),
                content=text_data.get("content"),
                created_at=text_data.get("created_at"),
                updated_at=text_data.get("updated_at")
            ))

    return texts


def create_text(user_id: str, library_id: str, content: str) -> Optional[Text]:
    """Create a new text in a library."""
    data = load_user_library_data(user_id)

    # Verify library exists
    library_exists = any(lib.get("id") == library_id for lib in data.get("libraries", []))
    if not library_exists:
        return None

    now = datetime.utcnow().isoformat()
    text_id = str(uuid.uuid4())

    new_text = {
        "id": text_id,
        "library_id": library_id,
        "content": content,
        "created_at": now,
        "updated_at": now
    }

    data["texts"].append(new_text)
    save_user_library_data(user_id, data)

    return Text(
        id=text_id,
        library_id=library_id,
        content=content,
        created_at=now,
        updated_at=now
    )


def update_text(user_id: str, text_id: str, content: str) -> Optional[Text]:
    """Update a text."""
    data = load_user_library_data(user_id)

    for text in data.get("texts", []):
        if text.get("id") == text_id:
            text["content"] = content
            text["updated_at"] = datetime.utcnow().isoformat()

            save_user_library_data(user_id, data)

            return Text(
                id=text_id,
                library_id=text.get("library_id"),
                content=content,
                created_at=text.get("created_at"),
                updated_at=text.get("updated_at")
            )

    return None


def delete_text(user_id: str, text_id: str) -> bool:
    """Delete a text."""
    data = load_user_library_data(user_id)

    original_count = len(data.get("texts", []))
    data["texts"] = [text for text in data.get("texts", []) if text.get("id") != text_id]

    if len(data.get("texts", [])) < original_count:
        save_user_library_data(user_id, data)
        return True

    return False


def export_library(user_id: str, library_id: str) -> Optional[dict]:
    """Export a library with all its texts as a dictionary."""
    data = load_user_library_data(user_id)

    # Find the library
    library = None
    for lib in data.get("libraries", []):
        if lib.get("id") == library_id:
            library = lib
            break

    if not library:
        return None

    # Get all texts in this library
    texts = [text for text in data.get("texts", []) if text.get("library_id") == library_id]

    return {
        "library": library,
        "texts": texts
    }


def import_library(user_id: str, import_data: dict, target_library_id: Optional[str] = None, merge_strategy: str = "merge") -> Optional[Library]:
    """Import a library from exported data.

    Args:
        user_id: User ID
        import_data: Dictionary with 'library' and 'texts' keys
        target_library_id: If provided, overwrite this library. If None, create new.
        merge_strategy: 'replace' to delete existing texts, 'merge' to keep them

    Returns:
        The imported Library object or None on failure
    """
    # Validate import data structure
    if "library" not in import_data or "texts" not in import_data:
        return None

    library_data = import_data["library"]
    texts_data = import_data["texts"]

    data = load_user_library_data(user_id)

    if target_library_id:
        # Overwrite existing library
        target_lib = None
        for lib in data["libraries"]:
            if lib["id"] == target_library_id:
                target_lib = lib
                break

        if not target_lib:
            return None

        # Update library metadata
        target_lib["name"] = library_data.get("name", "Imported Library")
        target_lib["description"] = library_data.get("description", "")
        target_lib["updated_at"] = datetime.utcnow().isoformat()

        library_id = target_library_id
    else:
        # Create new library
        now = datetime.utcnow().isoformat()
        library_id = str(uuid.uuid4())

        new_library = {
            "id": library_id,
            "name": library_data.get("name", "Imported Library"),
            "description": library_data.get("description", ""),
            "created_at": now,
            "updated_at": now
        }

        data["libraries"].append(new_library)

    # Handle texts based on merge strategy
    if merge_strategy == "replace":
        # Remove all existing texts in this library
        data["texts"] = [t for t in data["texts"] if t.get("library_id") != library_id]
    # else: merge - keep existing texts

    # Add imported texts with new IDs and correct library_id
    existing_contents = {t.get("content") for t in data.get("texts", []) if t.get("library_id") == library_id}

    for text_data in texts_data:
        # Skip if content already exists (avoid duplicates when merging)
        if merge_strategy == "merge" and text_data.get("content") in existing_contents:
            continue

        now = datetime.utcnow().isoformat()
        text_id = str(uuid.uuid4())

        new_text = {
            "id": text_id,
            "library_id": library_id,
            "content": text_data.get("content"),
            "created_at": now,
            "updated_at": now
        }

        data["texts"].append(new_text)
        existing_contents.add(text_data.get("content"))

    save_user_library_data(user_id, data)

    # Return the library
    final_lib = None
    for lib in data["libraries"]:
        if lib["id"] == library_id:
            text_count = sum(1 for t in data.get("texts", []) if t.get("library_id") == library_id)
            final_lib = Library(
                id=lib["id"],
                name=lib["name"],
                description=lib["description"],
                created_at=lib["created_at"],
                updated_at=lib["updated_at"],
                text_count=text_count
            )
            break

    return final_lib
