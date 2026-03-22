from pathlib import Path

import aiofiles
import orjson
import yaml

from src.constants.color import C


def open_file(file_path):
    """
    read file at provided path and return

    Args:
        file_path (str): every text file path

    Returns:
        string
        None: file not found || parse error
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = f.read()
        return data
    except FileNotFoundError:
        print(f"{C.red}[err] File Not Found > {file_path}{C.default}")
        return None
    except Exception as e:
        print(f"{C.red}[err] Unknown Error in [open_file] func: {e}")
        return None


def save_file(filepath: str, content: str) -> bool | None:
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True

    except IOError as e:
        print(f"An I/O error occurred while saving the file: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def json_load(file_path) -> dict | None:
    """
    read json file at provided path and return

    Args:
        file_path (str): JSON file path

    Returns:
        dict or list: JSON file object.
        None: file not found || parse error
    """
    try:
        data = orjson.loads(Path(file_path).read_bytes())
        return data
    except FileNotFoundError:
        print(f"{C.yellow}ERR: File Not Found > {file_path}{C.default}")
        return None
    except orjson.JSONDecodeError:
        print(f"{C.yellow}ERR: JSON Decode Exception > {file_path}{C.default}")
        return None
    except Exception as e:
        print(f"{C.red}ERR: {e}")
        return None


def json_save(data, file_path) -> bool:
    """
    convert object(dict or list) and save as JSON file

    Args:
        data (dict or list): to save data
        file_path (str): JSON file path

    Returns:
        bool: save success True, failed to save
    """
    try:
        Path(file_path).write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2))
        return True
    except TypeError as e:
        print(f"{C.red}[err] Convertion Error > {e}")
        return False
    except Exception as e:
        print(f"{C.red}[err] Unknown Error in [json_save] func > {e}")
        return False


def yaml_open(fname):
    obj = None
    try:
        with open(f"{fname}.yml", "r", encoding="utf-8") as f:
            obj = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"[warn]: '{fname}' not found.")

    return obj


# with async


async def open_file_async(file_path):
    """
    read file at provided path and return

    Args:
        file_path (str): every text file path

    Returns:
        string
        None: file not found || parse error
    """
    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            data = await f.read()
        return data
    except FileNotFoundError:
        print(f"{C.red}[err] File Not Found > {file_path}{C.default}")
        return None
    except Exception as e:
        print(f"{C.red}[err] Unknown Error in [open_file] func: {e}")
        return None


async def save_file_async(filepath: str, content: str) -> bool:
    """
    save file (Async)
    """
    try:
        async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
            await f.write(content)
        return True

    except IOError as e:
        print(f"An I/O error occurred while saving the file: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


async def json_load_async(file_path) -> dict | None:
    """
    read json file at provided path and return

    Args:
        file_path (str): JSON file path

    Returns:
        dict or list: JSON file object.
        None: file not found || parse error
    """
    try:
        async with aiofiles.open(file_path, "rb") as f:
            content = await f.read()

        data = orjson.loads(content)
        return data

    except FileNotFoundError:
        print(f"{C.yellow}ERR: File Not Found > {file_path}{C.default}")
        return None
    except orjson.JSONDecodeError:
        print(f"{C.yellow}ERR: JSON Decode Exception > {file_path}{C.default}")
        return None
    except Exception as e:
        print(f"{C.red}ERR: {e}")
        return None


async def json_save_async(data, file_path) -> bool:
    """
    convert object(dict or list) and save as JSON file

    Args:
        data (dict or list): to save data
        file_path (str): JSON file path

    Returns:
        bool: save success True, failed to save
    """
    try:
        content = orjson.dumps(data, option=orjson.OPT_INDENT_2)

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        return True
    except TypeError as e:
        print(f"{C.red}[err] Convertion Error > {e}")
        return False
    except Exception as e:
        print(f"{C.red}[err] Unknown Error in [json_save] func > {e}")
        return False


async def yaml_open_async(fname):
    obj = None
    try:
        async with aiofiles.open(f"{fname}.yml", "r", encoding="utf-8") as f:
            content = await f.read()
        obj = yaml.safe_load(content)
    except FileNotFoundError:
        print(f"[warn]: '{fname}' not found.")
    except Exception as e:
        print(f"[err]: YAML load error > {e}")

    return obj
