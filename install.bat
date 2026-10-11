@echo off
rem Adds the SkillLens folder to the user PATH once, then `skilllens` works anywhere.
setlocal
set "HERE=%~dp0"
set "HERE=%HERE:~0,-1%"
echo %PATH% | findstr /I /C:"%HERE%" >nul
if %ERRORLEVEL%==0 (
  echo Already on PATH: %HERE%
  echo Use it anywhere as: skilllens --prompt "your task"
  exit /b 0
)
for /f "tokens=2*" %%a in ('reg query HKCU\Environment /v Path 2^>nul') do set "USERPATH=%%b"
if not defined USERPATH set "USERPATH="
setx PATH "%USERPATH%;%HERE%" >nul
echo Added to user PATH: %HERE%
echo Restart your terminal, then run anywhere: skilllens --prompt "your task"
