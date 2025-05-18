# Enhanced debugging for natural language terminal script
param(
    [string]$PythonPath = "python",
    [string]$ControllerPath = "C:\Users\Nilay\Desktop\terminal-controller-mcp\terminal_controller.py"
)

# Enable verbose output
$VerbosePreference = "Continue"

function Start-TerminalServer {
    param(
        [string]$PythonPath = "python",
        [string]$ControllerPath = "C:\Users\Nilay\Desktop\terminal-controller-mcp\terminal_controller.py"
    )
    
    Write-Host "Starting Terminal Controller server..." -ForegroundColor Cyan
    
    # Start the Python script using Start-Process which works in constrained mode
    Start-Process -FilePath $PythonPath -ArgumentList "$ControllerPath --http" -NoNewWindow
    
    # Give the server a moment to start
    Start-Sleep -Seconds 2
    
    # Test the server with a direct command
    $testResult = Invoke-TerminalCommand -Command "echo 'Server test'"
    Write-Host "Server test result: $testResult" -ForegroundColor Gray
    
    Write-Host "Terminal server started!" -ForegroundColor Green
}

function Invoke-TerminalCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,
        
        [int]$Timeout = 30
    )
    
    Write-Verbose "Executing command: $Command"
    
    $requestData = @{
        jsonrpc = "2.0"
        method = "execute_command"
        params = @{
            command = $Command
            timeout = $Timeout
        }
        id = (Get-Random -Minimum 1000 -Maximum 9999)
    } | ConvertTo-Json
    
    Write-Verbose "Request data: $requestData"
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/jsonrpc" -Method Post -Body $requestData -ContentType "application/json"
        Write-Verbose "Response received successfully"
        return $response.result
    }
    catch {
        Write-Host "Error executing command: $_" -ForegroundColor Red
        Write-Verbose "Full error details: $($_ | Format-List -Force | Out-String)"
        throw $_
    }
}

function ConvertTo-Command {
    param(
        [Parameter(Mandatory = $true)]
        [string]$NaturalLanguagePrompt
    )
    
    Write-Verbose "Converting natural language to command: '$NaturalLanguagePrompt'"
    
    # Simple pattern matching for common tasks
    $prompt = $NaturalLanguagePrompt.ToLower()
    $command = $null
    
    Write-Verbose "Checking built-in patterns..."
    
    if ($prompt -match "list (files|directory)") {
        $command = "dir"
    }
    elseif ($prompt -match "show (current )?directory") {
        $command = "pwd"
    }
    elseif ($prompt -match "what('s| is) in (this folder|directory|here)") {
        $command = "dir"
    }
    elseif ($prompt -match "create (a )?folder (?<name>\w+)") {
        $command = "mkdir $($Matches.name)"
    }
    elseif ($prompt -match "delete (file|folder) (?<name>[\w\.]+)") {
        $command = "del $($Matches.name)"
    }
    elseif ($prompt -match "show file (?<name>[\w\.]+)") {
        $command = "type $($Matches.name)"
    }
    elseif ($prompt -match "ping (?<host>[\w\.]+)") {
        $command = "ping $($Matches.host)"
    }
    elseif ($prompt -match "system (info|information)") {
        $command = "systeminfo"
    }
    elseif ($prompt -match "network connections") {
        $command = "netstat -ano"
    }
    elseif ($prompt -match "processes") {
        $command = "tasklist"
    }
    
    if ($command) {
        Write-Verbose "Matched built-in pattern, command: $command"
        return $command
    }
    
    Write-Verbose "No built-in pattern matched, trying server translation..."
    
    # Try to get a command from the server
    try {
        $requestData = @{
            jsonrpc = "2.0"
            method = "convert_natural_language"
            params = @{
                prompt = $NaturalLanguagePrompt
            }
            id = (Get-Random -Minimum 1000 -Maximum 9999)
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "http://localhost:8000/jsonrpc" -Method Post -Body $requestData -ContentType "application/json"
        
        if ($response.result -and $response.result -ne "Could not translate") {
            Write-Verbose "Server translated command: $($response.result)"
            return $response.result
        }
    }
    catch {
        Write-Verbose "Error using server translation: $_"
    }
    
    # Last resort - basic verb extraction
    Write-Verbose "Trying basic verb extraction..."
    $words = $prompt -split '\s+'
    $commonVerbs = @("list", "show", "get", "find", "search", "create", "make", "delete", "remove")
    
    foreach ($verb in $commonVerbs) {
        if ($words -contains $verb) {
            if ($verb -eq "list" -or $verb -eq "show") {
                Write-Verbose "Basic verb matched: $verb - returning dir command"
                return "dir"
            }
        }
    }
    
    # If all else fails, just try the prompt as a command
    Write-Verbose "All translation methods failed, using input as direct command"
    return $NaturalLanguagePrompt
}

function Start-NaturalLanguageShell {
    # Start the terminal server
    Start-TerminalServer -PythonPath $PythonPath -ControllerPath $ControllerPath
    
    # Test direct command execution
    Write-Host "Testing direct command execution:" -ForegroundColor Cyan
    $testResult = Invoke-TerminalCommand -Command "dir"
    Write-Host "Test successful!" -ForegroundColor Green
    
    Write-Host "Natural Language Terminal Shell" -ForegroundColor Green
    Write-Host "Type your commands in plain English or 'exit' to quit" -ForegroundColor Cyan
    Write-Host "-----------------------------------------" -ForegroundColor Gray
    
    $running = $true
    
    while ($running) {
        Write-Host "NL>" -ForegroundColor Green -NoNewline
        $userInput = Read-Host
        
        Write-Verbose "User input: '$userInput'"
        
        if ($userInput -eq "exit") {
            $running = $false
            continue
        }
        
        if ([string]::IsNullOrWhiteSpace($userInput)) {
            Write-Host "Please enter a command" -ForegroundColor Yellow
            continue
        }
        
        try {
            Write-Verbose "Calling ConvertTo-Command..."
            $command = ConvertTo-Command -NaturalLanguagePrompt $userInput
            
            if ($command) {
                Write-Host "Executing: $command" -ForegroundColor Yellow
                $result = Invoke-TerminalCommand -Command $command
                Write-Host $result
            }
            else {
                Write-Host "Could not interpret the command. Try something simpler." -ForegroundColor Red
            }
        }
        catch {
            Write-Host "Error processing command: $_" -ForegroundColor Red
            Write-Verbose "Full error details: $($_ | Format-List -Force | Out-String)"
        }
        
        Write-Host "-----------------------------------------" -ForegroundColor Gray
    }
    
    Write-Host "Shell closed. Server still running." -ForegroundColor Yellow
}

# Execute the main function
Start-NaturalLanguageShell