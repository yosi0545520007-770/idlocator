@echo off
setlocal

REM הגדרת צבעים להודעות
for /f "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do (
    set "DEL=%%a"
)

call :colorEcho 91 "Error:"
call :colorEcho 92 "Success:"
call :colorEcho 93 "Warning:"
call :colorEcho 96 "Info:"

set "PROJECT_ID=idlocator-627e0"
set "SERVICE_NAME=idlocator-web"
set "REGION=us-central1"

REM בדיקה שאנחנו בתוך ריפוזיטורי של Git
git rev-parse --is-inside-work-tree >nul 2>&1
if %errorlevel% neq 0 (
    call :colorEcho 91 "Error: Not a git repository."
    echo Please run this script from the root of your project.
    goto :eof
)

REM קבלת הודעת ה-commit כארגומנט או מהמשתמש
set "commit_message=%~1"
if not defined commit_message (
    set /p commit_message="Enter commit message: "
)
if not defined commit_message (
    call :colorEcho 91 "Error: Commit message cannot be empty."
    goto :eof
)

echo.
call :colorEcho 96 "Step 1: Pushing code to GitHub..."
echo ===================================

echo.
echo --- Staging all changes...
git add .
if %errorlevel% neq 0 ( call :colorEcho 91 "Error: 'git add' failed." & goto :eof )

echo --- Committing changes...
git commit -m "%commit_message%"
if %errorlevel% neq 0 ( call :colorEcho 93 "Warning: 'git commit' failed. Maybe there are no changes to commit." )

echo --- Pushing to remote repository...
git push
if %errorlevel% neq 0 ( call :colorEcho 91 "Error: 'git push' failed." & goto :eof )

echo.
call :colorEcho 92 "Successfully pushed to GitHub."

echo.
call :colorEcho 96 "Step 2: Building and pushing container to Google Cloud Registry..."
echo =================================================================
gcloud builds submit --tag "gcr.io/%PROJECT_ID%/%SERVICE_NAME%"
if %errorlevel% neq 0 ( call :colorEcho 91 "Error: 'gcloud builds submit' failed." & goto :eof )

echo.
call :colorEcho 92 "Container built and pushed successfully."

echo.
call :colorEcho 96 "Step 3: Deploying new container to Google Cloud Run..."
echo =========================================================
gcloud run deploy %SERVICE_NAME% --image "gcr.io/%PROJECT_ID%/%SERVICE_NAME%" --platform managed --region "%REGION%" --allow-unauthenticated
if %errorlevel% neq 0 ( call :colorEcho 91 "Error: 'gcloud run deploy' failed." & goto :eof )

echo.
call :colorEcho 92 "Service deployed to Cloud Run successfully."

echo.
call :colorEcho 96 "Step 4: Deploying to Firebase Hosting..."
echo ========================================
firebase deploy --only hosting
if %errorlevel% neq 0 ( call :colorEcho 91 "Error: 'firebase deploy' failed." & goto :eof )

echo.
call :colorEcho 92 "Deployment to Firebase completed successfully!"
goto :eof

:colorEcho
echo %DEL%
echo %~2
exit /b