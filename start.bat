@echo off

REM 启动主程序，如果失败则跳转到错误处理
.\Python\python main.py || goto :error

:end
exit /b 0

:error
echo 程序执行失败，请检查日志或联系开发者。
pause
exit /b 1