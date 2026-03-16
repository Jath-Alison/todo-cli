#!/bin/bash

# todo wrapper function to handle 'todo cd'
todo() {
    if [[ "$1" == "cd" ]]; then
        # This is a command that finds the root of the todo list
        local todo_file=$(python -c "from todo.config import get_todo_path; print(get_todo_path())" 2>/dev/null)
        if [[ -f "$todo_file" ]]; then
            local todo_dir=$(dirname "$todo_file")
            cd "$todo_dir"
            echo "Changed directory to $todo_dir"
        else
            echo "No .todo.yaml found."
        fi
    else
        # Pass all other commands to the actual todo-cli
        # If installed via 'pip install -e .', the 'todo' command will be available
        command todo "$@"
    fi
}
