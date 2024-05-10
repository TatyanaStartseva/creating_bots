import os
import subprocess
import time
import re


def get_bot_directory():
    directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "bots"))
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def stop_processing(bot_token):
    process = subprocess.Popen(["pm2", "ls"], stdout=subprocess.PIPE, shell=True)
    output, _ = process.communicate()
    output_str = output.decode("utf-8")
    if bot_token in output_str:
        folder_full_path = os.path.join(get_bot_directory(), bot_token)
        pm2_command = f"pm2 stop {bot_token}"
        subprocess.run(pm2_command, shell=True, cwd=folder_full_path, encoding="utf-8")
    return


def get_pm2_processes():
    process = subprocess.Popen(["pm2", "ls"], stdout=subprocess.PIPE, shell=True)
    output, _ = process.communicate()
    output_str = output.decode("utf-8")
    lines = output_str.split("\n")
    process_names = []
    for line in lines[3:]:
        parts = line.split()
        if len(parts) > 1:
            process_name = parts[3]
            process_names.append(process_name)

    return process_names


def add_folders_to_pm2(added_folders, directory):
    try:
        process = subprocess.Popen(["pm2", "ls"], stdout=subprocess.PIPE, shell=True)
        output, _ = process.communicate()
        output_str = output.decode("utf-8")
        if added_folders:
            for folder in added_folders:
                if folder not in output_str:
                    folder_full_path = os.path.join(directory, folder)
                    pm2_command = f"pm2 start python --name {folder} --watch -- -m bot"
                    time.sleep(30)
                    subprocess.run(
                        pm2_command, shell=True, cwd=folder_full_path, encoding="utf-8"
                    )
                else:
                    print("Нет новых папок для добавления в pm2.")
        else:
            print("Нет новых папок для добавления в pm2.")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при запуске процесса: {e}")


def delete_folders_from_pm2(removed_folders, directory):
    try:
        process = subprocess.Popen(["pm2", "ls"], stdout=subprocess.PIPE, shell=True)
        output, _ = process.communicate()
        output_str = output.decode("utf-8")
        if removed_folders:
            for folder in removed_folders:
                if folder in output_str:
                    pm2_command = f"pm2 delete {folder}"
                    subprocess.run(
                        pm2_command, shell=True, cwd=directory, encoding="utf-8"
                    )
        else:
            print("Нет папок для удаления из pm2.")
    except Exception as e:
        print(f"Ошибка выполнения команды: ")
        print(f"{e}")


def monitor_folder(directory):
    while True:
        current_processes = get_pm2_processes()
        added_folders = [
            folder
            for folder in os.listdir(directory)
            if folder not in current_processes
        ]
        removed_folders = [
            folder
            for folder in current_processes
            if folder not in os.listdir(directory)
        ]
        if added_folders:
            add_folders_to_pm2(added_folders, directory)
        if removed_folders:
            delete_folders_from_pm2(removed_folders, directory)
        time.sleep(5)


if __name__ == "__main__":
    monitor_folder(get_bot_directory())
