@echo off
rem SkillLens launcher - run from anywhere once this folder is on PATH.
rem Forwards all args to cli.py next to this file.
python "%~dp0cli.py" %*
