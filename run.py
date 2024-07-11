import subprocess
import sys
import platform

shared_commands_windows  = [
    "cd C:\\coding\\fastmoon\\fastmoonStreams",
    "C:\\coding\\fastmoon\\fastmoonVenv\\v3.9\\Scripts\\activate"
]

shared_commands_linux = [
    # "cd /home/user/coding/fastmoon/fastmoonStreams",
    # "source /home/user/coding/fastmoon/fastmoonVenv/v3.9/bin/activate"
]

# pytests
# pytest ProcessCenter\tests\test_MessageProcess.py

command_groups_windows  = [
    ["python streams.py"],
    # ["cd C:\Kafka", ".\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties"], # zookeeper
    # ["cd C:\Kafka", ".\bin\windows\kafka-server-start.bat .\config\server.properties"], # kafka server
    # ["python producer.py"],    # producer
    # ["faust -A consumer worker -l info --web-port=6066"] # consumer
]

command_groups_linux = [
    ["python streams.py"],
    # ["chmod -R +x /workspaces/fastmoonStreams/kafka", "/workspaces/fastmoonStreams/kafka/bin/zookeeper-server-start.sh /workspaces/fastmoonStreams/kafka/config/zookeeper.properties"], # zookeeper
    # ["/workspaces/fastmoonStreams/kafka/bin/kafka-server-start.sh /workspaces/fastmoonStreams/kafka/config/server.properties"], # kafka server
    # ["python producer.py"],    # producer
    # ["faust -A consumer worker -l info --web-port=6066"] # consumer
    
    # You will need to create virtual environment first on the webserver
    # sudo add-apt-repository ppa:deadsnakes/ppa
    # sudo apt-get update
    # sudo apt-get install python3.7
    # sudo apt-get install python3.7-venv
    # python3.7 -m venv fastmoonVenv
]

def run_commands(commands, os_type):
    if os_type == 'windows':
        all_commands = shared_commands_windows + commands
        command_string = " && ".join(all_commands)
        final_command = f'start cmd /k "{command_string}"'
    else:
        all_commands = shared_commands_linux + commands
        command_string = " && ".join(all_commands)
        final_command = f'gnome-terminal -- bash -c "{command_string}; exec bash"'
    
    subprocess.run(final_command, shell=True)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_commands.py [w|l]")
        sys.exit(1)
    
    os_type = sys.argv[1].lower()
    
    if os_type == 'w':
        for command_group in command_groups_windows:
            run_commands(command_group, 'windows')
    elif os_type == 'l':
        for command_group in command_groups_linux:
            run_commands(command_group, 'linux')
    else:
        print("Invalid argument. Use 'w' for Windows or 'l' for Linux.")
        sys.exit(1)