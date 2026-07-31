@echo off
setlocal enabledelayedexpansion

rem run_lab.bat — Windows wrapper for python-ieee754-binary64-lab
rem Runs cases, unittest, and regenerates RESULTS.md

rem cd to script directory
cd /d "%~dp0"

rem find a suitable python (>= 3.12)
set PYTHON=
for %%P in (py python python3) do (
  if not defined PYTHON (
    where %%P >nul 2>nul
    if !errorlevel! equ 0 (
      %%P -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>nul
      if !errorlevel! equ 0 set PYTHON=%%P
    )
  )
)

if not defined PYTHON (
  echo ERROR: Python 3.12+ required - none found in PATH ^(tried: py, python, python3^)
  exit /b 1
)

rem print version
for /f "delims=" %%v in ('%PYTHON% -c "import sys; print('{}.{}'.format(*sys.version_info[:2]))"') do set PYVER=%%v
echo === python-ieee754-binary64-lab ^| Python %PYVER% ===
echo.

echo [1/3] Running cases...
%PYTHON% run.py
if errorlevel 1 exit /b %errorlevel%
echo.

echo [2/3] Running unittest...
%PYTHON% -m unittest test_binary64 -v
if errorlevel 1 exit /b %errorlevel%
echo.

echo [3/3] Rendering RESULTS.md...
%PYTHON% results_to_md.py
if errorlevel 1 exit /b %errorlevel%
echo.

echo === done ===
echo   results.json  -- full per-case output
echo   results.csv   -- summary table
echo   RESULTS.md    -- rendered summary
exit /b 0
