@echo off
echo Restoring Earlier Pipeline Version...
echo.

echo Current Git Status:
git --no-pager status --porcelain
echo.

echo Available Tags:
git --no-pager tag -l
echo.

echo Available Branches:
git --no-pager branch -a
echo.

echo Creating backup of current state...
set timestamp=%date:~10,4%%date:~4,2%%date:~7,2%-%time:~0,2%%time:~3,2%%time:~6,2%
set timestamp=%timestamp: =0%
set backup_branch=backup-frontend-%timestamp%
git checkout -b %backup_branch%
echo Created backup branch: %backup_branch%
echo.

echo Checking out earlier working version...
git checkout v2.1-doublet-working
if %errorlevel% equ 0 (
    echo Successfully checked out v2.1-doublet-working
) else (
    echo Failed to checkout v2.1-doublet-working, trying alternative...
    git checkout v2.0-doublet-analysis
)
echo.

echo Creating new branch for ICTcontent project...
git checkout -b ICTcontent
echo Created new branch: ICTcontent
echo.

echo Current Project Structure:
dir /B | findstr /v "^\."
echo.

echo Next Steps:
echo 1. Review the restored pipeline structure
echo 2. Decide what new dataset you want to add
echo 3. Create a new pipeline for the new dataset
echo 4. Test the restored pipeline works correctly
echo.

echo To return to your frontend version later:
echo    git checkout %backup_branch%
echo.

echo To work on the ICTcontent project:
echo    git checkout ICTcontent
echo.

echo Pipeline restoration completed!
pause
