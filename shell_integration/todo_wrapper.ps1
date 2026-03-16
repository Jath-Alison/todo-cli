function todo {
    if ($args[0] -eq "cd") {
        if ($args.Count -gt 1) {
            # Capture the path from the CLI and any error output
            $errFile = New-TemporaryFile
            $taskDir = & (Get-Command todo -CommandType Application) cd $args[1..($args.Count-1)] 2>$errFile
            
            if ($LASTEXITCODE -eq 0 -and $taskDir) {
                Set-Location $taskDir
            } else {
                $errContent = Get-Content $errFile
                Write-Error $errContent
            }
            Remove-Item $errFile
        } else {
            # Handle 'todo cd' without ID (jump to todo list root)
            $todoFile = python -c "from todo.config import get_todo_path; print(get_todo_path())"
            if (Test-Path $todoFile) {
                $todoDir = Split-Path $todoFile
                Set-Location $todoDir
                Write-Host "Changed directory to $todoDir" -ForegroundColor Green
            } else {
                Write-Error "No .todo.yaml found."
            }
        }
    } else {
        # Pass all other commands to the actual todo-cli
        & (Get-Command todo -CommandType Application) $args
    }
}
