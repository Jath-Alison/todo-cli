import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta
import sys

from .models import Task, TaskList
from .storage import load_tasks, save_tasks, edit_notes
from .config import get_todo_path, get_global_todo_path

console = Console()
err_console = Console(stderr=True)

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
@click.option("--location", "-l", help="Specify a custom location/path for this task.")
@click.option("--global", "-g", "is_global", is_flag=True, help="Add task to the global list.")
def add(title, priority, tag, notes, location, is_global):
    """
    Add a new task to the todo list.
    
    TITLE is the brief description of the task.
    """
    path = get_global_todo_path() if is_global else get_todo_path()
    task_list = load_tasks(path)
    
    new_id = 1
    if task_list.tasks:
        new_id = max(t.id for t in task_list.tasks) + 1
    
    task_notes = ""
    if notes:
        try:
            task_notes = edit_notes()
        except Exception as e:
            err_console.print(f"[red]Error opening editor:[/red] {e}")
            err_console.print("[yellow]Hint: Set your $EDITOR environment variable (e.g., to 'code' or 'vim').[/yellow]")
    
    # Default location to None if not provided
    task_location = location
    
    new_task = Task(
        id=new_id,
        title=title,
        priority=priority,
        tags=list(tag),
        notes=task_notes,
        status="pending",
        location=task_location,
        created_at=datetime.now(),
        last_worked_at=datetime.now()
    )
    
    task_list.tasks.append(new_task)
    save_tasks(path, task_list)
    console.print(f"[green]Task #{new_id} added successfully to {path.name}.[/green]")

@cli.command(name="list")
@click.option("--all", "-a", is_flag=True, help="Include completed tasks in the output.")
@click.option("--tag", "-t", help="Filter tasks by a specific tag.")
@click.option("--sort", "-s", type=click.Choice(["created", "worked", "priority"]), default="worked", help="Sort tasks.")
@click.option("--stale", is_flag=True, help="Show tasks that haven't been worked on in 7+ days.")
@click.option("--global", "-g", "is_global", is_flag=True, help="List tasks from the global list.")
def list_tasks(all, tag, sort, stale, is_global):
    """
    Display tasks from the todo list.
    
    By default, it only shows 'pending' tasks and sorts by last worked on.
    """
    path = get_global_todo_path() if is_global else get_todo_path()
    task_list = load_tasks(path)
    
    filtered_tasks = task_list.tasks
    if not all:
        filtered_tasks = [t for t in filtered_tasks if t.status == "pending"]
    
    if tag:
        filtered_tasks = [t for t in filtered_tasks if tag in t.tags]
    
    if stale:
        seven_days_ago = datetime.now() - timedelta(days=7)
        filtered_tasks = [t for t in filtered_tasks if t.last_worked_at < seven_days_ago]
        
    if not filtered_tasks:
        console.print(f"[yellow]No tasks found in {path.name}.[/yellow]")
        return

    # Sort tasks
    priority_map = {"high": 0, "medium": 1, "low": 2}
    if sort == "created":
        filtered_tasks.sort(key=lambda x: x.created_at, reverse=True)
    elif sort == "worked":
        filtered_tasks.sort(key=lambda x: x.last_worked_at, reverse=True)
    elif sort == "priority":
        filtered_tasks.sort(key=lambda x: priority_map.get(x.priority, 1))

    table = Table(title=f"Tasks for {path.parent.name} ({path.name})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Priority", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Worked On", style="yellow")
    table.add_column("Tags", style="blue")

    for task in filtered_tasks:
        status_color = "green" if task.status == "completed" else "yellow"
        
        # Format "last worked on" relative time or date
        worked_on_str = task.last_worked_at.strftime("%Y-%m-%d")
        
        table.add_row(
            str(task.id),
            task.title,
            task.priority,
            f"[{status_color}]{task.status}[/{status_color}]",
            worked_on_str,
            ", ".join(task.tags)
        )

    console.print(table)

@cli.command()
@click.argument("id", type=int)
@click.option("--title", help="New title for the task.")
@click.option("--priority", "-p", type=click.Choice(["low", "medium", "high"]), help="New priority level.")
@click.option("--tag", "-t", "tags", multiple=True, help="New tags (replaces existing tags).")
@click.option("--location", "-l", help="New location path.")
@click.option("--global", "-g", "is_global", is_flag=True, help="Edit task in the global list.")
def edit(id, title, priority, tags, location, is_global):
    """
    Modify an existing task's properties.
    """
    path = get_global_todo_path() if is_global else get_todo_path()
    task_list = load_tasks(path)
    
    task = next((t for t in task_list.tasks if t.id == id), None)
    if not task:
        err_console.print(f"[red]Task #{id} not found in {path.name}.[/red]")
        return

    updated = False
    if title:
        task.title = title
        updated = True
    if priority:
        task.priority = priority
        updated = True
    if tags:
        task.tags = list(tags)
        updated = True
    if location:
        task.location = location
        updated = True
        
    if updated:
        task.last_worked_at = datetime.now()
        save_tasks(path, task_list)
        console.print(f"[green]Task #{id} updated in {path.name}.[/green]")
    else:
        console.print(f"[yellow]No changes specified for task #{id}.[/yellow]")

@cli.command()
@click.argument("id", type=int)
@click.option("--global", "-g", "is_global", is_flag=True, help="Open task from the global list.")
def open(id, is_global):
    """
    Edit notes for a specific task using your default editor.
    """
    path = get_global_todo_path() if is_global else get_todo_path()
    task_list = load_tasks(path)
    
    task = next((t for t in task_list.tasks if t.id == id), None)
    if not task:
        err_console.print(f"[red]Task #{id} not found.[/red]")
        return
    
    try:
        new_notes = edit_notes(task.notes)
        task.notes = new_notes
        task.last_worked_at = datetime.now()
        save_tasks(path, task_list)
        console.print(f"[green]Notes for task #{id} updated and task bumped.[/green]")
    except Exception as e:
        err_console.print(f"[red]Error opening editor:[/red] {e}")

@cli.command()
@click.argument("id", type=int)
@click.option("--global", "-g", "is_global", is_flag=True, help="Bump task in the global list.")
def bump(id, is_global):
    """
    Update a task's 'last worked on' timestamp.
    """
    path = get_global_todo_path() if is_global else get_todo_path()
    task_list = load_tasks(path)
    
    task = next((t for t in task_list.tasks if t.id == id), None)
    if not task:
        err_console.print(f"[red]Task #{id} not found.[/red]")
        return
    
    task.last_worked_at = datetime.now()
    save_tasks(path, task_list)
    console.print(f"[green]Task #{id} bumped (last worked on time updated).[/green]")

@cli.command()
@click.argument("id", type=int)
@click.option("--global", "-g", "is_global", is_flag=True, help="Mark task as done in the global list.")
def done(id, is_global):
    """
    Mark a task as 'completed'.
    """
    path = get_global_todo_path() if is_global else get_todo_path()
    task_list = load_tasks(path)
    
    task = next((t for t in task_list.tasks if t.id == id), None)
    if not task:
        err_console.print(f"[red]Task #{id} not found.[/red]")
        return
    
    task.status = "completed"
    task.last_worked_at = datetime.now()
    save_tasks(path, task_list)
    console.print(f"[green]Task #{id} marked as completed.[/green]")

@cli.command()
@click.argument("id", type=int)
@click.option("--global", "-g", "is_global", is_flag=True, help="Get location from the global list.")
def cd(id, is_global):
    """
    Output the location of a task for the shell wrapper.
    """
    path = get_global_todo_path() if is_global else get_todo_path()
    task_list = load_tasks(path)
    
    task = next((t for t in task_list.tasks if t.id == id), None)
    if not task:
        err_console.print(f"[red]Task #{id} not found.[/red]")
        sys.exit(1)
    
    if not task.location:
        err_console.print(f"[red]Task #{id} has no location specified.[/red]")
        sys.exit(1)
    
    # Just print the location to stdout for the wrapper
    print(task.location)

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
