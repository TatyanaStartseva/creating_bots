from dotenv import load_dotenv
from aiohttp import web
from pm2_bots_manager import stop_processing, directory_path
import os
import requests
import git
import shutil
import json
import uuid
import aiofiles

load_dotenv()
REMOVE_SENT_CONFIRMATION = os.getenv("REMOVE_SENT_CONFIRMATION")
DATABASE_URI = os.getenv("DATABASE_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_COLLECTION = os.getenv("DATABASE_COLLECTION")
repo_url = "https://github.com/TatyanaStartseva/mega_bot"


def get_bot_directory():
    directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "bots"))
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def get_video_directory():
    directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "video"))
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


async def clone_repo(bot_token, data):
    try:
        bot_token_str = str(bot_token).replace("!", ":")
        clone_path = os.path.join(get_bot_directory(), bot_token)
        data["bot_token"] = bot_token_str
        if not os.path.exists(clone_path):
            os.makedirs(clone_path)
        git.Repo.clone_from(repo_url, clone_path)
        with open(f"{clone_path}\\setup.json", "w") as f:
            json.dump(data, f)
        with open(f"{clone_path}\\.env", "w") as f:
            f.write(
                f"REMOVE_SENT_CONFIRMATION = {REMOVE_SENT_CONFIRMATION}\n DATABASE_URI ={DATABASE_URI}\n DATABASE_NAME= {DATABASE_NAME}\n DATABASE_COLLECTION= {str(bot_token_str)}\n"
            )
    except Exception as e:
        print(f"{e}")
        return web.Response(text=f"{e}")


async def update_bot(requests):
    try:
        data = await requests.json()
        bot_token = requests.match_info["id"]
        required_keys = ["admin_chat_id", "name", "steps"]
        for key in required_keys:
            if key not in data:
                return web.Response(text=f"Отсутствует ключ '{key}' в данных")

        if not isinstance(data["admin_chat_id"], int):
            return web.Response(text="Значение 'admin_chat_id' должно быть числом")

        if not isinstance(data["name"], str):
            return web.Response(text="Значение 'name' должно быть строкой")

        if not isinstance(data["steps"], list):
            return web.Response(text="Значение 'steps' должно быть списком")

        for step in data["steps"]:
            if not isinstance(step, dict):
                return web.Response(
                    text="Элементы списка 'steps' должны быть словарями"
                )
            if "type" not in step:
                return web.Response(
                    text="Каждый элемент в списке 'steps' должен содержать ключ 'type'"
                )
            allowed_types = ["text", "video", "website", "zoomcall"]
            if not any(step_type in allowed_types for step_type in step["type"]):
                return web.Response(
                    text="Значение ключа 'type' должно быть одним из: 'text', 'video', 'website', 'zoomcall'"
                )

        data["bot_token"] = str(bot_token).replace("!", ":")
        bot_number, bot_token = bot_token.split(":")
        bot_token_str = f"{bot_number}!{bot_token}"
        exist_bot_path = os.path.join(get_bot_directory(), bot_token_str)
        if os.path.exists(exist_bot_path):
            setup_json_path = os.path.join(exist_bot_path, "setup.json")
            if os.path.exists(setup_json_path):
                os.remove(setup_json_path)
                with open(f"{setup_json_path}", "w") as f:
                    json.dump(data, f)
            else:
                with open(f"{setup_json_path}", "w") as f:
                    json.dump(data, f)
        else:
            return web.Response(
                text=f"Бот с токеном {exist_bot_path} не найден. Добавьте бота."
            )
        return web.Response(text="Обновление завершено")
    except Exception as e:
        print(f"{e}")
        return web.Response(text=f"{e}")


async def bot_info(requests):
    try:
        bot_token = requests.match_info["id"]
        bot_token_str = str(bot_token)
        bot_number, bot_token = bot_token.split(":")
        bot_token_str = f"{bot_number}!{bot_token}"
        exist_bot_path = os.path.join(get_bot_directory(), bot_token_str)
        if os.path.exists(exist_bot_path):
            setup_json_path = os.path.join(exist_bot_path, "setup.json")
            with open(setup_json_path, "r") as file:
                setup_data = json.load(file)
                return web.json_response(setup_data)
        else:
            return web.Response(text="Бот не найден")
    except Exception as e:
        print(f"{e}")
        return web.Response(text=f"{e}")


async def delete_bot(requests):
    try:
        bot_token = requests.match_info["id"]
        bot_token_str = str(bot_token)
        bot_number, bot_token = bot_token.split(":")
        bot_token_str = f"{bot_number}!{bot_token}"
        stop_processing(bot_token_str)
        exist_bot_path = os.path.join(get_bot_directory(), bot_token_str)
        git_dir = os.path.join(exist_bot_path, ".git")
        os.system(f'attrib -h "{git_dir}"')
        files_list = os.listdir(f"{git_dir}\\objects\\pack\\")
        if os.path.exists(git_dir):
            for file_name in files_list:
                if file_name.endswith(".idx"):
                    file_path = os.path.join(f"{git_dir}\\objects\\pack\\", file_name)
                    os.chmod(file_path, 0o777)
                if file_name.endswith(".pack"):
                    file_path = os.path.join(f"{git_dir}\\objects\\pack\\", file_name)
                    os.chmod(file_path, 0o777)
            shutil.rmtree(git_dir)
        if os.path.exists(exist_bot_path):
            shutil.rmtree(exist_bot_path)
            return web.Response(text="Бот удален")
        else:
            return web.Response(text=f"Бота {bot_token}, не существует")
    except Exception as e:
        print(f"{e}")
        return web.Response(text=f"{e}")


async def create_bot(requests):
    try:
        bot_token = requests.match_info["id"]
        data = await requests.json()

        required_keys = ["admin_chat_id", "name", "steps"]
        for key in required_keys:
            if key not in data:
                return web.Response(text=f"Отсутствует ключ '{key}' в данных")

        if not isinstance(data["admin_chat_id"], int):
            return web.Response(text="Значение 'admin_chat_id' должно быть числом")

        if not isinstance(data["name"], str):
            return web.Response(text="Значение 'name' должно быть строкой")

        if not isinstance(data["steps"], list):
            return web.Response(text="Значение 'steps' должно быть списком")

        for step in data["steps"]:
            if not isinstance(step, dict):
                return web.Response(
                    text="Элементы списка 'steps' должны быть словарями"
                )
            if "type" not in step:
                return web.Response(
                    text="Каждый элемент в списке 'steps' должен содержать ключ 'type'"
                )
            allowed_types = ["text", "video", "website", "zoomcall"]
            if not any(step_type in allowed_types for step_type in step["type"]):
                return web.Response(
                    text="Значение ключа 'type' должно быть одним из: 'text', 'video', 'website', 'zoomcall'"
                )

        bot_token = requests.match_info["id"]
        data = await requests.json()
        bot_token_str = str(bot_token)
        bot_number, bot_token = bot_token.split(":")
        bot_token_str = f"{bot_number}!{bot_token}"
        exist_bot_path = os.path.join(get_bot_directory(), bot_token_str)
        if not os.path.exists(exist_bot_path):
            await clone_repo(bot_token_str, data)
            return web.Response(text="Бот создан")
        else:
            return web.Response(
                text=f"Этот бот уже существует {bot_token}, папка должн называться {bot_token_str}"
            )
    except Exception as e:
        print(f"{e}")
        return web.Response(text=f"{e}")


async def get_video_path(requests):
    try:
        video_name = requests.query.get("video_name")
        path_video = get_video_directory()
        video_path = os.path.join(path_video, video_name + ".mp4")
        if os.path.exists(video_path):
            response = web.FileResponse(video_path)
            response.headers["Content-Type"] = "video/mp4"
            return response
        else:
            return web.json_response({"error": "Этого файла нет"})
    except Exception as e:
        return web.json_response(
            {"error": f"Произошла ошибка при загрузке видео: {str(e)}"}
        )


async def upload_video(request):
    try:
        data = await request.post()
        video = data["video"].file
        filename = str(uuid.uuid4())
        path_video = get_video_directory()
        filepath = path_video + "\\" + filename + ".mp4"
        async with aiofiles.open(filepath, "wb") as f:
            while True:
                chunk = video.read(1024)
                if not chunk:
                    break
                await f.write(chunk)
        return web.json_response(
            {
                "uuid": f"{filename}",
                "message": "Видео успешно скачено. Его название соответвует ключу uuid",
            }
        )
    except Exception as e:
        return web.json_response(
            {"error": f"Произошла ошибка при загрузке видео: {str(e)}"}
        )


async def bots_info(requests):
    try:
        dirs_list = []
        path = get_bot_directory()
        for dir in next(os.walk(path))[1]:
            exist_bot_path = f"{path}\\{dir}"
            if os.path.exists(exist_bot_path):
                setup_json_path = os.path.join(exist_bot_path, "setup.json")
                with open(setup_json_path, "r") as file:
                    info = json.load(file)
                    dirs_list.append(info)
        return web.json_response(dirs_list)
    except Exception as e:
        print(f"{e}")
        return web.Response(text=f"{e}")


app = web.Application(client_max_size=1024**3)
app.router.add_get("/get_video_path", get_video_path)
app.router.add_get("/bots/{id}", bot_info)
app.router.add_get("/bots", bots_info)
app.router.add_post("/bots/{id}", create_bot)
app.router.add_patch("/bots/{id}", update_bot)
app.router.add_delete("/bots/{id}", delete_bot)
app.router.add_post("/upload", upload_video)
web.run_app(app, port=80)
