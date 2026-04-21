@echo off
setlocal enabledelayedexpansion

REM Get the project root directory
set PROJECT_ROOT=%~dp0..

REM Step 1: Build the .NET assembly
echo Building .NET assembly...
cd /d "%PROJECT_ROOT%\wpf"
dotnet build -c Release
if errorlevel 1 (
    echo Build failed!
    exit /b 1
)

REM Step 2: Copy DLLs to Python layer
echo.
echo Copying DLLs to Python layer...
set SOURCE_DIR=%PROJECT_ROOT%\wpf\bin\Release\net472
set TARGET_DIR=%PROJECT_ROOT%\PythonPartsScripts\web_browser_demo

if not exist "%SOURCE_DIR%" (
    echo Error: Source directory not found: %SOURCE_DIR%
    exit /b 1
)

if not exist "%TARGET_DIR%" (
    echo Creating target directory: %TARGET_DIR%
    mkdir "%TARGET_DIR%"
)

REM Copy all DLL files
for %%F in ("%SOURCE_DIR%\*.dll") do (
    echo Copying: %%~nxF
    copy "%%F" "%TARGET_DIR%\" /Y
)

echo.
echo Build completed successfully!
exit /b 0
