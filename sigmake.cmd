@echo off
REM Check if an argument is provided
IF "%~1"=="" (
    echo Usage: sigmake.cmd filename.pat description
    exit /b 1
)

IF "%~2"=="" (
    echo Usage: sigmake.cmd filename description
    exit /b 1
)

REM Extract the filename without the extension
SET "filename=%~n1"

IF EXIST ".\%filename%.sig" (
    echo .\%filename%.sig already exists.
    exit /b 0
)

REM Loop through the sigmake.exe and python calls
:loop
REM Call sig.exe with the provided argument
echo Try to make sign using pat pattern file .\%filename%.pat
sigmake.exe -n="%~2" .\%filename%.pat .\%filename%.sig
REM Call sig2pat.py with the provided argument
echo Solve file .\%filename%.exc
REM Check if the .sig file was created
IF EXIST ".\%filename%.sig" (
    echo .\%filename%.sig created successfully.
    exit /b 0
) ELSE (
    python .\pat_resolve.py .\%filename%.exc
    echo .\%filename%.sig not created. Retrying...
    GOTO loop
)
