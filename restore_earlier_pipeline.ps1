# Restore Earlier Pipeline and Setup New Dataset
# =============================================

Write-Host "Restoring Earlier Pipeline Version..." -ForegroundColor Cyan

# Step 1: Check current status
Write-Host "`nCurrent Git Status:" -ForegroundColor Yellow
git --no-pager status --porcelain

# Step 2: Check available tags and branches
Write-Host "`nAvailable Tags and Branches:" -ForegroundColor Yellow
git --no-pager tag -l
git --no-pager branch -a

# Step 3: Create a backup branch of current state
Write-Host "`nCreating backup of current state..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backup_branch = "backup-frontend-$timestamp"
git checkout -b $backup_branch
Write-Host "Created backup branch: $backup_branch" -ForegroundColor Green

# Step 4: Checkout the earlier working version
Write-Host "`nChecking out earlier working version..." -ForegroundColor Yellow
git checkout v2.1-doublet-working
if ($LASTEXITCODE -eq 0) {
    Write-Host "Successfully checked out v2.1-doublet-working" -ForegroundColor Green
} else {
    Write-Host "Failed to checkout v2.1-doublet-working, trying alternative..." -ForegroundColor Red
    git checkout v2.0-doublet-analysis
}

# Step 5: Create a new branch for the separate project
Write-Host "`nCreating new branch for separate project..." -ForegroundColor Yellow
git checkout -b ICTcontent
Write-Host "Created new branch: ICTcontent" -ForegroundColor Green

# Step 6: Show current structure
Write-Host "`nCurrent Project Structure:" -ForegroundColor Yellow
Get-ChildItem -Name | Where-Object { $_ -notlike ".*" } | Sort-Object

# Step 7: Setup instructions
Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "1. Review the restored pipeline structure" -ForegroundColor White
Write-Host "2. Decide what new dataset you want to add" -ForegroundColor White
Write-Host "3. Create a new pipeline for the new dataset" -ForegroundColor White
Write-Host "4. Test the restored pipeline works correctly" -ForegroundColor White

Write-Host "`nTo return to your frontend version later:" -ForegroundColor Yellow
Write-Host "   git checkout $backup_branch" -ForegroundColor White
Write-Host "`nTo work on the ICTcontent project:" -ForegroundColor Yellow
Write-Host "   git checkout ICTcontent" -ForegroundColor White

Write-Host "`nPipeline restoration completed!" -ForegroundColor Green
