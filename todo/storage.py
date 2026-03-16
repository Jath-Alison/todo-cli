import yaml
import os
from pathlib import Path
from typing import Optional
import click
from .models import TaskList

def load_tasks(path: Path) -> TaskList:
    if not path.exists():
        return TaskList(tasks=[])
    
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    
    if data is None:
        return TaskList(tasks=[])
        
    return TaskList(**data)

def save_tasks(path: Path, tasks: TaskList):
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Dump model to dict, then save to yaml
    # use exclude_none=True to keep yaml clean
    data = tasks.model_dump(exclude_none=True)
    
    # We want to format the datetime in a readable way
    # yaml.safe_dump handles some datetime objects, but we can do it ourselves if needed
    with open(path, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)

def edit_notes(initial_content: str = "") -> str:
    # Use click's built-in editor utility
    # which respects $EDITOR
    edited_content = click.edit(initial_content)
    return edited_content.strip() if edited_content else initial_content
