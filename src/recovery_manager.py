class RecoveryManager:
    def __init__(self, virtual_disk, journal_manager):
        self.disk = virtual_disk
        self.journal = journal_manager
        self.recovery_log = []

    def recover(self):
        print("\nSTARTING FILE SYSTEM RECOVERY")
        print("-" * 60)

        # Clear the previous recovery log for a new recovery run.
        self.recovery_log = []

        incomplete = self.journal.get_incomplete_transactions()

        if not incomplete:
            print("No incomplete transactions found.")
            return self.recovery_log

        for transaction in incomplete:
            transaction_id = transaction["transaction_id"]
            operation = transaction["operation"]

            print(
                f"\nRecovering TX{transaction_id:03d} "
                f"({operation})"
            )

            if operation == "CREATE":
                self._undo_create(transaction)

            elif operation == "MODIFY":
                self._recover_modify(transaction)

            elif operation == "DELETE":
                self._redo_delete(transaction)

            else:
                print(f"Unknown operation: {operation}")

                self.recovery_log.append({
                    "transaction_id": transaction_id,
                    "action": "FAILED",
                    "reason": "Unknown operation"
                })

                continue

            self._mark_recovered(transaction_id)

        return self.recovery_log

    def _undo_create(self, transaction):
        transaction_id = transaction["transaction_id"]
        blocks = transaction["blocks"]

        print("Recovery action: UNDO CREATE")

        released_blocks = []

        for block_id in blocks:
            if 0 <= block_id < self.disk.total_blocks:
                block = self.disk.blocks[block_id]

                if block["status"] in (
                    self.disk.USED,
                    self.disk.CORRUPTED,
                    self.disk.RECOVERED
                ):
                    self.disk.release_blocks([block_id])
                    released_blocks.append(block_id)

        self.recovery_log.append({
            "transaction_id": transaction_id,
            "action": "UNDO CREATE",
            "blocks_released": released_blocks
        })

        print("Allocated blocks released.")

    def _recover_modify(self, transaction):
        transaction_id = transaction["transaction_id"]
        blocks = transaction["blocks"]

        print("Recovery action: RECOVER MODIFY")

        recovered_blocks = []

        for block_id in blocks:
            if 0 <= block_id < self.disk.total_blocks:
                block = self.disk.blocks[block_id]

                if block["status"] == self.disk.CORRUPTED:
                    self.disk.recover_block(
                        block_id,
                        transaction["file"]
                    )

                    recovered_blocks.append(block_id)

        self.recovery_log.append({
            "transaction_id": transaction_id,
            "action": "REDO/REPAIR MODIFY",
            "recovered_blocks": recovered_blocks
        })

        print("Recovered blocks:", recovered_blocks)

    def _redo_delete(self, transaction):
        transaction_id = transaction["transaction_id"]
        blocks = transaction["blocks"]

        print("Recovery action: REDO DELETE")

        released_blocks = []

        for block_id in blocks:
            if 0 <= block_id < self.disk.total_blocks:
                self.disk.release_blocks([block_id])
                released_blocks.append(block_id)

        self.recovery_log.append({
            "transaction_id": transaction_id,
            "action": "REDO DELETE",
            "blocks_released": released_blocks
        })

        print("Blocks released for deleted file.")

    def _mark_recovered(self, transaction_id):
        transaction = self.journal._find_transaction(transaction_id)

        transaction["recovery_required"] = True
        transaction["status"] = "RECOVERED"

        self.journal.save_journal()

        print(
            f"TX{transaction_id:03d} marked as RECOVERED."
        )

    def display_recovery_log(self):
        print("\nRECOVERY LOG")
        print("-" * 60)

        if not self.recovery_log:
            print("No recovery actions performed.")
            return

        for entry in self.recovery_log:
            print(
                f"TX{entry['transaction_id']:03d} | "
                f"{entry['action']}"
            )


def test_recovery_manager():
    from virtual_disk import VirtualDisk
    from journal_manager import JournalManager
    from crash_simulator import CrashSimulator

    print("Creating virtual disk...")

    disk = VirtualDisk(
        total_blocks=16,
        block_size=1024
    )

    journal = JournalManager(
        "data/test_recovery_journal.log"
    )

    # Allocate blocks for a file.
    blocks = disk.allocate_blocks(
        3,
        "report.txt"
    )

    print("Allocated blocks:", blocks)

    # Create pending transaction.
    transaction_id = journal.begin_transaction(
        operation="CREATE",
        file_name="report.txt",
        blocks=blocks,
        details={
            "size": 2500
        }
    )

    print(
        f"Created transaction TX{transaction_id:03d}"
    )

    # Simulate crash.
    simulator = CrashSimulator(
        disk,
        journal
    )

    print("\nSimulating crash...")

    simulator.simulate_crash(
        transaction_id
    )

    print(
        "Corrupted blocks:",
        disk.get_corrupted_blocks()
    )

    # Start recovery.
    recovery = RecoveryManager(
        disk,
        journal
    )

    recovery.recover()

    # Display final state.
    recovery.display_recovery_log()

    print("\nFINAL DISK STATUS")
    disk.display_disk()

    print("\nFINAL JOURNAL")
    journal.display_journal()


if __name__ == "__main__":
    test_recovery_manager()