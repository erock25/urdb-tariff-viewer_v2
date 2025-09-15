@echo off
REM GitHub Update Batch Script for Windows
REM This script helps you update your project on GitHub

echo 🚀 Updating URDB Tariff Viewer on GitHub...
echo ============================================

REM Check if Git is available
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git is not installed or not in PATH
    echo Please install Git and try again
    pause
    exit /b 1
)

REM Check for changes
echo 🔍 Checking for changes...
git status --porcelain >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error checking git status
    pause
    exit /b 1
)

REM Check if there are changes
for /f %%i in ('git status --porcelain 2^>nul') do (
    goto :has_changes
)

echo ℹ️  No changes detected. Nothing to update.
echo.
echo 💡 To make changes:
echo    1. Edit your files (src/main.py, etc.)
echo    2. Save the changes
echo    3. Run this script again
echo.
pause
exit /b 0

:has_changes
echo ✅ Changes detected, proceeding with update...

REM Stage changes
echo 🔄 Staging changes...
git add .
if %errorlevel% neq 0 (
    echo ❌ Error staging changes
    pause
    exit /b 1
)

REM Get commit message
set /p commit_msg="📝 Enter commit message: "
if "%commit_msg%"=="" (
    echo ❌ Commit message cannot be empty
    pause
    exit /b 1
)

REM Commit changes
echo 📝 Committing changes...
git commit -m "%commit_msg%"
if %errorlevel% neq 0 (
    echo ❌ Error committing changes
    pause
    exit /b 1
)

REM Push to GitHub
echo 📤 Pushing to GitHub...
git push
if %errorlevel% neq 0 (
    echo ❌ Error pushing to GitHub
    pause
    exit /b 1
)

echo.
echo 🎉 SUCCESS! Project updated on GitHub!
echo =======================================
echo 📱 Streamlit Cloud will automatically redeploy your app
echo 🔗 Your app URL: https://urdb-tariff-viewer-v2-erock25.streamlit.app
echo.
echo 💡 The redeployment usually takes 2-5 minutes
echo.
pause
