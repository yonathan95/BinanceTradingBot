# Script: Concatenate all relevant project files into one output file

$outputFile = "debug-codebase-concat.txt"

# Define excluded directories and file patterns
$excludedDirs = @("node_modules", ".git", ".vscode", "__pycache__")
$excludedPatterns = @("*.webp", "*.png", "*.jpg", "*.jpeg", "*.exe", "*.dll", "*.bin", "*.lock", "*.ico", "*.svg", "*.DS_Store")

# Clear the output file if it exists
if (Test-Path $outputFile) {
    Remove-Item $outputFile
}

# Get all files recursively, excluding specified directories and patterns
$allFiles = Get-ChildItem -Recurse -File | Where-Object {
    $file = $_
    # Exclude files in excluded directories
    foreach ($dir in $excludedDirs) {
        if ($file.FullName -match "\\$dir\\") { return $false }
    }
    # Exclude files matching excluded patterns
    foreach ($pattern in $excludedPatterns) {
        if ($file.Name -like $pattern) { return $false }
    }
    # Exclude hidden files
    if ($file.Attributes -band [System.IO.FileAttributes]::Hidden) { return $false }
    return $true
}

foreach ($file in $allFiles) {
    Add-Content $outputFile "--- FILE: $($file.FullName) ---"
    Get-Content $file.FullName | Add-Content $outputFile
    Add-Content $outputFile "`n"
}

Write-Host "Concatenation complete. Output written to $outputFile" 