import os
import shutil


def open_file(filepath):
    filepath = os.path.expanduser(filepath)
    try:
        os.startfile(filepath)
        return True, f"Opening {os.path.basename(filepath)}."
    except FileNotFoundError:
        return False, f"File not found: {filepath}"
    except Exception as e:
        return False, f"Failed to open file: {e}"


def list_files(directory=None):
    if directory is None:
        directory = os.path.expanduser("~\\Desktop")
    else:
        directory = os.path.expanduser(directory)
    try:
        items = os.listdir(directory)
        folders = [d for d in items if os.path.isdir(os.path.join(directory, d))]
        files = [f for f in items if os.path.isfile(os.path.join(directory, f))]
        result = []
        if folders:
            result.append(f"Folders: {', '.join(folders[:10])}")
        if files:
            result.append(f"Files: {', '.join(files[:10])}")
        if not result:
            return True, "Directory is empty."
        return True, ". ".join(result)
    except Exception as e:
        return False, f"Failed to list files: {e}"


def create_folder(name, location=None):
    if location is None:
        location = os.path.expanduser("~\\Desktop")
    else:
        location = os.path.expanduser(location)
    folder_path = os.path.join(location, name)
    try:
        os.makedirs(folder_path, exist_ok=True)
        return True, f"Created folder '{name}' on Desktop."
    except Exception as e:
        return False, f"Failed to create folder: {e}"


def create_file(name, location=None):
    if location is None:
        location = os.path.expanduser("~\\Desktop")
    else:
        location = os.path.expanduser(location)
    file_path = os.path.join(location, name)
    try:
        with open(file_path, "w") as f:
            f.write("")
        return True, f"Created file '{name}' on Desktop."
    except Exception as e:
        return False, f"Failed to create file: {e}"


def delete_file(filepath):
    filepath = os.path.expanduser(filepath)
    try:
        if os.path.isdir(filepath):
            shutil.rmtree(filepath)
            return True, f"Deleted folder '{os.path.basename(filepath)}'."
        else:
            os.remove(filepath)
            return True, f"Deleted file '{os.path.basename(filepath)}'."
    except FileNotFoundError:
        return False, f"File not found: {filepath}"
    except Exception as e:
        return False, f"Failed to delete: {e}"


def move_file(source, destination):
    source = os.path.expanduser(source)
    destination = os.path.expanduser(destination)
    try:
        shutil.move(source, destination)
        return True, f"Moved {os.path.basename(source)} to {destination}."
    except Exception as e:
        return False, f"Failed to move file: {e}"


def copy_file(source, destination):
    source = os.path.expanduser(source)
    destination = os.path.expanduser(destination)
    try:
        if os.path.isdir(source):
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)
        return True, f"Copied {os.path.basename(source)} to {destination}."
    except Exception as e:
        return False, f"Failed to copy file: {e}"


def search_files(query, directory=None):
    if directory is None:
        directory = os.path.expanduser("~")
    results = []
    try:
        for root, dirs, files in os.walk(directory):
            for f in files:
                if query.lower() in f.lower():
                    results.append(os.path.join(root, f))
            if len(results) >= 10:
                break
        if results:
            return True, f"Found: {', '.join([os.path.basename(r) for r in results])}"
        return True, f"No files found matching '{query}'."
    except Exception as e:
        return False, f"Search failed: {e}"
