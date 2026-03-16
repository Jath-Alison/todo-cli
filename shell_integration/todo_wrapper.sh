#!/bin/bash

# todo wrapper function to handle 'todo cd'
todo() {
    if [[ "$1" == "cd" ]]; then
        if [[ -n "$2" ]]; then
            # 'todo cd <id>' - get the task location and cd to it
            # Strip trailing carriage returns (^M) from the output
            local task_dir=$(command todo cd "$2" 2>/tmp/todo_err | tr -d '\r')
            if [[ $? -eq 0 && -n "$task_dir" ]]; then
                cd "$task_dir"
            else
                cat /tmp/todo_err | tr -d '\r' >&2
                return 1
            fi
        else
            # 'todo cd' (no id) - cd to the root of the current todo list
            local todo_file=$(python -c "from todo.config import get_todo_path; print(get_todo_path())" 2>/dev/null | tr -d '\r')
            if [[ -f "$todo_file" ]]; then
                local todo_dir=$(dirname "$todo_file")
                cd "$todo_dir"
                echo "Changed directory to $todo_dir"
            else
                echo "No .todo.yaml found." >&2
                return 1
            fi
        fi
    else
        # Pass all other commands to the actual todo-cli
        command todo "$@"
    fi
}
