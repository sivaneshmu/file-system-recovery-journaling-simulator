import time
import matplotlib.pyplot as plt


class PerformanceAnalyzer:
    def __init__(self):
        self.metrics = {}

    def start_timer(self):
        return time.perf_counter()

    def end_timer(self, start_time):
        return time.perf_counter() - start_time

    def record_operation_time(self, operation, elapsed_time):
        self.metrics[operation] = elapsed_time

    def calculate_disk_utilization(self, virtual_disk):
        used = sum(
            1 for block in virtual_disk.blocks
            if block["status"] in (
                virtual_disk.USED,
                virtual_disk.RECOVERED
            )
        )

        total = virtual_disk.total_blocks

        if total == 0:
            return 0.0

        return (used / total) * 100

    def count_corrupted_blocks(self, virtual_disk):
        return len(virtual_disk.get_corrupted_blocks())

    def count_recovered_blocks(self, virtual_disk):
        return sum(
            1 for block in virtual_disk.blocks
            if block["status"] == virtual_disk.RECOVERED
        )

    def count_transactions(self, journal_manager):
        return len(journal_manager.get_all_transactions())

    def calculate_recovery_success_rate(self, journal_manager):
        transactions = journal_manager.get_all_transactions()

        if not transactions:
            return 0.0

        recovered = sum(
            1 for transaction in transactions
            if transaction["status"] == "RECOVERED"
        )

        return (recovered / len(transactions)) * 100

    def generate_report(self, virtual_disk, journal_manager):
        report = {
            "operation_times": self.metrics.copy(),
            "disk_utilization": self.calculate_disk_utilization(
                virtual_disk
            ),
            "corrupted_blocks": self.count_corrupted_blocks(
                virtual_disk
            ),
            "recovered_blocks": self.count_recovered_blocks(
                virtual_disk
            ),
            "transactions": self.count_transactions(
                journal_manager
            ),
            "recovery_success_rate": self.calculate_recovery_success_rate(
                journal_manager
            )
        }

        return report

    def display_report(self, report):
        print("\nPERFORMANCE ANALYSIS")
        print("-" * 60)

        print("\nOperation Times:")

        for operation, elapsed in report["operation_times"].items():
            print(
                f"{operation:<25}: "
                f"{elapsed:.6f} seconds"
            )

        print(
            f"\nDisk Utilization         : "
            f"{report['disk_utilization']:.2f}%"
        )

        print(
            f"Corrupted Blocks         : "
            f"{report['corrupted_blocks']}"
        )

        print(
            f"Recovered Blocks         : "
            f"{report['recovered_blocks']}"
        )

        print(
            f"Transactions             : "
            f"{report['transactions']}"
        )

        print(
            f"Recovery Success Rate    : "
            f"{report['recovery_success_rate']:.2f}%"
        )

    def plot_operation_times(self):
        if not self.metrics:
            print("No operation timing data available.")
            return

        operations = list(self.metrics.keys())
        times = list(self.metrics.values())

        plt.figure(figsize=(9, 5))
        plt.bar(operations, times)
        plt.xlabel("Operation")
        plt.ylabel("Time (seconds)")
        plt.title("File System Operation Time")
        plt.xticks(rotation=30)
        plt.tight_layout()
        plt.show()


def test_performance_analyzer():
    from virtual_disk import VirtualDisk
    from journal_manager import JournalManager

    print("Creating test environment...")

    disk = VirtualDisk(
        total_blocks=16,
        block_size=1024
    )

    journal = JournalManager(
        "data/test_performance_journal.log"
    )

    analyzer = PerformanceAnalyzer()

    # Measure file-system block allocation
    start = analyzer.start_timer()

    blocks = disk.allocate_blocks(
        3,
        "report.txt"
    )

    elapsed = analyzer.end_timer(start)

    analyzer.record_operation_time(
        "Block Allocation",
        elapsed
    )

    # Measure journal transaction creation
    start = analyzer.start_timer()

    transaction_id = journal.begin_transaction(
        operation="CREATE",
        file_name="report.txt",
        blocks=blocks,
        details={
            "size": 2500
        }
    )

    elapsed = analyzer.end_timer(start)

    analyzer.record_operation_time(
        "Journal Write",
        elapsed
    )

    journal.commit_transaction(transaction_id)

    # Simulate corruption
    disk.corrupt_block(blocks[2])

    # Recover the block manually for measurement
    start = analyzer.start_timer()

    disk.recover_block(
        blocks[2],
        "report.txt"
    )

    elapsed = analyzer.end_timer(start)

    analyzer.record_operation_time(
        "Block Recovery",
        elapsed
    )

    report = analyzer.generate_report(
        disk,
        journal
    )

    analyzer.display_report(report)

    # Uncomment to display graph
    # analyzer.plot_operation_times()


if __name__ == "__main__":
    test_performance_analyzer()