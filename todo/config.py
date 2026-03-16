from pathlib import Path
import os

def get_todo_path() -> Path:
    # Check current directory
    local_todo = Path.cwd() / ".todo.yaml"
    if local_todo.exists():
        return local_todo
    
    # Check parent directories for a .todo.yaml (like git)
    for parent in Path.cwd().parents:
        if (parent / ".todo.yaml").exists():
            return parent / ".todo.yaml"

    # Default to global list if nothing found
    return get_global_todo_path()

def get_global_todo_path() -> Path:
    # Use user's home directory for global todo list
    global_todo = Path.home() / ".todo.yaml"
    return global_todo
