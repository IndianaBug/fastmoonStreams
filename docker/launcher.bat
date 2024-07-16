@echo off

"C:\workspaces\fastmoonStreams\kafka\bin\zookeeper-server-start.bat" "C:\workspaces\fastmoonStreams\kafka\config\zookeeper.properties"
"C:\workspaces\fastmoonStreams\kafka\bin\kafka-server-start.bat" "C:\workspaces\fastmoonStreams\kafka\config\server.properties"

python "C:\path\to\clauncher.py"
python "C:\path\to\plauncher.py"

pause  ; This keeps the command prompt open after execution (optional)