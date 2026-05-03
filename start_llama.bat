@echo off
title PartnerAI — LLM Server

:RESTART
echo.
echo [%date% %time%] Starting LLM server on port 8080...

REM Kill any stale instance first
taskkill /F /IM llama-server.exe >nul 2>&1
timeout /T 2 /NOBREAK >nul

REM Start the server
start "" /B "E:\llama_cpp\llama-server.exe" ^
    -m "E:\llama_cpp\Phi-3-mini-4k-instruct-q4.gguf" ^
    -c 4096 ^
    --host 127.0.0.1 ^
    --port 8080

REM Wait up to 30 s for it to bind the port
set /A tries=0
:WAIT
netstat -ano | findstr "8080" | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL%==0 goto READY
set /A tries+=1
if %tries% GEQ 30 (
    echo [ERROR] Server did not start after 30 seconds. Check the model path.
    pause
    goto END
)
timeout /T 1 /NOBREAK >nul
goto WAIT

:READY
echo [OK] Llama.cpp server is ready on http://127.0.0.1:8080
echo      Press Ctrl+C to stop, window will auto-restart on crash.

REM Keep monitoring and auto-restart if process dies
:MONITOR
timeout /T 5 /NOBREAK >nul
netstat -ano | findstr "8080" | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL%==0 goto MONITOR

echo [WARN] Server stopped. Restarting in 3 seconds...
timeout /T 3 /NOBREAK >nul
goto RESTART

:END
pause
