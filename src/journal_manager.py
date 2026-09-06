import json
import os
from datetime import datetime


class JournalManager:
    def __init__(self, journal_file="data/journal.log"):
        self.journal_file = journal_file
        self.transactions = []

        self._create_journal_directory()
        self.load_journal()

    def _create_journal_directory(self):
        directory = os.path.dirname(self.journal_file)

        if directory:
            os.makedirs(directory, exist_ok=True)

    def _next_transaction_id(self):
        if not self.transactions:
            return 1

        return max(
            transaction["transaction_id"]
            for transaction in self.transactions
        ) + 1

    def begin_transaction(self, operation, file_name, blocks=None, details=None):
        transaction = {
            "transaction_id": self._next_transaction_id(),
            "operation": operation,
            "file": file_name,
            "blocks": blocks or [],
            "details": details or {},
            "status": "PENDING",
            "timestamp": datetime.now().isoformat()
        }

        self.transactions.append(transaction)
        self.save_journal()

        return transaction["transaction_id"]

    def commit_transaction(self, transaction_id):
        transaction = self._find_transaction(transaction_id)

        if transaction["status"] != "PENDING":
            raise ValueError("Only pending transactions can be committed.")

        transaction["status"] = "COMMITTED"
        transaction["commit_time"] = datetime.now().isoformat()

        self.save_journal()

    def rollback_transaction(self, transaction_id):
        transaction = self._find_transaction(transaction_id)

        if transaction["status"] == "COMMITTED":
            raise ValueError("Committed transaction cannot be rolled back.")

        transaction["status"] = "ROLLED_BACK"
        transaction["rollback_time"] = datetime.now().isoformat()

        self.save_journal()

    def mark_incomplete(self, transaction_id):
        transaction = self._find_transaction(transaction_id)

        if transaction["status"] != "PENDING":
            raise ValueError("Only pending transactions can be incomplete.")

        transaction["status"] = "INCOMPLETE"

        self.save_journal()

    def get_transaction(self, transaction_id):
        return self._find_transaction(transaction_id).copy()

    def get_pending_transactions(self):
        return [
            transaction.copy()
            for transaction in self.transactions
            if transaction["status"] == "PENDING"
        ]

    def get_incomplete_transactions(self):
        return [
            transaction.copy()
            for transaction in self.transactions
            if transaction["status"] == "INCOMPLETE"
        ]

    def get_committed_transactions(self):
        return [
            transaction.copy()
            for transaction in self.transactions
            if transaction["status"] == "COMMITTED"
        ]

    def get_all_transactions(self):
        return [transaction.copy() for transaction in self.transactions]

    def save_journal(self):
        with open(self.journal_file, "w", encoding="utf-8") as file:
            json.dump(
                self.transactions,
                file,
                indent=4
            )

    def load_journal(self):
        if not os.path.exists(self.journal_file):
            self.transactions = []
            return

        try:
            with open(self.journal_file, "r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, list):
                self.transactions = data
            else:
                self.transactions = []

        except (json.JSONDecodeError, OSError):
            self.transactions = []

    def display_journal(self):
        print("\nJOURNAL")
        print("-" * 95)

        if not self.transactions:
            print("No journal entries.")
            return

        for transaction in self.transactions:
            print(
                f"TX{transaction['transaction_id']:03d} | "
                f"{transaction['operation']:<8} | "
                f"{transaction['file']:<20} | "
                f"{transaction['status']}"
            )

    def _find_transaction(self, transaction_id):
        for transaction in self.transactions:
            if transaction["transaction_id"] == transaction_id:
                return transaction

        raise ValueError("Transaction not found.")


def test_journal_manager():
    journal = JournalManager()

    print("Starting CREATE transaction...")

    tx1 = journal.begin_transaction(
        operation="CREATE",
        file_name="student.txt",
        blocks=[1, 2, 3],
        details={
            "size": 2500
        }
    )

    print(f"Transaction created: TX{tx1:03d}")

    journal.commit_transaction(tx1)

    print("Transaction committed.")

    print("\nStarting MODIFY transaction...")

    tx2 = journal.begin_transaction(
        operation="MODIFY",
        file_name="student.txt",
        blocks=[1, 2, 3],
        details={
            "old_size": 2500,
            "new_size": 3000
        }
    )

    print(f"Transaction created: TX{tx2:03d}")

    journal.mark_incomplete(tx2)

    print("Transaction marked incomplete.")

    print("\nStarting DELETE transaction...")

    tx3 = journal.begin_transaction(
        operation="DELETE",
        file_name="old.txt",
        blocks=[4, 5]
    )

    print(f"Transaction created: TX{tx3:03d}")

    journal.rollback_transaction(tx3)

    print("Transaction rolled back.")

    journal.display_journal()

    print("\nCommitted transactions:")
    print(journal.get_committed_transactions())

    print("\nIncomplete transactions:")
    print(journal.get_incomplete_transactions())


if __name__ == "__main__":
    test_journal_manager()