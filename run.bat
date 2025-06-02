@echo off

REM Start Flask app in a new command window
start cmd /k "python app.py"

REM Wait a few seconds to ensure Flask starts
timeout /t 3

REM Start ngrok in the current window
ngrok http --url=wren-proper-sadly.ngrok-free.app 8080