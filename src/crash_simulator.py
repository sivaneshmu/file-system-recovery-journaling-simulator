class CrashSimulator:
    def __init__(self, virtual_disk, journal_manager):
        self.disk = virtual_disk
        self.journal = journal_manager
        self.crashed = False

    def simulate_crash(self, transaction_id):
        transaction = self.journal.get_transaction(transaction_id)

        if transaction["status"] != "PENDING":
            raise ValueError(
                "Only pending transactions can be crashed."
            )

        self.crashed = True

        # Mark some allocated blocks as corrupted
        blocks = transaction["blocks"]

        if blocks:
            crash_block = blocks[-1]
            self.disk.corrupt_block(crash_block)

        # Mark transaction as incomplete
        self.journal.mark_incomplete(transaction_id)

        return {
            "transaction_id": transaction_id,
            "status": "CRASHED",
            "corrupted_blocks": blocks[-1:] if blocks else []
        }

    def reset(self):
        self.crashed = False

    def is_crashed(self):
        return self.crashed

    def display_crash_status(self):
        if self.crashed:
            print("\nSYSTEM STATUS: CRASHED")
        else:
            print("\nSYSTEM STATUS: NORMAL")


def test_crash_simulator():
    from virtual_disk import VirtualDisk
    from journal_manager import JournalManager

    print("Creating virtual disk...")
    disk = VirtualDisk(total_blocks=16, block_size=1024)

    print("Creating journal manager...")
    journal = JournalManager("data/test_crash_journal.log")

    print("\nAllocating blocks for report.txt...")

    blocks = disk.allocate_blocks(3, "report.txt")

    print("Allocated blocks:", blocks)

    print("\nStarting transaction...")

    transaction_id = journal.begin_transaction(
        operation="CREATE",
        file_name="report.txt",
        blocks=blocks,
        details={
            "size": 2500
        }
    )

    print(f"Transaction created: TX{transaction_id:03d}")

    simulator = CrashSimulator(disk, journal)

    print("\nSimulating crash...")

    result = simulator.simulate_crash(transaction_id)

    print("Crash result:")
    print(result)

    simulator.display_crash_status()

    print("\nCorrupted blocks:")
    print(disk.get_corrupted_blocks())

    print("\nJournal:")
    journal.display_journal()

    print("\nTransaction status:")
    print(
        journal.get_transaction(transaction_id)
    )


if __name__ == "__main__":
    test_crash_simulator()