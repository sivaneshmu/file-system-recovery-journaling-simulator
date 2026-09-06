class VirtualDisk:
    FREE = "FREE"
    USED = "USED"
    RESERVED = "RESERVED"
    CORRUPTED = "CORRUPTED"
    RECOVERED = "RECOVERED"

    def __init__(self, total_blocks=32, block_size=1024):
        self.total_blocks = total_blocks
        self.block_size = block_size

        self.blocks = [
            {
                "block_id": i,
                "status": self.FREE,
                "file": None
            }
            for i in range(total_blocks)
        ]

        # Reserve block 0 for system information
        self.blocks[0]["status"] = self.RESERVED

    def allocate_blocks(self, count, file_name):
        free_blocks = [
            block for block in self.blocks
            if block["status"] == self.FREE
        ]

        if len(free_blocks) < count:
            raise ValueError("Not enough free blocks.")

        allocated = []

        for block in free_blocks[:count]:
            block["status"] = self.USED
            block["file"] = file_name
            allocated.append(block["block_id"])

        return allocated

    def release_blocks(self, block_ids):
        for block_id in block_ids:
            self._validate_block_id(block_id)

            block = self.blocks[block_id]

            if block["status"] != self.RESERVED:
                block["status"] = self.FREE
                block["file"] = None

    def corrupt_block(self, block_id):
        self._validate_block_id(block_id)

        block = self.blocks[block_id]

        if block["status"] != self.RESERVED:
            block["status"] = self.CORRUPTED

    def recover_block(self, block_id, file_name=None):
        self._validate_block_id(block_id)

        block = self.blocks[block_id]

        if block["status"] == self.CORRUPTED:
            block["status"] = self.RECOVERED
            block["file"] = file_name

    def get_free_blocks(self):
        return [
            block["block_id"]
            for block in self.blocks
            if block["status"] == self.FREE
        ]

    def get_used_blocks(self):
        return [
            block["block_id"]
            for block in self.blocks
            if block["status"] == self.USED
        ]

    def get_corrupted_blocks(self):
        return [
            block["block_id"]
            for block in self.blocks
            if block["status"] == self.CORRUPTED
        ]

    def display_disk(self):
        print("\nVIRTUAL DISK STATUS")
        print("-" * 60)

        for block in self.blocks:
            print(
                f"Block {block['block_id']:02d} | "
                f"{block['status']:<9} | "
                f"File: {block['file']}"
            )

    def _validate_block_id(self, block_id):
        if block_id < 0 or block_id >= self.total_blocks:
            raise ValueError("Invalid block ID.")


def test_virtual_disk():
    disk = VirtualDisk(total_blocks=16, block_size=1024)

    print("Creating Virtual Disk...")
    print(f"Total blocks : {disk.total_blocks}")
    print(f"Block size   : {disk.block_size} bytes")

    blocks = disk.allocate_blocks(3, "student.txt")

    print("\nAllocated blocks:", blocks)

    disk.corrupt_block(blocks[1])

    print("Corrupted block:", blocks[1])

    print("Free blocks:", disk.get_free_blocks())
    print("Corrupted blocks:", disk.get_corrupted_blocks())

    disk.recover_block(blocks[1], "student.txt")

    print("Recovered block:", blocks[1])

    disk.display_disk()


if __name__ == "__main__":
    test_virtual_disk()