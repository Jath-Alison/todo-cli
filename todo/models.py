from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class Task(BaseModel):
    id: int
    title: str
    priority: str = "medium"
    tags: List[str] = []
    due_date: Optional[datetime] = None
    notes: str = ""
    status: str = "pending"  # "pending", "completed"

class TaskList(BaseModel):
    tasks: List[Task] = []
