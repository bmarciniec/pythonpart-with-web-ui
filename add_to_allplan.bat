@echo off
REM This script will place symbolic link in your ALLLPLAN Usr or Std directory pointing to this repository
REM for testing purposes
set /p targetPath="Please enter the Path to Usr or Std: "

set scriptDir=%~dp0

if not exist "%targetPath%\PythonPartsScripts" (
    mkdir "%targetPath%\PythonPartsScripts"
)
mklink /D "%targetPath%\Library\Test WPF" "%scriptDir%Library\Test WPF"
mklink /D "%targetPath%\PythonPartsScripts\web_browser_demo" "%scriptDir%PythonPartsScripts\web_browser_demo"

echo "PythonPart installed in Allplan. You'll find it in Library -> Test WPF -> Test WPF. Press any key to continue"
pause >nul
