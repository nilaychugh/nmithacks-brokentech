function Execute-NaturalCommand {
    param (
        [Parameter(Mandatory=$true, Position=0, ValueFromRemainingArguments=$true)]
        [string[]]$Query
    )
    
    $fullQuery = $Query -join " "
    $pythonPath = "python"
    $scriptPath = "C:\Users\Nilay\Desktop\terminal-controller-mcp\term_control.py"
    
    $request = @{
        jsonrpc = "2.0"
        method = "process_natural_language"
        params = @{
            query = $fullQuery
        }
        id = 1
    } | ConvertTo-Json -Compress
    
    $result = $request | & $pythonPath $scriptPath
    
    try {
        $response = $result | ConvertFrom-Json
        if ($response.error) {
            Write-Error $response.error.message
            return $null
        }
        return $response.result
    }
    catch {
        Write-Error "Failed to parse response: $_"
        return $result
    }
}

# Add an alias for easier use
Set-Alias -Name nlc -Value Execute-NaturalCommand