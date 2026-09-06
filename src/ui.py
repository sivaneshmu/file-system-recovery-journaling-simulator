import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from virtual_disk import VirtualDisk


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.disk = VirtualDisk(
            total_blocks=32,
            block_size=1024
        )

        self.setWindowTitle(
            "File System Recovery & Journaling Simulator"
        )

        self.resize(1000, 650)

        self.build_ui()
        self.refresh_disk()

    def build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        title = QLabel(
            "File System Recovery and Journaling Simulator"
        )

        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 22px; font-weight: bold; padding: 10px;"
        )

        main_layout.addWidget(title)

        content_layout = QHBoxLayout()

        # Left panel
        left_layout = QVBoxLayout()

        disk_label = QLabel("Virtual Disk")
        disk_label.setStyleSheet(
            "font-size: 16px; font-weight: bold;"
        )

        left_layout.addWidget(disk_label)

        self.disk_table = QTableWidget()
        self.disk_table.setColumnCount(3)

        self.disk_table.setHorizontalHeaderLabels(
            ["Block", "Status", "File"]
        )

        self.disk_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        left_layout.addWidget(self.disk_table)

        content_layout.addLayout(left_layout, 2)

        # Right panel
        right_layout = QVBoxLayout()

        status_label = QLabel("System Status")
        status_label.setStyleSheet(
            "font-size: 16px; font-weight: bold;"
        )

        right_layout.addWidget(status_label)

        self.status_value = QLabel("NORMAL")
        self.status_value.setAlignment(Qt.AlignCenter)

        self.status_value.setStyleSheet(
            "font-size: 18px; font-weight: bold; padding: 15px;"
        )

        right_layout.addWidget(self.status_value)

        self.allocate_button = QPushButton(
            "Allocate Test File"
        )

        self.allocate_button.clicked.connect(
            self.allocate_test_file
        )

        right_layout.addWidget(
            self.allocate_button
        )

        self.corrupt_button = QPushButton(
            "Corrupt Block"
        )

        self.corrupt_button.clicked.connect(
            self.corrupt_test_block
        )

        right_layout.addWidget(
            self.corrupt_button
        )

        self.recover_button = QPushButton(
            "Recover Block"
        )

        self.recover_button.clicked.connect(
            self.recover_test_block
        )

        right_layout.addWidget(
            self.recover_button
        )

        self.refresh_button = QPushButton(
            "Refresh Disk"
        )

        self.refresh_button.clicked.connect(
            self.refresh_disk
        )

        right_layout.addWidget(
            self.refresh_button
        )

        right_layout.addStretch()

        content_layout.addLayout(
            right_layout,
            1
        )

        main_layout.addLayout(content_layout)

        self.log_list = QListWidget()

        main_layout.addWidget(
            QLabel("Activity Log")
        )

        main_layout.addWidget(
            self.log_list
        )

    def allocate_test_file(self):
        try:
            blocks = self.disk.allocate_blocks(
                3,
                "demo.txt"
            )

            self.log(
                f"Allocated demo.txt → blocks {blocks}"
            )

            self.refresh_disk()

        except ValueError as error:
            self.log(str(error))

    def corrupt_test_block(self):
        used_blocks = self.disk.get_used_blocks()

        if not used_blocks:
            self.log(
                "No allocated blocks available."
            )
            return

        block_id = used_blocks[-1]

        self.disk.corrupt_block(
            block_id
        )

        self.status_value.setText(
            "CORRUPTION DETECTED"
        )

        self.log(
            f"Block {block_id} marked CORRUPTED"
        )

        self.refresh_disk()

    def recover_test_block(self):
        corrupted = self.disk.get_corrupted_blocks()

        if not corrupted:
            self.log(
                "No corrupted blocks available."
            )
            return

        block_id = corrupted[0]

        self.disk.recover_block(
            block_id,
            "demo.txt"
        )

        self.status_value.setText(
            "RECOVERED"
        )

        self.log(
            f"Block {block_id} recovered"
        )

        self.refresh_disk()

    def refresh_disk(self):
        blocks = self.disk.blocks

        self.disk_table.setRowCount(
            len(blocks)
        )

        for row, block in enumerate(blocks):
            self.disk_table.setItem(
                row,
                0,
                QTableWidgetItem(
                    str(block["block_id"])
                )
            )

            self.disk_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    block["status"]
                )
            )

            self.disk_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    str(block["file"])
                    if block["file"] is not None
                    else "-"
                )
            )

        self.disk_table.resizeColumnsToContents()

    def log(self, message):
        self.log_list.addItem(
            message
        )

        self.log_list.scrollToBottom()


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()