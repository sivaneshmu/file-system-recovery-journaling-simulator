from datetime import datetime


class FileManager:
    def __init__(self, virtual_disk):
        self.disk = virtual_disk
        self.files = {}

    def create_file(self, file_name, size, content=""):
        if file_name in self.files:
            raise ValueError("File already exists.")

        if size <= 0:
            raise ValueError("File size must be greater than zero.")

        blocks_required = (size + self.disk.block_size - 1) // self.disk.block_size

        blocks = self.disk.allocate_blocks(blocks_required, file_name)

        self.files[file_name] = {
            "name": file_name,
            "size": size,
            "content": content,
            "blocks": blocks,
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat()
        }

        return blocks

    def read_file(self, file_name):
        self._check_file(file_name)
        return self.files[file_name]["content"]

    def modify_file(self, file_name, content):
        self._check_file(file_name)

        self.files[file_name]["content"] = content
        self.files[file_name]["size"] = len(content)
        self.files[file_name]["modified"] = datetime.now().isoformat()

    def delete_file(self, file_name):
        self._check_file(file_name)

        blocks = self.files[file_name]["blocks"]

        self.disk.release_blocks(blocks)
        del self.files[file_name]

    def get_metadata(self, file_name):
        self._check_file(file_name)
        return self.files[file_name].copy()

    def list_files(self):
        return list(self.files.keys())

    def _check_file(self, file_name):
        if file_name not in self.files:
            raise FileNotFoundError(f"File '{file_name}' not found.")


def test_file_manager():
    from virtual_disk import VirtualDisk

    disk = VirtualDisk(total_blocks=16, block_size=1024)
    manager = FileManager(disk)

    print("Creating file...")
    blocks = manager.create_file(
        "student.txt",
        2500,
        "Operating Systems Lab Project"
    )

    print("Allocated blocks:", blocks)

    print("\nReading file:")
    print(manager.read_file("student.txt"))

    print("\nMetadata:")
    for key, value in manager.get_metadata("student.txt").items():
        print(f"{key}: {value}")

    print("\nModifying file...")
    manager.modify_file(
        "student.txt",
        "File System Recovery and Journaling Simulator"
    )

    print("New content:")
    print(manager.read_file("student.txt"))

    print("\nFiles:")
    print(manager.list_files())

    print("\nDeleting file...")
    manager.delete_file("student.txt")

    print("Files after deletion:")
    print(manager.list_files())


if __name__ == "__main__":
    test_file_manager()