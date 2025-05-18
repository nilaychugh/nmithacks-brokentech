# Import required modules
using namespace System.Net.Http
using namespace System.Text

# Global variables
$script:ServerUrl = "http://localhost:8000/jsonrpc"
$script:NlpEnabled = $true
$script:TerminalProcess = $null

function Start-TerminalServer {
    [CmdletBinding()]
    param(
        [Parameter()]
        [string]$PythonPath = "python",
        
        [Parameter()]
        [string]$ControllerPath = "terminal_controller.py"
    )
    
    Write-Host "Starting Terminal Controller server..." -ForegroundColor Cyan
    
    # Check if server is already running
    if ($script:TerminalProcess -ne $null -and !$script:TerminalProcess.HasExited) {
        Write-Host "Terminal server is already running." -ForegroundColor Green
        return
    }
    
    # Start the server process
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $PythonPath
    $startInfo.Arguments = "$ControllerPath --http"
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $false
    
    $script:TerminalProcess = [System.Diagnostics.Process]::Start($startInfo)
    
    # Give the server a moment to start
    Start-Sleep -Seconds 2
    
    # Check if server is running by sending a test request
    try {
        $result = Invoke-TerminalCommand -Command "echo 'Server test'"
        Write-Host "Terminal server started successfully!" -ForegroundColor Green
    }
    catch {
        Write-Host "Failed to start server: $_" -ForegroundColor Red
    }
}

function Stop-TerminalServer {
    [CmdletBinding()]
    param()
    
    if ($script:TerminalProcess -ne $null -and !$script:TerminalProcess.HasExited) {
        Write-Host "Stopping Terminal Controller server..." -ForegroundColor Cyan
        $script:TerminalProcess.Kill()
        $script:TerminalProcess = $null
        Write-Host "Server stopped." -ForegroundColor Green
    }
    else {
        Write-Host "Server is not running." -ForegroundColor Yellow
    }
}

function Invoke-TerminalCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$Command,
        
        [Parameter()]
        [int]$Timeout = 30
    )
    
    $client = New-Object HttpClient
    $client.Timeout = [TimeSpan]::FromSeconds(60)
    
    $requestData = @{
        jsonrpc = "2.0"
        method = "execute_command"
        params = @{
            command = $Command
            timeout = $Timeout
        }
        id = Get-Random -Minimum 1000 -Maximum 9999
    } | ConvertTo-Json
    
    try {
        $content = New-Object StringContent($requestData, [Encoding]::UTF8, "application/json")
        $response = $client.PostAsync($script:ServerUrl, $content).Result
        
        if (!$response.IsSuccessStatusCode) {
            throw "HTTP Error: $($response.StatusCode) - $($response.ReasonPhrase)"
        }
        
        $responseContent = $response.Content.ReadAsStringAsync().Result
        $result = $responseContent | ConvertFrom-Json
        
        if ($result.error) {
            throw "API Error: $($result.error.message)"
        }
        
        return $result.result
    }
    catch {
        Write-Host "Error executing command: $_" -ForegroundColor Red
        throw $_
    }
    finally {
        $client.Dispose()
    }
}

function Invoke-NaturalLanguageCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0, ValueFromPipeline = $true)]
        [string]$NaturalLanguagePrompt
    )
    
    Write-Host "Processing: '$NaturalLanguagePrompt'" -ForegroundColor Cyan
    
    # Use OpenAI or a similar service to translate natural language to a command
    $command = ConvertTo-Command -NaturalLanguagePrompt $NaturalLanguagePrompt
    
    if ($command) {
        Write-Host "Executing: $command" -ForegroundColor Yellow
        $result = Invoke-TerminalCommand -Command $command
        return $result
    }
    else {
        Write-Host "Could not interpret the natural language command." -ForegroundColor Red
    }
}

function ConvertTo-Command {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$NaturalLanguagePrompt
    )
    
    # This function converts natural language to commands
    # Here we use a simple pattern matching approach 
    # In a production environment, you would use an LLM API

    # Simple pattern matching for common tasks
    switch -Regex ($NaturalLanguagePrompt.ToLower()) {
        "list (files|directory)" { return "dir" }
        "show (current )?directory" { return "pwd" }
        "what('s| is) in (this folder|directory|here)" { return "dir" }
        "create (a )?folder (?<name>\w+)" { return "mkdir $($Matches.name)" }
        "delete (file|folder) (?<name>[\w\.]+)" { return "del $($Matches.name)" }
        "show file (?<name>[\w\.]+)" { return "type $($Matches.name)" }
        "ping (?<host>[\w\.]+)" { return "ping $($Matches.host)" }
        "copy (?<source>[\w\.]+) to (?<dest>[\w\.]+)" { return "copy $($Matches.source) $($Matches.dest)" }
        "move (?<source>[\w\.]+) to (?<dest>[\w\.]+)" { return "move $($Matches.source) $($Matches.dest)" }
        "search for (?<text>[\w\.]+)" { return "findstr $($Matches.text) *" }
        "system (info|information)" { return "systeminfo" }
        "network connections" { return "netstat -ano" }
        "processes" { return "tasklist" }
        
        # Fallback option - call an LLM API for more complex commands
        default {
            return Invoke-LlmTranslation -NaturalLanguagePrompt $NaturalLanguagePrompt
        }
    }
}

function Invoke-LlmTranslation {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$NaturalLanguagePrompt
    )
    
    # In a real implementation, you would call an LLM API here
    # For now, we'll use a simplified version with your terminal controller
    
    try {
        $client = New-Object HttpClient
        $client.Timeout = [TimeSpan]::FromSeconds(30)
        
        $requestData = @{
            jsonrpc = "2.0"
            method = "convert_natural_language"
            params = @{
                prompt = $NaturalLanguagePrompt
            }
            id = Get-Random -Minimum 1000 -Maximum 9999
        } | ConvertTo-Json
        
        # This is a placeholder for where you'd call an API
        # For now, let's use simple heuristics for common tasks
        
        # Extract likely command verbs and targets
        $words = $NaturalLanguagePrompt.ToLower() -split '\s+'
        $verbs = @("list", "show", "create", "delete", "copy", "move", "find", "search", "get")
        
        foreach ($verb in $verbs) {
            if ($words -contains $verb) {
                # Simple context-based command building
                switch ($verb) {
                    "list" { return "dir" }
                    "show" { 
                        if ($words -contains "processes") { return "tasklist" }
                        else { return "dir" }
                    }
                    "find" { return "dir /s" }
                    "get" { 
                        if ($words -contains "ip") { return "ipconfig" }
                        elseif ($words -contains "disk") { return "diskpart list disk" }
                        else { return "echo Getting information..." }
                    }
                    default { return $null }
                }
            }
        }
        
        # If we couldn't match anything
        return $null
    }
    catch {
        Write-Host "Error translating natural language: $_" -ForegroundColor Red
        return $null
    }
}

function Start-NaturalLanguageShell {
    [CmdletBinding()]
    param()
    
    # Start the terminal server if it's not already running
    Start-TerminalServer
    
    Write-Host "Natural Language Terminal Shell" -ForegroundColor Green
    Write-Host "Type your commands in plain English or 'exit' to quit" -ForegroundColor Cyan
    Write-Host "-----------------------------------------" -ForegroundColor Gray
    
    $running = $true
    
    while ($running) {
        Write-Host "NL>" -ForegroundColor Green -NoNewline
        $input = Read-Host
        
        if ($input -eq "exit") {
            $running = $false
            continue
        }
        
        try {
            $result = Invoke-NaturalLanguageCommand -NaturalLanguagePrompt $input
            Write-Host $result
        }
        catch {
            Write-Host "Error: $_" -ForegroundColor Red
        }
        
        Write-Host "-----------------------------------------" -ForegroundColor Gray
    }
    
    Write-Host "Shell closed. Server still running. Use Stop-TerminalServer to shut it down." -ForegroundColor Yellow
}

# Export functions
Export-ModuleMember -Function Start-TerminalServer, Stop-TerminalServer, Invoke-TerminalCommand, Invoke-NaturalLanguageCommand, Start-NaturalLanguageShell