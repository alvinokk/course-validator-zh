@echo off
echo 启动课程验证器...
echo 请在浏览器打开 http://localhost:3001
echo.
set PORT=3001
python "%~dp0server.py"
pause
