import os
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

    def create_directory(self, path):
        start = time.perf_counter()

        self.directory_manager.create_directory(path)

        elapsed = time.perf_counter() - start

        self.performance_analyzer.record_operation_time(
            "Create Directory",
            elapsed
        )

    def create_file(
        self,
        file_name,
        size,
        content,
        directory="/"
    ):
        start = time.perf_counter()

        blocks = self.file_manager.create_file(
            file_name,
            size,
            content
        )

        self.directory_manager.add_file(
            directory,
            file_name
        )

        elapsed = time.perf_counter() - start

        self.performance_analyzer.record_operation_time(
            "Create File",
            elapsed
        )

        # Record the transaction.
        journal_start = time.perf_counter()

        transaction_id = self.journal_manager.begin_transaction(
            operation="CREATE",
            file_name=file_name,
            blocks=blocks,
            details={
                "size": size,
                "directory": directory
            }
        )

        self.journal_manager.commit_transaction(
            transaction_id
        )

        journal_elapsed = (
            time.perf_counter() - journal_start
        )

        self.performance_analyzer.record_operation_time(
            "Journal Transaction",
            journal_elapsed
        )

        return transaction_id

    def modify_file(self, file_name, content):
        start = time.perf_counter()

        metadata = self.file_manager.get_metadata(
            file_name
        )

        transaction_id = self.journal_manager.begin_transaction(
            operation="MODIFY",
            file_name=file_name,
            blocks=metadata["blocks"],
            details={
                "old_size": metadata["size"],
                "new_size": len(content)
            }
        )

        self.file_manager.modify_file(
            file_name,
            content
        )

        self.journal_manager.commit_transaction(
            transaction_id
        )

        elapsed = time.perf_counter() - start

        self.performance_analyzer.record_operation_time(
            "Modify File",
            elapsed
        )

        return transaction_id

    def delete_file(self, file_name):
        start = time.perf_counter()

        metadata = self.file_manager.get_metadata(
            file_name
        )

        transaction_id = self.journal_manager.begin_transaction(
            operation="DELETE",
            file_name=file_name,
            blocks=metadata["blocks"]
        )

        # Remove the file from its directory.
        for path, directory in self.directory_manager.directories.items():
            if file_name in directory["files"]:
                self.directory_manager.remove_file(
                    path,
                    file_name
                )
                break

        self.file_manager.delete_file(
            file_name
        )

        self.journal_manager.commit_transaction(
            transaction_id
        )

        elapsed = time.perf_counter() - start

        self.performance_analyzer.record_operation_time(
            "Delete File",
            elapsed
        )

        return transaction_id

    def simulate_crash(self, file_name, blocks):
        start = time.perf_counter()

        transaction_id = self.journal_manager.begin_transaction(
            operation="CREATE",
            file_name=file_name,
            blocks=blocks,
            details={
                "crash_test": True
            }
        )

        # Partially apply the simulated operation.
        for block_id in blocks:
            if 0 <= block_id < self.disk.total_blocks:
                block = self.disk.blocks[block_id]

                if block["status"] == self.disk.FREE:
                    block["status"] = self.disk.USED
                    block["file"] = file_name

        result = self.crash_simulator.simulate_crash(
            transaction_id
        )

        elapsed = time.perf_counter() - start

        self.performance_analyzer.record_operation_time(
            "Crash Simulation",
            elapsed
        )

        return result

    def recover(self):
        start = time.perf_counter()

        result = self.recovery_manager.recover()

        # Recovery is complete, so restore normal system state.
        self.crash_simulator.reset()

        elapsed = time.perf_counter() - start

        self.performance_analyzer.record_operation_time(
            "Recovery",
            elapsed
        )

        return result

    def check_consistency(self):
        return self.consistency_checker.check()

    def performance_report(self):
        report = self.performance_analyzer.generate_report(
            self.disk,
            self.journal_manager
        )

        self.performance_analyzer.display_report(
            report
        )

        return report

    def display_system_state(self):
        print("\n" + "=" * 70)
        print("CURRENT FILE SYSTEM STATE")
        print("=" * 70)

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


def run_integration_demo():
    system = FileSystemSystem()

    print("=" * 70)
    print("FILE SYSTEM RECOVERY AND JOURNALING SIMULATOR")
    print("INTEGRATED SYSTEM DEMONSTRATION")
    print("=" * 70)

    # ---------------------------------------------------------
    # Step 1: Directory creation
    # ---------------------------------------------------------

    print("\n[1] Creating directory...")

    system.create_directory(
        "/documents"
    )

    print("Directory '/documents' created.")

    # ---------------------------------------------------------
    # Step 2: File creation
    # ---------------------------------------------------------

    print("\n[2] Creating file...")

    transaction_id = system.create_file(
        file_name="report.txt",
        size=2500,
        content="Operating Systems Lab Project",
        directory="/documents"
    )

    print(
        f"report.txt created successfully "
        f"(TX{transaction_id:03d})."
    )

    # ---------------------------------------------------------
    # Step 3: File modification
    # ---------------------------------------------------------

    print("\n[3] Modifying file...")

    transaction_id = system.modify_file(
        "report.txt",
        "File System Recovery and Journaling Simulator"
    )

    print(
        f"report.txt modified successfully "
        f"(TX{transaction_id:03d})."
    )

    # ---------------------------------------------------------
    # Step 4: Consistency before crash
    # ---------------------------------------------------------

    print("\n[4] Checking consistency...")

    system.check_consistency()

    # ---------------------------------------------------------
    # Step 5: Crash simulation
    # ---------------------------------------------------------

    print("\n[5] Creating crash scenario...")

    crash_blocks = (
        system.disk.get_free_blocks()[:3]
    )

    print(
        "Blocks selected for crash simulation:",
        crash_blocks
    )

    crash_result = system.simulate_crash(
        "crash_demo.txt",
        crash_blocks
    )

    print(
        "\nCrash result:",
        crash_result
    )

    system.crash_simulator.display_crash_status()

    # ---------------------------------------------------------
    # Step 6: Consistency after crash
    # ---------------------------------------------------------

    print("\n[6] Checking consistency after crash...")

    system.check_consistency()

    # ---------------------------------------------------------
    # Step 7: Recovery
    # ---------------------------------------------------------

    print("\n[7] Recovering file system...")

    system.recover()

    print("\nSystem status after recovery:")

    system.crash_simulator.display_crash_status()

    # ---------------------------------------------------------
    # Step 8: Consistency after recovery
    # ---------------------------------------------------------

    print("\n[8] Checking consistency after recovery...")

    system.check_consistency()

    # ---------------------------------------------------------
    # Step 9: Performance
    # ---------------------------------------------------------

    print("\n[9] Performance analysis...")

    system.performance_report()

    # ---------------------------------------------------------
    # Step 10: Final state
    # ---------------------------------------------------------

    print("\n[10] Final system state...")

    system.display_system_state()

    print("\n" + "=" * 70)
    print("INTEGRATION DEMONSTRATION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    run_integration_demo()