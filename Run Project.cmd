@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 build_project.py
  goto done
)
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
  "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" build_project.py
  goto done
)
where python >nul 2>nul
if not errorlevel 1 (
  python build_project.py
  goto done
)
echo Python was not found. Install Python 3.10 or newer from python.org, then try again.
:done
echo.
echo Results are in the results folder. Read docs\findings.md for the explanation.
pause
