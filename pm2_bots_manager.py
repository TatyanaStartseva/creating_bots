import os
import subprocess
import time
python_path = "C:\\Users\\User\\PycharmProjects\\pythonProject6\\Scripts\\python.exe"
directory_path = 'C:/Users/User/PycharmProjects/pythonProject6/mega_bot/web_app/bots'
pm2_list_file = 'pm2_processes.txt'

def stop_processing(bot_token):
    process = subprocess.Popen(['pm2', 'ls'], stdout=subprocess.PIPE, shell=True)
    output, _ = process.communicate()
    output_str = output.decode('utf-8')
    if bot_token in output_str:
        folder_full_path = os.path.join(directory_path, bot_token)
        pm2_command = f'pm2 stop {bot_token}'
        subprocess.run(pm2_command, shell=True, cwd=folder_full_path, encoding='utf-8')
    return


def get_folders_in_directory(directory):
    return [folder for folder in os.listdir(directory) if os.path.isdir(os.path.join(directory, folder))]


def get_pm2_processes(directory):
    process = subprocess.Popen(['pm2', 'ls'], stdout=subprocess.PIPE, shell=True)
    output, _ = process.communicate()
    output_str = output.decode('utf-8')

    folders = get_folders_in_directory(directory)
    pm2_processes = []

    for folder in folders:
        if folder in output_str:
            pm2_processes.append(folder)

    return pm2_processes

def write_pm2_processes_to_file(processes):
    with open(pm2_list_file, 'w', encoding='utf-8', errors='ignore') as file:
        for process in processes:
            file.write(process + '\n')


def read_pm2_processes_from_file():
    if os.path.exists(pm2_list_file):
        with open(pm2_list_file, 'r', encoding='utf-8') as file:
            return file.read().splitlines()
    return []


def add_folders_to_pm2(added_folders, directory):
    try:
        process = subprocess.Popen(['pm2', 'ls'], stdout=subprocess.PIPE, shell=True)
        output, _ = process.communicate()
        output_str = output.decode('utf-8')
        if added_folders:
                for folder in added_folders:
                    if folder not in output_str:
                        folder_full_path = os.path.join(directory, folder)
                        python_path = "C:\\Users\\User\\PycharmProjects\\pythonProject6\\Scripts\\python.exe"
                        pm2_command = f'pm2 start {python_path} --name {folder} --watch -- -m bot'
                        time.sleep(30)
                        subprocess.run(pm2_command, shell=True, cwd=folder_full_path, encoding='utf-8')
                    else:
                        print("Нет новых папок для добавления в pm2.")
        else:
            print("Нет новых папок для добавления в pm2.")
    except subprocess.CalledProcessError as e:
            print(f"Ошибка при запуске процесса: {e}")

def delete_folders_from_pm2(removed_folders, directory):
    try:
        process = subprocess.Popen(['pm2', 'ls'], stdout=subprocess.PIPE, shell=True)
        output, _ = process.communicate()
        output_str = output.decode('utf-8')
        if removed_folders:
                for folder in removed_folders:
                    if folder in output_str:
                        pm2_command = f'pm2 delete {folder}'
                        subprocess.run(pm2_command, shell=True, cwd=directory, encoding='utf-8')
        else:
            print("Нет папок для удаления из pm2.")
    except Exception as e:
        print(f"Ошибка выполнения команды: ")
        print(f"{e}")

def monitor_folder(directory):
    while True:
        current_processes = get_pm2_processes(directory)
        previous_processes = read_pm2_processes_from_file()
        added_folders = [folder for folder in os.listdir(directory) if folder not in previous_processes]
        removed_folders = [folder for folder in previous_processes if folder not in os.listdir(directory)]
        if added_folders:
            add_folders_to_pm2(added_folders, directory)
            current_processes += added_folders

        if removed_folders:
            delete_folders_from_pm2(removed_folders, directory)
            current_processes = [process for process in current_processes if process not in removed_folders]

        write_pm2_processes_to_file(current_processes)

        time.sleep(5)

if __name__ == "__main__":
    monitor_folder(directory_path)
