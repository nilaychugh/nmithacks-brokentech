param(
    [string]$PythonPath = "python",
    [string]$ControllerPath = "C:\Users\Nilay\Desktop\terminal-controller-mcp\term_control.py",
    [string]$ClientPath = "C:\Users\Nilay\Desktop\terminal-controller-mcp\nl_client.py"
)

function Start-TerminalServer {
    # Start the server in a separate process
    $process = Start-Process -FilePath $PythonPath -ArgumentList $ControllerPath -PassThru -NoNewWindow
    Start-Sleep -Seconds 2
    return $process
}

function Start-NaturalLanguageShell {
    # Start the terminal server
    $serverProcess = Start-TerminalServer -PythonPath $PythonPath -ControllerPath $ControllerPath
    
    Write-Host "`nNatural Language Terminal Shell" -ForegroundColor Green
    Write-Host "Type your commands in plain English or 'exit' to quit" -ForegroundColor Cyan
    Write-Host "-----------------------------------------" -ForegroundColor DarkGray
    
    $running = $true
    
    while ($running) {
        Write-Host "NL>" -ForegroundColor Green -NoNewline
        $userInput = Read-Host
        
        if ($userInput -eq "exit") {
            $running = $false
            continue
        }
        
        if ([string]::IsNullOrWhiteSpace($userInput)) {
            Write-Host "Please enter a command" -ForegroundColor Yellow
            continue
        }
        
        try {
            # Use the Python client to communicate with the server
            $clientOutput = & $PythonPath $ClientPath $userInput
            Write-Host $clientOutput
        }
        catch {
            Write-Host "Error: $_" -ForegroundColor Red
        }
        
        Write-Host "-----------------------------------------" -ForegroundColor DarkGray
    }
    
    # Stop the server when we're done
    if (!$serverProcess.HasExited) {
        Stop-Process -Id $serverProcess.Id -Force
    }
    
    Write-Host "Shell closed" -ForegroundColor Yellow
}

# Execute the main function
Start-NaturalLanguageShell