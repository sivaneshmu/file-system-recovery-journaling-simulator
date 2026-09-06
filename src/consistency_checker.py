class ConsistencyChecker:
    def __init__(self, virtual_disk, file_manager, directory_manager, journal_manager):
        self.disk = virtual_disk
        self.file_manager = file_manager
        self.directory_manager = directory_manager
        self.journal_manager = journal_manager

    def check(self):
        errors = []

        self._check_block_allocation(errors)
        self._check_file_references(errors)
        self._check_directory_references(errors)
        self._check_corrupted_blocks(errors)
        self._check_journal_consistency(errors)

        result = {
            "healthy": len(errors) == 0,
            "errors": errors
        }

        self._display_result(result)

        return result

    def _check_block_allocation(self, errors):
        block_owners = {}

        for file_name, metadata in self.file_manager.files.items():
            for block_id in metadata["blocks"]:
                if block_id < 0 or block_id >= self.disk.total_blocks:
                    errors.append(
                        f"File '{file_name}' references invalid block {block_id}."
                    )
                    continue

                if block_id in block_owners:
                    errors.append(
                        f"Duplicate block allocation: "
                        f"Block {block_id} belongs to "
                        f"'{block_owners[block_id]}' and '{file_name}'."
                    )
                else:
                    block_owners[block_id] = file_name

        # Check that every file-owned block is actually marked USED
        for block_id, file_name in block_owners.items():
            block = self.disk.blocks[block_id]

            if block["status"] not in (
                self.disk.USED,
                self.disk.RECOVERED
            ):
                errors.append(
                    f"File '{file_name}' references block {block_id}, "
                    f"but its disk status is {block['status']}."
                )

            if block["file"] != file_name:
                errors.append(
                    f"Block {block_id} metadata mismatch: "
                    f"expected '{file_name}', found '{block['file']}'."
                )

    def _check_file_references(self, errors):
        referenced_blocks = set()

        for file_name, metadata in self.file_manager.files.items():
            if metadata["name"] != file_name:
                errors.append(
                    f"Metadata name mismatch for file '{file_name}'."
                )

            for block_id in metadata["blocks"]:
                referenced_blocks.add(block_id)

        # Detect orphan used/recovered blocks
        for block in self.disk.blocks:
            if block["status"] in (
                self.disk.USED,
                self.disk.RECOVERED
            ):
                if block["block_id"] not in referenced_blocks:
                    errors.append(
                        f"Orphan block detected: "
                        f"Block {block['block_id']} is allocated but "
                        f"not referenced by any file."
                    )

    def _check_directory_references(self, errors):
        for path, directory in self.directory_manager.directories.items():

            for file_name in directory["files"]:
                if file_name not in self.file_manager.files:
                    errors.append(
                        f"Directory '{path}' references missing file "
                        f"'{file_name}'."
                    )

            for directory_name in directory["directories"]:
                if path == "/":
                    child_path = "/" + directory_name
                else:
                    child_path = path + "/" + directory_name

                if child_path not in self.directory_manager.directories:
                    errors.append(
                        f"Directory '{path}' references missing "
                        f"directory '{directory_name}'."
                    )

    def _check_corrupted_blocks(self, errors):
        corrupted = self.disk.get_corrupted_blocks()

        for block_id in corrupted:
            errors.append(
                f"Corrupted block detected: Block {block_id}."
            )

    def _check_journal_consistency(self, errors):
        transactions = self.journal_manager.get_all_transactions()

        for transaction in transactions:
            status = transaction["status"]

            if status == "PENDING":
                errors.append(
                    f"Incomplete transaction still pending: "
                    f"TX{transaction['transaction_id']:03d}."
                )

            elif status == "INCOMPLETE":
                errors.append(
                    f"Incomplete transaction detected: "
                    f"TX{transaction['transaction_id']:03d}."
                )

            elif status not in (
                "COMMITTED",
                "ROLLED_BACK",
                "RECOVERED"
            ):
                errors.append(
                    f"Invalid transaction status for "
                    f"TX{transaction['transaction_id']:03d}: {status}."
                )

    def _display_result(self, result):
        print("\nCONSISTENCY CHECK")
        print("-" * 60)

        if result["healthy"]:
            print("✓ File references")
            print("✓ Directory structure")
            print("✓ Block allocation")
            print("✓ Corruption check")
            print("✓ Journal consistency")
            print("\nRESULT: FILE SYSTEM HEALTHY")
        else:
            print("✗ Inconsistencies detected:")

            for error in result["errors"]:
                print(f"  - {error}")

            print("\nRESULT: INCONSISTENT FILE SYSTEM")


def test_healthy_filesystem():
    from virtual_disk import VirtualDisk
    from file_manager import FileManager
    from directory_manager import DirectoryManager
    from journal_manager import JournalManager

    print("\n===== HEALTHY FILE SYSTEM TEST =====")

    disk = VirtualDisk(total_blocks=16, block_size=1024)
    file_manager = FileManager(disk)
    directory_manager = DirectoryManager(file_manager)
    journal = JournalManager("data/test_consistency_healthy.log")

    directory_manager.create_directory("/documents")

    file_manager.create_file(
        "report.txt",
        1500,
        "Operating Systems Project"
    )

    directory_manager.add_file(
        "/documents",
        "report.txt"
    )

    transaction_id = journal.begin_transaction(
        "CREATE",
        "report.txt",
        file_manager.files["report.txt"]["blocks"]
    )

    journal.commit_transaction(transaction_id)

    checker = ConsistencyChecker(
        disk,
        file_manager,
        directory_manager,
        journal
    )

    checker.check()


def test_inconsistent_filesystem():
    from virtual_disk import VirtualDisk
    from file_manager import FileManager
    from directory_manager import DirectoryManager
    from journal_manager import JournalManager

    print("\n===== INCONSISTENT FILE SYSTEM TEST =====")

    disk = VirtualDisk(total_blocks=16, block_size=1024)
    file_manager = FileManager(disk)
    directory_manager = DirectoryManager(file_manager)
    journal = JournalManager("data/test_consistency_bad.log")

    directory_manager.create_directory("/documents")

    file_manager.create_file(
        "report.txt",
        1500,
        "Operating Systems Project"
    )

    directory_manager.add_file(
        "/documents",
        "report.txt"
    )

    blocks = file_manager.files["report.txt"]["blocks"]

    # Create corruption
    disk.corrupt_block(blocks[0])

    # Create incomplete transaction
    transaction_id = journal.begin_transaction(
        "MODIFY",
        "report.txt",
        blocks
    )

    journal.mark_incomplete(transaction_id)

    checker = ConsistencyChecker(
        disk,
        file_manager,
        directory_manager,
        journal
    )

    checker.check()


if __name__ == "__main__":
    test_healthy_filesystem()
    test_inconsistent_filesystem()