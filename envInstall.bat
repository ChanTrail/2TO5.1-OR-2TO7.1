@echo off

REM 运行主程序，并添加错误处理
.\Python\python -m pip install -r requirements.txt || goto :error

:end
exit /b 0

:error
echo 发生错误，请检查日志并尝试重新运行脚本。
pause
exit /b 1