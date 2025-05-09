# PowerShell script to change VS Code branch

param (
    [Parameter(Mandatory=$false)]
    [switch]$List,
    
    [Parameter(Mandatory=$false)]
    [string]$Client,
    
    [Parameter(Mandatory=$false)]
    [string]$Branch,
    
    [Parameter(Mandatory=$false)]
    [string]$Commit,
    
    [Parameter(Mandatory=$false)]
    [string]$Url = "http://localhost:5000",

    [Parameter(Mandatory=$false)]
    [switch]$CreateMock,
    
    [Parameter(Mandatory=$false)]
    [switch]$GrantPermission,
    
    [Parameter(Mandatory=$false)]
    [switch]$DenyPermission
)

Write-Host "DEBUG: PowerShell script raw parameters received:" -ForegroundColor Magenta
Write-Host "  List: $List" -ForegroundColor Magenta
Write-Host "  Client: '$($Client)'" -ForegroundColor Magenta # Enclose in quotes to see if it's empty or has spaces
Write-Host "  Branch: '$($Branch)'" -ForegroundColor Magenta
Write-Host "  Commit: '$($Commit)'" -ForegroundColor Magenta
Write-Host "  Url: '$($Url)'" -ForegroundColor Magenta
Write-Host "  CreateMock: '$($CreateMock)'" -ForegroundColor Magenta
Write-Host "  GrantPermission: '$($GrantPermission)'" -ForegroundColor Magenta
Write-Host "  DenyPermission: '$($DenyPermission)'" -ForegroundColor Magenta
Write-Host "--- End DEBUG ---" -ForegroundColor Magenta

# Trim leading/trailing backslashes from string parameters if they exist
if ($Client -is [string]) { $Client = $Client.Trim('\') }
if ($Branch -is [string]) { $Branch = $Branch.Trim('\') }
if ($Commit -is [string]) { $Commit = $Commit.Trim('\') }

Write-Host "DEBUG: PowerShell script parameters after trimming:" -ForegroundColor Cyan
Write-Host "  Client: '$($Client)'" -ForegroundColor Cyan
Write-Host "  Branch: '$($Branch)'" -ForegroundColor Cyan
Write-Host "  Commit: '$($Commit)'" -ForegroundColor Cyan
Write-Host "--- End DEBUG ---" -ForegroundColor Cyan

# Check if backend is running
try {
    $null = Invoke-RestMethod -Uri $Url -Method Get -ErrorAction Stop
    Write-Host "Backend is running at $Url" -ForegroundColor Green
} catch {
    Write-Host "Backend is not running. Starting the backend..." -ForegroundColor Yellow
    
    # Try to start the backend
    Start-Process -FilePath "docker-compose" -ArgumentList "up -d hive-mind-backend" -NoNewWindow -Wait
    
    # Wait for backend to start
    Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}

# Build arguments for the Python script
$pythonArgs = @("change-vscode-branch.py") # Initialize with script name only

$pythonArgs += "--url", $Url # Add URL and its value

if ($List) {
    $pythonArgs += "--list"
}

if ($Client) {
    $pythonArgs += "--client", $Client # Add client flag and its value
}

if ($Branch) {
    $pythonArgs += "--branch", $Branch # Add branch flag and its value
}

if ($Commit) {
    $pythonArgs += "--commit", $Commit # Add commit flag and its value
}

# Create a mock client if requested (will use the new direct API)
if ($CreateMock) {
    Write-Host "Creating a mock VS Code client..." -ForegroundColor Yellow
    try {
        $response = Invoke-RestMethod -Method POST -Uri "$Url/api/vscode/mock" -ContentType "application/json"
        $mockClientId = $response.client_id
        Write-Host "Mock client created with ID: $mockClientId" -ForegroundColor Green
        
        # If no specific client was specified, use this mock client
        if (-not $Client) {
            $Client = $mockClientId
            Write-Host "Using newly created mock client ID: $Client" -ForegroundColor Cyan
            # Add to pythonArgs if not already present
            if (-not ($pythonArgs -contains "--client")) {
                $pythonArgs += "--client", $Client
            }
        }
    } catch {
        Write-Host "Error creating mock client: $_" -ForegroundColor Red
    }
}

# Update permissions if requested
if (($GrantPermission -or $DenyPermission) -and $Client) {
    $permissionVal = if ($GrantPermission) { $true } else { $false }
    $permissionDesc = if ($GrantPermission) { "granted" } else { "denied" }
    
    Write-Host "$permissionDesc permission for client $Client..." -ForegroundColor Yellow
    try {
        $body = @{
            clientId = $Client
            allowed = $permissionVal
            reason = "Set via PowerShell script"
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Method POST -Uri "$Url/api/vscode/permission" -Body $body -ContentType "application/json"
        Write-Host "Permission successfully $permissionDesc for client $Client" -ForegroundColor Green
    } catch {
        Write-Host "Error setting permission: $_" -ForegroundColor Red
    }
}

Write-Host "PowerShell: Constructed pythonArgs before execution:" -ForegroundColor Cyan
$pythonArgs | ForEach-Object { Write-Host "  Arg: '$_'" -ForegroundColor Cyan }

# Run the Python script and capture its combined stdout and stderr
Write-Host "PowerShell: Executing Python script..." -ForegroundColor Cyan
$stdOutAndErr = (& python $pythonArgs 2>&1)
$exitCode = $LASTEXITCODE # Capture exit code immediately

if ($exitCode -ne 0) {
    Write-Host "Python script failed with exit code $exitCode." -ForegroundColor Red
    Write-Host "Output from script (stdout/stderr):" -ForegroundColor Yellow
    $stdOutAndErr | ForEach-Object { Write-Host $_ }
    exit $exitCode
}

# If Python script was successful (exitCode is 0)
if ($List) {
    # Python script prints JSON to its stdout when --list is used.
    # All other prints (debug/log messages) go to its stderr.
    # $stdOutAndErr contains all lines, we need to find the JSON list.
    $jsonLine = $null
    foreach ($line in $stdOutAndErr) {
        if (-not ($line -is [string]) -or [string]::IsNullOrWhiteSpace($line)) {
            continue
        }
        # Heuristic: JSON list starts with '[' and ends with ']'
        if ($line.TrimStart().StartsWith("[") -and $line.TrimEnd().EndsWith("]")) {
            try {
                # Attempt to parse. If it deserializes to a PowerShell array, it's likely our target.
                $parsedCandidate = $line | ConvertFrom-Json -ErrorAction SilentlyContinue
                if ($parsedCandidate -is [System.Array]) {
                    $jsonLine = $line
                    break # Found the JSON line
                }
            } catch {
                # Line was not parseable JSON or not an array, continue searching
            }
        }
    }

    if ($jsonLine) {
        try {
            $connectedClients = $jsonLine | ConvertFrom-Json -ErrorAction Stop
            Write-Host "Connected VS Code Clients:" -ForegroundColor Green
            if ($connectedClients.Count -gt 0) {
                $connectedClients | ForEach-Object { Write-Host "- $_" }
            } else {
                Write-Host "No clients reported by the script (empty list received)." -ForegroundColor Cyan
            }
            # Store in a variable for potential further use in the script
            $Global:ConnectedClientIDs = $connectedClients
            Write-Host "Client IDs are available in `$Global:ConnectedClientIDs" -ForegroundColor Magenta
        } catch {
            Write-Host "Failed to parse the identified JSON line ('$jsonLine') for client list." -ForegroundColor Red
            Write-Host "Specific Error: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "Full output from Python script was:" -ForegroundColor Yellow
            $stdOutAndErr | ForEach-Object { Write-Host $_ }
            exit 1 
        }
    } else {
        Write-Host "Could not find the JSON list in the Python script output." -ForegroundColor Yellow
        Write-Host "This may indicate an issue with the Python script or no clients connected and an unexpected output format." -ForegroundColor Yellow
        Write-Host "Full output from Python script was:" -ForegroundColor Yellow
        $stdOutAndErr | ForEach-Object { Write-Host $_ }
        # If the Python script is expected to always return a JSON array (e.g., "[]" for no clients),
        # then not finding $jsonLine might be considered an error.
        # For now, just a warning. If this state should be an error, add 'exit 1' here.
    }
} else {
    # Successful non-list command (e.g., branch change).
    # Python script's useful output (logs, success/failure messages for the operation) is on its stderr.
    # $stdOutAndErr contains everything (stdout and stderr from Python).
    Write-Host "Python script (non-list command) executed successfully (exit code 0)." -ForegroundColor Green
    Write-Host "Full output from script (stdout/stderr):" -ForegroundColor DarkGray
    $stdOutAndErr | ForEach-Object { Write-Host $_ }
}

# Examples of usage:
# .\change-vscode-branch.ps1 -List
# .\change-vscode-branch.ps1 -Client "client-id" -Branch "main"
# .\change-vscode-branch.ps1 -Client "client-id" -Branch "feature/new-feature" -Commit "a1b2c3d4" 
# .\change-vscode-branch.ps1 -CreateMock -Branch "main" 