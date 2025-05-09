# PowerShell script to test VS Code API endpoints

param (
    [Parameter(Mandatory=$false)]
    [string]$BaseUrl = "http://localhost:5000",
    
    [Parameter(Mandatory=$false)]
    [switch]$CreateMockClient,
    
    [Parameter(Mandatory=$false)]
    [switch]$ListClients,
    
    [Parameter(Mandatory=$false)]
    [string]$GetClient,
    
    [Parameter(Mandatory=$false)]
    [string]$ClientId,
    
    [Parameter(Mandatory=$false)]
    [string]$Branch,
    
    [Parameter(Mandatory=$false)]
    [string]$Commit,
    
    [Parameter(Mandatory=$false)]
    [switch]$GrantPermission,
    
    [Parameter(Mandatory=$false)]
    [switch]$DenyPermission
)

Write-Host "VS Code API Test Script" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan

# Create a mock client for testing
if ($CreateMockClient) {
    Write-Host "Creating mock client..." -ForegroundColor Yellow
    try {
        $response = Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/vscode/mock" -ContentType "application/json"
        Write-Host "Mock client created successfully:" -ForegroundColor Green
        $response | ConvertTo-Json
        $Global:LastCreatedClientId = $response.client_id
        Write-Host "Client ID stored in `$Global:LastCreatedClientId: $($Global:LastCreatedClientId)" -ForegroundColor Magenta
    }
    catch {
        Write-Host "Error creating mock client: $_" -ForegroundColor Red
    }
}

# List all clients
if ($ListClients) {
    Write-Host "Listing all VS Code clients..." -ForegroundColor Yellow
    try {
        $response = Invoke-RestMethod -Method GET -Uri "$BaseUrl/api/vscode/clients" -ContentType "application/json"
        Write-Host "Clients retrieved successfully:" -ForegroundColor Green
        $response | ConvertTo-Json -Depth 5
        $clientsArray = @()
        foreach ($key in $response.clients.PSObject.Properties.Name) {
            $clientsArray += [PSCustomObject]@{
                ClientId = $key
                WorkspaceName = $response.clients.$key.workspace_name
                CurrentBranch = $response.clients.$key.current_branch
                Connected = $response.clients.$key.connected
                Permission = $response.clients.$key.permission
            }
        }
        $Global:VSCodeClients = $clientsArray
        Write-Host "Clients data stored in `$Global:VSCodeClients" -ForegroundColor Magenta
    }
    catch {
        Write-Host "Error listing clients: $_" -ForegroundColor Red
    }
}

# Get information about a specific client
if ($GetClient) {
    Write-Host "Getting information for client: $GetClient" -ForegroundColor Yellow
    try {
        $response = Invoke-RestMethod -Method GET -Uri "$BaseUrl/api/vscode/client/$GetClient" -ContentType "application/json"
        Write-Host "Client information retrieved successfully:" -ForegroundColor Green
        $response | ConvertTo-Json -Depth 5
        $Global:VSCodeClientInfo = $response
        Write-Host "Client info stored in `$Global:VSCodeClientInfo" -ForegroundColor Magenta
    }
    catch {
        Write-Host "Error getting client info: $_" -ForegroundColor Red
    }
}

# Grant permission to a client
if ($GrantPermission -and $ClientId) {
    Write-Host "Granting permission to client: $ClientId" -ForegroundColor Yellow
    try {
        $body = @{
            clientId = $ClientId
            allowed = $true
            reason = "Granted via test script"
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/vscode/permission" -Body $body -ContentType "application/json"
        Write-Host "Permission granted successfully:" -ForegroundColor Green
        $response | ConvertTo-Json
    }
    catch {
        Write-Host "Error granting permission: $_" -ForegroundColor Red
    }
}

# Deny permission to a client
if ($DenyPermission -and $ClientId) {
    Write-Host "Denying permission to client: $ClientId" -ForegroundColor Yellow
    try {
        $body = @{
            clientId = $ClientId
            allowed = $false
            reason = "Denied via test script"
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/vscode/permission" -Body $body -ContentType "application/json"
        Write-Host "Permission denied successfully:" -ForegroundColor Green
        $response | ConvertTo-Json
    }
    catch {
        Write-Host "Error denying permission: $_" -ForegroundColor Red
    }
}

# Change branch for a client
if ($ClientId -and $Branch) {
    Write-Host "Changing branch for client: $ClientId to $Branch" -ForegroundColor Yellow
    
    $body = @{
        clientId = $ClientId
        branch = $Branch
    }
    
    if ($Commit) {
        $body.commit = $Commit
        Write-Host "Including commit: $Commit" -ForegroundColor Yellow
    }
    
    try {
        $bodyJson = $body | ConvertTo-Json
        $response = Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/vscode/checkout" -Body $bodyJson -ContentType "application/json"
        Write-Host "Branch change request processed successfully:" -ForegroundColor Green
        $response | ConvertTo-Json
    }
    catch {
        Write-Host "Error changing branch: $_" -ForegroundColor Red
        if ($_.Exception.Response) {
            try {
                $responseBody = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($responseBody)
                $responseText = $reader.ReadToEnd()
                Write-Host "Response body: $responseText" -ForegroundColor Red
            }
            catch {
                Write-Host "Could not read error response: $_" -ForegroundColor Red
            }
        }
    }
} 