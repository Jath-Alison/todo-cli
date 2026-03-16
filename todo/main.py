import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path
from typing import Optional, List
import sys

from .models import Task, TaskList
from .storage import load_tasks, save_tasks, edit_notes
from .config import get_todo_path, get_global_todo_path

console = Console()

@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def cli():
    """
    \b
    Todo-CLI: A Git-style, directory-aware task manager.
    
    This tool allows you to manage tasks specific to your project directories
    while maintaining a global fallback. It stores tasks in '.todo.yaml'.
    """
    pass

@cli.command()
def init():
    """
    Initialize a local todo list in the current directory.
    
    This creates a '.todo.yaml' file, making this directory the root
    for all future 'todo' commands run within this subtree.
    """
    local_path = Path.cwd() / ".todo.yaml"
    if local_path.exists():
        console.print("[red]Local todo list already exists here.[/red]")
        return
    
    save_tasks(local_path, TaskList())
    console.print(f"[green]Initialized empty todo list at {local_path}[/green]")

@cli.command()
@click.argument("title", required=True)
@click.option("--priority", "-p", default="medium", type=click.Choice(["low", "medium", "high"]), help="Task priority level.")
@click.option("--tag", "-t", multiple=True, help="Add one or more tags (e.g., -t bug -t fix).")
@click.option("--notes", "-n", is_flag=True, help="Open your default editor to add detailed notes.")
def add(title, priority, tag, notes):
    """
    Add a new task to the current todo list.
    
    TITLE is the brief description of the task.
    """
    path = get_todo_path()
    task_list = load_tasks(path)
    
    new_id = 1
    if task_list.tasks:
        new_id = max(t.id for t in task_list.tasks) + 1
    
    task_notes = ""
    if notes:
        try:
            task_notes = edit_notes()
        except Exception as e:
            console.print(f"[red]Error opening editor:[/red] {e}")
            console.print("[yellow]Hint: Set your $EDITOR environment variable (e.g., to 'code' or 'vim').[/yellow]")
    
    new_task = Task(
        id=new_id,
        title=title,
        priority=priority,
        tags=list(tag),
        notes=task_notes,
        status="pending"
    )
    
    task_list.tasks.append(new_task)
    save_tasks(path, task_list)
    console.print(f"[green]Task #{new_id} added successfully to {path.name}.[/green]")

@cli.command(name="list")
@click.option("--all", "-a", is_flag=True, help="Include completed tasks in the output.")
@click.option("--tag", "-t", help="Filter tasks by a specific tag.")
def list_tasks(all, tag):
    """
    Display tasks from the current list.
    
    By default, it only shows 'pending' tasks.
    """
    path = get_todo_path()
    task_list = load_tasks(path)
    
    filtered_tasks = task_list.tasks
    if not all:
        filtered_tasks = [t for t in filtered_tasks if t.status == "pending"]
    
    if tag:
        filtered_tasks = [t for t in filtered_tasks if tag in t.tags]
        
    if not filtered_tasks:
        console.print(f"[yellow]No tasks found in {path.name}.[/yellow]")
        return

    table = Table(title=f"Tasks for {path.parent.name} ({path.name})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Priority", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Tags", style="blue")

    for task in filtered_tasks:
        status_color = "green" if task.status == "completed" else "yellow"
        table.add_row(
            str(task.id),
            task.title,
            task.priority,
            f"[{status_color}]{task.status}[/{status_color}]",
            ", ".join(task.tags)
        )

    console.print(table)

@cli.command()
@click.argument("id", type=int)
def open(id):
    """
    Edit notes for a specific task using your default editor.
    """
    path = get_todo_path()
    task_list = load_tasks(path)
    
    task = next((t for t in task_list.tasks if t.id == id), None)
    if not task:
        console.print(f"[red]Task #{id} not found.[/red]")
        return
    
    try:
        new_notes = edit_notes(task.notes)
        task.notes = new_notes
        save_tasks(path, task_list)
        console.print(f"[green]Notes for task #{id} updated.[/green]")
    except Exception as e:
        console.print(f"[red]Error opening editor:[/red] {e}")

@cli.command()
@click.argument("id", type=int)
def bump(id):
    """
    Mark a task as 'completed'.
    """
    path = get_todo_path()
    task_list = load_tasks(path)
    
    task = next((t for t in task_list.tasks if t.id == id), None)
    if not task:
        console.print(f"[red]Task #{id} not found.[/red]")
        return
    
    task.status = "completed"
    save_tasks(path, task_list)
    console.print(f"[green]Task #{id} bumped (marked as completed).[/green]")

@cli.command()
def status():
    """
    Show information about the current todo environment.
    """
    path = get_todo_path()
    global_path = get_global_todo_path()
    task_list = load_tasks(path)
    
    pending = len([t for t in task_list.tasks if t.status == "pending"])
    completed = len([t for t in task_list.tasks if t.status == "completed"])
    
    status_text = (
        f"[bold]Active File:[/bold] {path}\n"
        f"[bold]Global File:[/bold] {global_path}\n\n"
        f"[bold]Summary:[/bold]\n"
        f"  - Pending:   {pending}\n"
        f"  - Completed: {completed}\n"
        f"  - Total:     {len(task_list.tasks)}"
    )
    
    console.print(Panel(status_text, title="Todo CLI Status", expand=False))

# For package entry point
app = cli

if __name__ == "__main__":
    cli()
