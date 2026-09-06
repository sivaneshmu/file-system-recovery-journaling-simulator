class DirectoryManager:
    def __init__(self, file_manager):
        self.file_manager = file_manager
        self.directories = {
            "/": {
                "name": "/",
                "parent": None,
                "directories": [],
                "files": []
            }
        }

    def create_directory(self, path):
        path = self._normalize_path(path)

        if path == "/":
            raise ValueError("Root directory already exists.")

        if path in self.directories:
            raise ValueError("Directory already exists.")

        parent = self._get_parent(path)

        if parent not in self.directories:
            raise FileNotFoundError("Parent directory does not exist.")

        name = path.split("/")[-1]

        self.directories[path] = {
            "name": name,
            "parent": parent,
            "directories": [],
            "files": []
        }

        self.directories[parent]["directories"].append(name)

    def delete_directory(self, path):
        path = self._normalize_path(path)

        if path == "/":
            raise ValueError("Root directory cannot be deleted.")

        if path not in self.directories:
            raise FileNotFoundError("Directory does not exist.")

        directory = self.directories[path]

        if directory["directories"] or directory["files"]:
            raise ValueError("Directory is not empty.")

        parent = directory["parent"]
        name = directory["name"]

        self.directories[parent]["directories"].remove(name)
        del self.directories[path]

    def add_file(self, directory, file_name):
        directory = self._normalize_path(directory)

        if directory not in self.directories:
            raise FileNotFoundError("Directory does not exist.")

        if file_name not in self.file_manager.files:
            raise FileNotFoundError("File does not exist.")

        if file_name not in self.directories[directory]["files"]:
            self.directories[directory]["files"].append(file_name)

    def remove_file(self, directory, file_name):
        directory = self._normalize_path(directory)

        if directory not in self.directories:
            raise FileNotFoundError("Directory does not exist.")

        if file_name in self.directories[directory]["files"]:
            self.directories[directory]["files"].remove(file_name)

    def move_file(self, file_name, source, destination):
        source = self._normalize_path(source)
        destination = self._normalize_path(destination)

        if source not in self.directories:
            raise FileNotFoundError("Source directory does not exist.")

        if destination not in self.directories:
            raise FileNotFoundError("Destination directory does not exist.")

        if file_name not in self.directories[source]["files"]:
            raise FileNotFoundError("File not found in source directory.")

        if file_name in self.directories[destination]["files"]:
            raise ValueError("File already exists in destination directory.")

        self.directories[source]["files"].remove(file_name)
        self.directories[destination]["files"].append(file_name)

    def list_directory(self, path="/"):
        path = self._normalize_path(path)

        if path not in self.directories:
            raise FileNotFoundError("Directory does not exist.")

        directory = self.directories[path]

        return {
            "directories": directory["directories"].copy(),
            "files": directory["files"].copy()
        }

    def get_directory_metadata(self, path):
        path = self._normalize_path(path)

        if path not in self.directories:
            raise FileNotFoundError("Directory does not exist.")

        return self.directories[path].copy()

    def _normalize_path(self, path):
        if not path:
            return "/"

        if not path.startswith("/"):
            path = "/" + path

        path = path.rstrip("/")

        return path if path else "/"

    def _get_parent(self, path):
        if path == "/":
            return None

        parent = path.rsplit("/", 1)[0]

        return parent if parent else "/"


def test_directory_manager():
    from virtual_disk import VirtualDisk
    from file_manager import FileManager

    disk = VirtualDisk(total_blocks=16, block_size=1024)
    file_manager = FileManager(disk)
    directory_manager = DirectoryManager(file_manager)

    print("Creating directories...")

    directory_manager.create_directory("/documents")
    directory_manager.create_directory("/documents/projects")

    print("Directories created.")

    print("\nCreating file...")
    file_manager.create_file(
        "report.txt",
        1500,
        "Operating Systems Project"
    )

    directory_manager.add_file("/documents/projects", "report.txt")

    print("File added to /documents/projects")

    print("\nRoot directory:")
    print(directory_manager.list_directory("/"))

    print("\n/documents:")
    print(directory_manager.list_directory("/documents"))

    print("\n/documents/projects:")
    print(directory_manager.list_directory("/documents/projects"))

    print("\nMoving file to /documents...")
    directory_manager.move_file(
        "report.txt",
        "/documents/projects",
        "/documents"
    )

    print(directory_manager.list_directory("/documents"))
    print(directory_manager.list_directory("/documents/projects"))

    print("\nDeleting file...")
    directory_manager.remove_file("/documents", "report.txt")
    file_manager.delete_file("report.txt")

    print("\nDeleting directories...")
    directory_manager.delete_directory("/documents/projects")
    directory_manager.delete_directory("/documents")

    print("Directories deleted.")

    print("\nFinal root directory:")
    print(directory_manager.list_directory("/"))


if __name__ == "__main__":
    test_directory_manager()