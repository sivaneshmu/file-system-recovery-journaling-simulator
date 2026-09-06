import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request


# ---------------------------------------------------------
# PROJECT PATH
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from main import FileSystemSystem


# ---------------------------------------------------------
# FLASK APP
# ---------------------------------------------------------

app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / "templates"),
    static_folder=str(PROJECT_ROOT / "static"),
)


# One simulator instance for the running web application.
system = FileSystemSystem()


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def get_transactions():
    """
    Return journal transactions in a safe list form.
    """
    journal = getattr(system.journal_manager, "journal", None)

    if isinstance(journal, list):
        return journal

    return []


def get_file_data():
    """
    Return file manager data in a safe dictionary form.
    """
    files = getattr(system.file_manager, "files", {})

    if isinstance(files, dict):
        return files

    return {}


def get_directories():
    """
    Return directory manager data in a safe dictionary form.
    """
    directories = getattr(
        system.directory_manager,
        "directories",
        {}
    )

    if isinstance(directories, dict):
        return directories

    return {}


def get_disk_state():
    """
    Convert the virtual disk into JSON-friendly information.
    """

    blocks = getattr(system.disk, "blocks", [])

    result = []

    used = 0
    corrupted = 0
    recovered = 0
    reserved = 0

    for index, block in enumerate(blocks):

        if not isinstance(block, dict):
            block = {
                "status": str(block)
            }

        status = str(
            block.get("status", "FREE")
        ).upper()

        file_name = block.get(
            "file",
            block.get("file_name", "")
        )

        if status == getattr(system.disk, "USED", "USED"):
            used += 1

        elif status == getattr(
            system.disk,
            "CORRUPTED",
            "CORRUPTED"
        ):
            corrupted += 1

        elif status == getattr(
            system.disk,
            "RECOVERED",
            "RECOVERED"
        ):
            recovered += 1

        elif status == getattr(
            system.disk,
            "RESERVED",
            "RESERVED"
        ):
            reserved += 1

        result.append({
            "id": index,
            "status": status,
            "file": file_name,
        })

    total = len(result)

    utilization = (
        (used / total) * 100
        if total
        else 0
    )

    return {
        "total": total,
        "used": used,
        "free": total - used - corrupted - recovered - reserved,
        "corrupted": corrupted,
        "recovered": recovered,
        "reserved": reserved,
        "utilization": round(utilization, 2),
        "blocks": result,
    }


def get_recovery_success_rate():
    """
    Calculate recovery success using transactions that
    actually required recovery.
    """

    transactions = get_transactions()

    recovery_transactions = [
        tx
        for tx in transactions
        if tx.get("recovery_required") is True
    ]

    if not recovery_transactions:
        return 100.0

    successful = sum(
        1
        for tx in recovery_transactions
        if str(
            tx.get("status", "")
        ).upper() == "RECOVERED"
    )

    return round(
        (successful / len(recovery_transactions)) * 100,
        2
    )


def get_crash_status():
    """
    Determine the overall filesystem status from
    the actual simulator state.
    """

    # If the disk contains corrupted blocks,
    # the system is not in a normal state.
    disk = get_disk_state()

    if disk["corrupted"] > 0:
        return "CRASHED"

    # Check the journal for unfinished transactions.
    transactions = get_transactions()

    for transaction in transactions:

        status = str(
            transaction.get("status", "")
        ).upper()

        if status in ("PENDING", "INCOMPLETE"):
            return "CRASHED"

    # Otherwise the filesystem is operating normally.
    return "NORMAL"


def get_consistency_summary():
    """
    Run consistency checking and convert the result
    to JSON-friendly data.
    """

    try:
        result = system.check_consistency()

        if isinstance(result, dict):
            return result

        return {
            "status": str(result)
        }

    except Exception as exc:
        return {
            "status": "ERROR",
            "message": str(exc)
        }


def get_state():
    """
    Return complete dashboard state.
    """

    disk = get_disk_state()
    files = get_file_data()
    directories = get_directories()
    transactions = get_transactions()

    return {
        "disk": disk,
        "files": files,
        "file_count": len(files),
        "directories": directories,
        "transactions": transactions,
        "transaction_count": len(transactions),
        "crash_status": get_crash_status(),
        "recovery_success": get_recovery_success_rate(),
    }


# ---------------------------------------------------------
# PAGE
# ---------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------
# STATE API
# ---------------------------------------------------------

@app.get("/api/state")
def api_state():

    try:
        return jsonify({
            "success": True,
            "state": get_state(),
        })

    except Exception as exc:

        return jsonify({
            "success": False,
            "message": str(exc),
        }), 500


# ---------------------------------------------------------
# CREATE FILE
# ---------------------------------------------------------

@app.post("/api/create-file")
def create_file():

    data = request.get_json(silent=True) or {}

    file_name = str(
        data.get("file_name", "")
    ).strip()

    size = int(
        data.get("size", 0)
    )

    content = str(
        data.get("content", "")
    )

    directory = str(
        data.get("directory", "/")
    ).strip() or "/"

    if not file_name:
        return jsonify({
            "success": False,
            "message": "Enter a file name.",
        }), 400

    if size <= 0:
        return jsonify({
            "success": False,
            "message": "File size must be greater than 0.",
        }), 400

    try:

        transaction_id = system.create_file(
            file_name=file_name,
            size=size,
            content=content,
            directory=directory,
        )

        return jsonify({
            "success": True,
            "message": (
                f"{file_name} created successfully."
            ),
            "transaction_id": transaction_id,
            "state": get_state(),
        })

    except Exception as exc:

        return jsonify({
            "success": False,
            "message": str(exc),
        }), 400


# ---------------------------------------------------------
# MODIFY FILE
# ---------------------------------------------------------

@app.post("/api/modify-file")
def modify_file():

    data = request.get_json(silent=True) or {}

    file_name = str(
        data.get("file_name", "")
    ).strip()

    content = str(
        data.get("content", "")
    )

    if not file_name:
        return jsonify({
            "success": False,
            "message": "Enter a file name.",
        }), 400

    try:

        transaction_id = system.modify_file(
            file_name,
            content
        )

        return jsonify({
            "success": True,
            "message": (
                f"{file_name} modified successfully."
            ),
            "transaction_id": transaction_id,
            "state": get_state(),
        })

    except Exception as exc:

        return jsonify({
            "success": False,
            "message": str(exc),
        }), 400


# ---------------------------------------------------------
# DELETE FILE
# ---------------------------------------------------------

@app.post("/api/delete-file")
def delete_file():

    data = request.get_json(silent=True) or {}

    file_name = str(
        data.get("file_name", "")
    ).strip()

    if not file_name:
        return jsonify({
            "success": False,
            "message": "Enter a file name.",
        }), 400

    try:

        transaction_id = system.delete_file(
            file_name
        )

        return jsonify({
            "success": True,
            "message": (
                f"{file_name} deleted successfully."
            ),
            "transaction_id": transaction_id,
            "state": get_state(),
        })

    except Exception as exc:

        return jsonify({
            "success": False,
            "message": str(exc),
        }), 400


# ---------------------------------------------------------
# CREATE DIRECTORY
# ---------------------------------------------------------

@app.post("/api/create-directory")
def create_directory():

    data = request.get_json(silent=True) or {}

    path = str(
        data.get("path", "")
    ).strip()

    if not path:
        return jsonify({
            "success": False,
            "message": "Enter a directory path.",
        }), 400

    try:

        system.create_directory(path)

        return jsonify({
            "success": True,
            "message": (
                f"Directory {path} created successfully."
            ),
            "state": get_state(),
        })

    except Exception as exc:

        return jsonify({
            "success": False,
            "message": str(exc),
        }), 400


# ---------------------------------------------------------
# DELETE DIRECTORY
# ---------------------------------------------------------

@app.post("/api/delete-directory")
def delete_directory():

    data = request.get_json(silent=True) or {}

    path = str(
        data.get("path", "")
    ).strip()

    if not path:
        return jsonify({
            "success": False,
            "message": "Enter a directory path.",
        }), 400

    try:

        system.directory_manager.delete_directory(
            path
        )

        return jsonify({
            "success": True,
            "message": (
                f"Directory {path} deleted successfully."
            ),
            "state": get_state(),
        })

    except Exception as exc:

        return jsonify({
            "success": False,
            "message": str(exc),
        }), 400


# ---------------------------------------------------------
# SIMULATE CRASH
# ---------------------------------------------------------

@app.post("/api/crash")
def simulate_crash():

    try:

        crash_blocks = (
            system.disk.get_free_blocks()[:3]
        )

        if len(crash_blocks) < 3:

            return jsonify({
                "success": False,
                "message": (
                    "Not enough free blocks "
                    "for crash simulation."
                ),
            }), 400

        result = system.simulate_crash(
            "crash_demo.txt",
            crash_blocks
        )

        return jsonify({
            "success": True,
            "message": "Crash simulation completed.",
            "result": result,
            "blocks": crash_blocks,
            "state": get_state(),
        })

    except Exception as exc:

        return jsonify({
            "success": False,
            "message": str(exc),
        }), 400


# ---------------------------------------------------------
# RECOVER FILE SYSTEM
# ---------------------------------------------------------

@app.post("/api/recover")
def recover():

    try:

        result = system.recover()

        return jsonify({
            "success": True,
            "message": (
                "File system recovery completed."
            ),
            "result": result,
            "state": get_state(),
        })

    except Exception as exc:

        return jsonify({
            "success": False,
            "message": str(exc),
        }), 400


# ---------------------------------------------------------
# CONSISTENCY CHECK
# ---------------------------------------------------------

@app.post("/api/consistency")
def consistency():

    try:

        result = get_consistency_summary()

        return jsonify({
            "success": True,
            "result": result,
            "state": get_state(),
        })

    except Exception as exc:

        return jsonify({
            "success": False,
            "message": str(exc),
        }), 500


# ---------------------------------------------------------
# PERFORMANCE
# ---------------------------------------------------------

@app.get("/api/performance")
def performance():

    try:

        report = system.performance_analyzer.generate_report(
            system.disk,
            system.journal_manager,
        )

        return jsonify({
            "success": True,
            "report": report,
        })

    except Exception as exc:

        return jsonify({
            "success": False,
            "message": str(exc),
        }), 500


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )