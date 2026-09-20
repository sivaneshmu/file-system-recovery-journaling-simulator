import os
import math
import time

from virtual_disk import VirtualDisk
from file_manager import FileManager
from directory_manager import DirectoryManager
from journal_manager import JournalManager
from crash_simulator import CrashSimulator
from recovery_manager import RecoveryManager
from consistency_checker import ConsistencyChecker
from performance_analyzer import PerformanceAnalyzer


class FileSystemSystem:

    def __init__(self):

        self.disk = VirtualDisk(
            total_blocks=32,
            block_size=1024
        )

        self.file_manager = FileManager(
            self.disk
        )

        self.directory_manager = DirectoryManager(
            self.file_manager
        )

        journal_file = "data/integration_journal.log"

        # Start every demonstration with a clean journal.
        if os.path.exists(journal_file):
            os.remove(journal_file)

        self.journal_manager = JournalManager(
            journal_file
        )

        self.crash_simulator = CrashSimulator(
            self.disk,
            self.journal_manager
        )

        self.recovery_manager = RecoveryManager(
            self.disk,
            self.journal_manager
        )

        self.consistency_checker = ConsistencyChecker(
            self.disk,
            self.file_manager,
            self.directory_manager,
            self.journal_manager
        )

        self.performance_analyzer = PerformanceAnalyzer()


    # =====================================================
    # CREATE DIRECTORY
    # =====================================================

    def create_directory(self, path):

        start = time.perf_counter()

        self.directory_manager.create_directory(
            path
        )

        elapsed = (
            time.perf_counter() - start
        )

        self.performance_analyzer.record_operation_time(
            "Create Directory",
            elapsed
        )


    # =====================================================
    # CREATE FILE
    # WRITE-AHEAD LOGGING
    # =====================================================

    def create_file(
        self,
        file_name,
        size,
        content,
        directory="/"
    ):

        start = time.perf_counter()

        if size <= 0:
            raise ValueError(
                "File size must be greater than 0."
            )

        # -------------------------------------------------
        # Determine the number of blocks required.
        # -------------------------------------------------

        required_blocks = math.ceil(
            size / self.disk.block_size
        )

        free_blocks = (
            self.disk.get_free_blocks()
        )

        if len(free_blocks) < required_blocks:
            raise RuntimeError(
                "Not enough free blocks to create the file."
            )

        planned_blocks = free_blocks[
            :required_blocks
        ]

        # -------------------------------------------------
        # WRITE-AHEAD LOG
        # Journal BEFORE modifying the filesystem.
        # -------------------------------------------------

        journal_start = time.perf_counter()

        transaction_id = (
            self.journal_manager.begin_transaction(
                operation="CREATE",
                file_name=file_name,
                blocks=planned_blocks,
                details={
                    "size": size,
                    "directory": directory,
                    "content": content,
                    "wal": True
                }
            )
        )

        journal_begin_elapsed = (
            time.perf_counter() - journal_start
        )

        try:

            # -------------------------------------------------
            # Apply filesystem operation.
            # -------------------------------------------------

            blocks = self.file_manager.create_file(
                file_name,
                size,
                content
            )

            self.directory_manager.add_file(
                directory,
                file_name
            )

            # -------------------------------------------------
            # Store the actual allocated blocks in the
            # transaction, when the journal structure allows it.
            # -------------------------------------------------

            try:

                transaction = (
                    self.journal_manager._find_transaction(
                        transaction_id
                    )
                )

                if (
                    transaction is not None
                    and isinstance(blocks, list)
                ):
                    transaction["blocks"] = blocks

            except Exception:
                pass

            # -------------------------------------------------
            # COMMIT
            # -------------------------------------------------

            commit_start = time.perf_counter()

            self.journal_manager.commit_transaction(
                transaction_id
            )

            journal_commit_elapsed = (
                time.perf_counter() - commit_start
            )

            elapsed = (
                time.perf_counter() - start
            )

            journal_elapsed = (
                journal_begin_elapsed +
                journal_commit_elapsed
            )

            self.performance_analyzer.record_operation_time(
                "Create File",
                elapsed
            )

            self.performance_analyzer.record_operation_time(
                "Journal Transaction",
                journal_elapsed
            )

            return transaction_id

        except Exception:

            # Failed transaction remains recoverable.
            try:

                self.journal_manager.mark_incomplete(
                    transaction_id
                )

            except Exception:
                pass

            raise


    # =====================================================
    # MODIFY FILE
    # WRITE-AHEAD LOGGING
    # =====================================================

    def modify_file(
        self,
        file_name,
        content
    ):

        start = time.perf_counter()

        # -------------------------------------------------
        # Get metadata before modification.
        # -------------------------------------------------

        metadata = (
            self.file_manager.get_metadata(
                file_name
            )
        )

        old_blocks = list(
            metadata["blocks"]
        )

        old_size = metadata["size"]

        # -------------------------------------------------
        # WRITE-AHEAD LOG
        # -------------------------------------------------

        journal_start = time.perf_counter()

        transaction_id = (
            self.journal_manager.begin_transaction(
                operation="MODIFY",
                file_name=file_name,
                blocks=old_blocks,
                details={
                    "old_size": old_size,
                    "new_size": len(content),
                    "old_blocks": old_blocks,
                    "wal": True
                }
            )
        )

        journal_begin_elapsed = (
            time.perf_counter() - journal_start
        )

        try:

            # -------------------------------------------------
            # Apply modification.
            # -------------------------------------------------

            self.file_manager.modify_file(
                file_name,
                content
            )

            # -------------------------------------------------
            # COMMIT
            # -------------------------------------------------

            commit_start = time.perf_counter()

            self.journal_manager.commit_transaction(
                transaction_id
            )

            journal_commit_elapsed = (
                time.perf_counter() - commit_start
            )

            elapsed = (
                time.perf_counter() - start
            )

            journal_elapsed = (
                journal_begin_elapsed +
                journal_commit_elapsed
            )

            self.performance_analyzer.record_operation_time(
                "Modify File",
                elapsed
            )

            self.performance_analyzer.record_operation_time(
                "Journal Transaction",
                journal_elapsed
            )

            return transaction_id

        except Exception:

            try:

                self.journal_manager.mark_incomplete(
                    transaction_id
                )

            except Exception:
                pass

            raise


    # =====================================================
    # DELETE FILE
    # WRITE-AHEAD LOGGING
    # =====================================================

    def delete_file(
        self,
        file_name
    ):

        start = time.perf_counter()

        # -------------------------------------------------
        # Get metadata before deleting.
        # -------------------------------------------------

        metadata = (
            self.file_manager.get_metadata(
                file_name
            )
        )

        old_blocks = list(
            metadata["blocks"]
        )

        # -------------------------------------------------
        # WRITE-AHEAD LOG
        # -------------------------------------------------

        journal_start = time.perf_counter()

        transaction_id = (
            self.journal_manager.begin_transaction(
                operation="DELETE",
                file_name=file_name,
                blocks=old_blocks,
                details={
                    "old_size": metadata["size"],
                    "old_blocks": old_blocks,
                    "wal": True
                }
            )
        )

        journal_begin_elapsed = (
            time.perf_counter() - journal_start
        )

        try:

            # -------------------------------------------------
            # Remove file from directory.
            # -------------------------------------------------

            for (
                path,
                directory
            ) in self.directory_manager.directories.items():

                if file_name in directory["files"]:

                    self.directory_manager.remove_file(
                        path,
                        file_name
                    )

                    break

            # -------------------------------------------------
            # Delete from file system.
            # -------------------------------------------------

            self.file_manager.delete_file(
                file_name
            )

            # -------------------------------------------------
            # COMMIT
            # -------------------------------------------------

            commit_start = time.perf_counter()

            self.journal_manager.commit_transaction(
                transaction_id
            )

            journal_commit_elapsed = (
                time.perf_counter() - commit_start
            )

            elapsed = (
                time.perf_counter() - start
            )

            journal_elapsed = (
                journal_begin_elapsed +
                journal_commit_elapsed
            )

            self.performance_analyzer.record_operation_time(
                "Delete File",
                elapsed
            )

            self.performance_analyzer.record_operation_time(
                "Journal Transaction",
                journal_elapsed
            )

            return transaction_id

        except Exception:

            try:

                self.journal_manager.mark_incomplete(
                    transaction_id
                )

            except Exception:
                pass

            raise


    # =====================================================
    # CRASH SIMULATION
    # =====================================================

    def simulate_crash(
        self,
        file_name,
        blocks
    ):

        start = time.perf_counter()

        # -------------------------------------------------
        # Write transaction to journal FIRST.
        # -------------------------------------------------

        transaction_id = (
            self.journal_manager.begin_transaction(
                operation="CREATE",
                file_name=file_name,
                blocks=blocks,
                details={
                    "crash_test": True,
                    "wal": True
                }
            )
        )

        try:

            # -------------------------------------------------
            # Partially apply the simulated filesystem update.
            # -------------------------------------------------

            for block_id in blocks:

                if (
                    0 <= block_id
                    < self.disk.total_blocks
                ):

                    block = self.disk.blocks[block_id]

                    if block["status"] == self.disk.FREE:

                        block["status"] = self.disk.USED
                        block["file"] = file_name

            # -------------------------------------------------
            # Deliberately simulate crash.
            # -------------------------------------------------

            result = (
                self.crash_simulator.simulate_crash(
                    transaction_id
                )
            )

            elapsed = (
                time.perf_counter() - start
            )

            self.performance_analyzer.record_operation_time(
                "Crash Simulation",
                elapsed
            )

            return result

        except Exception:

            try:

                self.journal_manager.mark_incomplete(
                    transaction_id
                )

            except Exception:
                pass

            raise


    # =====================================================
    # RECOVERY
    # =====================================================

    def recover(self):

        start = time.perf_counter()

        result = (
            self.recovery_manager.recover()
        )

        # Recovery completed.
        self.crash_simulator.reset()

        elapsed = (
            time.perf_counter() - start
        )

        self.performance_analyzer.record_operation_time(
            "Recovery",
            elapsed
        )

        return result


    # =====================================================
    # CONSISTENCY CHECK
    # =====================================================

    def check_consistency(self):

        return (
            self.consistency_checker.check()
        )


    # =====================================================
    # PERFORMANCE REPORT
    # =====================================================

    def performance_report(self):

        report = (
            self.performance_analyzer.generate_report(
                self.disk,
                self.journal_manager
            )
        )

        self.performance_analyzer.display_report(
            report
        )

        return report


    # =====================================================
    # DISPLAY SYSTEM STATE
    # =====================================================

    def display_system_state(self):

        print(
            "\n" + "=" * 70
        )

        print(
            "CURRENT FILE SYSTEM STATE"
        )

        print(
            "=" * 70
        )

        print("\nFiles:")

        print(
            self.file_manager.list_files()
        )

        print("\nDirectories:")

        print(
            list(
                self.directory_manager.directories.keys()
            )
        )

        print("\nJournal:")

        self.journal_manager.display_journal()

        print("\nDisk:")

        self.disk.display_disk()


# =========================================================
# INTEGRATION DEMONSTRATION
# =========================================================

def run_integration_demo():

    system = FileSystemSystem()

    print(
        "=" * 70
    )

    print(
        "FILE SYSTEM RECOVERY AND JOURNALING SIMULATOR"
    )

    print(
        "INTEGRATED SYSTEM DEMONSTRATION"
    )

    print(
        "=" * 70
    )


    # -----------------------------------------------------
    # STEP 1
    # Directory creation
    # -----------------------------------------------------

    print(
        "\n[1] Creating directory..."
    )

    system.create_directory(
        "/documents"
    )

    print(
        "Directory '/documents' created."
    )


    # -----------------------------------------------------
    # STEP 2
    # File creation
    # -----------------------------------------------------

    print(
        "\n[2] Creating file..."
    )

    transaction_id = (
        system.create_file(
            file_name="report.txt",
            size=2500,
            content="Operating Systems Lab Project",
            directory="/documents"
        )
    )

    print(
        f"report.txt created successfully "
        f"(TX{transaction_id:03d})."
    )


    # -----------------------------------------------------
    # STEP 3
    # File modification
    # -----------------------------------------------------

    print(
        "\n[3] Modifying file..."
    )

    transaction_id = (
        system.modify_file(
            "report.txt",
            "File System Recovery and Journaling Simulator"
        )
    )

    print(
        f"report.txt modified successfully "
        f"(TX{transaction_id:03d})."
    )


    # -----------------------------------------------------
    # STEP 4
    # Consistency before crash
    # -----------------------------------------------------

    print(
        "\n[4] Checking consistency..."
    )

    system.check_consistency()


    # -----------------------------------------------------
    # STEP 5
    # Crash simulation
    # -----------------------------------------------------

    print(
        "\n[5] Creating crash scenario..."
    )

    crash_blocks = (
        system.disk.get_free_blocks()[:3]
    )

    print(
        "Blocks selected for crash simulation:",
        crash_blocks
    )

    crash_result = (
        system.simulate_crash(
            "crash_demo.txt",
            crash_blocks
        )
    )

    print(
        "\nCrash result:",
        crash_result
    )

    system.crash_simulator.display_crash_status()


    # -----------------------------------------------------
    # STEP 6
    # Consistency after crash
    # -----------------------------------------------------

    print(
        "\n[6] Checking consistency after crash..."
    )

    system.check_consistency()


    # -----------------------------------------------------
    # STEP 7
    # Recovery
    # -----------------------------------------------------

    print(
        "\n[7] Recovering file system..."
    )

    system.recover()

    print(
        "\nSystem status after recovery:"
    )

    system.crash_simulator.display_crash_status()


    # -----------------------------------------------------
    # STEP 8
    # Consistency after recovery
    # -----------------------------------------------------

    print(
        "\n[8] Checking consistency after recovery..."
    )

    system.check_consistency()


    # -----------------------------------------------------
    # STEP 9
    # Performance analysis
    # -----------------------------------------------------

    print(
        "\n[9] Performance analysis..."
    )

    system.performance_report()


    # -----------------------------------------------------
    # STEP 10
    # Final system state
    # -----------------------------------------------------

    print(
        "\n[10] Final system state..."
    )

    system.display_system_state()

    print(
        "\n" + "=" * 70
    )

    print(
        "INTEGRATION DEMONSTRATION COMPLETED"
    )

    print(
        "=" * 70
    )


# =========================================================
# PROGRAM ENTRY POINT
# =========================================================

if __name__ == "__main__":

    run_integration_demo()