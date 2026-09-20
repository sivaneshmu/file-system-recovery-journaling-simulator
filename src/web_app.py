import sys
import json

from pathlib import Path
from datetime import datetime

from flask import (
    Flask,
    jsonify,
    render_template,
    request
)


# =========================================================
# PROJECT PATH
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from main import FileSystemSystem


# =========================================================
# FLASK APP
# =========================================================

app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / "templates"),
    static_folder=str(PROJECT_ROOT / "static")
)


# One simulator instance for the running application
system = FileSystemSystem()


# =========================================================
# PERSISTENT ACTIVITY LOG
# =========================================================

ACTIVITY_LOG_PATH = (
    PROJECT_ROOT /
    "data" /
    "activity_log.json"
)

ACTIVITY_LOG_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)


def _load_activity_log():
    if not ACTIVITY_LOG_PATH.exists():
        return []

    try:
        with ACTIVITY_LOG_PATH.open(
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, list):
            return [
                item
                for item in data
                if isinstance(item, dict)
                and "time" in item
                and "message" in item
            ]

    except (
        OSError,
        ValueError,
        TypeError
    ):
        pass

    return []


activity_log = _load_activity_log()


def _save_activity_log():
    temporary_path = (
        ACTIVITY_LOG_PATH.with_suffix(".tmp")
    )

    try:
        with temporary_path.open(
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                activity_log,
                file,
                indent=2,
                ensure_ascii=False
            )

        temporary_path.replace(
            ACTIVITY_LOG_PATH
        )

    except OSError:
        pass


def add_activity(message):
    activity_log.insert(
        0,
        {
            "time":
                datetime.now().strftime(
                    "%H:%M:%S"
                ),
            "message":
                str(message)
        }
    )

    del activity_log[200:]

    _save_activity_log()


# =========================================================
# STATUS HELPERS
# =========================================================

def _normalise_status(value):

    if value is None:
        return "FREE"

    text = (
        str(value)
        .strip()
        .upper()
    )

    if "." in text:
        text = text.rsplit(
            ".",
            1
        )[-1]

    return text


def _transactions_from_object(value):

    if isinstance(value, list):
        return [
            item
            for item in value
            if isinstance(item, dict)
        ]

    if isinstance(value, dict):

        for key in (
            "transactions",
            "journal",
            "entries",
            "records"
        ):

            nested = value.get(key)

            if isinstance(nested, list):
                return [
                    item
                    for item in nested
                    if isinstance(item, dict)
                ]

    return []


# =========================================================
# JOURNAL
# =========================================================

def get_transactions():

    journal_manager = (
        system.journal_manager
    )

    # In-memory containers
    for attribute in (
        "transactions",
        "journal",
        "entries",
        "records"
    ):

        transactions = (
            _transactions_from_object(
                getattr(
                    journal_manager,
                    attribute,
                    None
                )
            )
        )

        if transactions:
            return transactions


    # Public getter methods
    for method_name in (
        "get_transactions",
        "get_all_transactions",
        "read_journal",
        "load_journal"
    ):

        method = getattr(
            journal_manager,
            method_name,
            None
        )

        if callable(method):

            try:
                transactions = (
                    _transactions_from_object(
                        method()
                    )
                )

                if transactions:
                    return transactions

            except Exception:
                pass


    # Persistent journal fallback
    possible_paths = []

    for attribute in (
        "journal_file",
        "journal_path",
        "file_path",
        "path"
    ):

        value = getattr(
            journal_manager,
            attribute,
            None
        )

        if value:
            possible_paths.append(
                Path(value)
            )


    possible_paths.append(
        PROJECT_ROOT /
        "data" /
        "integration_journal.log"
    )


    checked = set()

    for journal_path in possible_paths:

        try:

            journal_path = Path(
                journal_path
            )

            if (
                journal_path in checked
                or not journal_path.exists()
            ):
                continue

            checked.add(journal_path)

            with journal_path.open(
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)


            transactions = (
                _transactions_from_object(
                    data
                )
            )

            if transactions:
                return transactions

        except (
            OSError,
            ValueError,
            TypeError
        ):
            continue


    return []


# =========================================================
# FILES
# =========================================================

def get_file_data():

    files = getattr(
        system.file_manager,
        "files",
        {}
    )

    if isinstance(files, dict):
        return files

    return {}


def get_directories():

    directories = getattr(
        system.directory_manager,
        "directories",
        {}
    )

    if isinstance(directories, dict):
        return directories

    return {}


# =========================================================
# DISK
# =========================================================

def get_disk_state():

    blocks = getattr(
        system.disk,
        "blocks",
        []
    )

    result = []

    used = 0
    corrupted = 0
    recovered = 0
    reserved = 0


    for index, block in enumerate(blocks):

        if not isinstance(block, dict):

            block = {
                "status": block
            }


        status = _normalise_status(
            block.get(
                "status",
                "FREE"
            )
        )


        file_name = block.get(
            "file",
            block.get(
                "file_name",
                ""
            )
        )


        if status == "USED":
            used += 1

        elif status == "CORRUPTED":
            corrupted += 1

        elif status == "RECOVERED":
            recovered += 1

        elif status == "RESERVED":
            reserved += 1


        result.append(
            {
                "id": index,
                "status": status,
                "file": file_name or ""
            }
        )


    total = len(result)


    utilization = (
        (used / total) * 100
        if total
        else 0
    )


    return {
        "total": total,
        "used": used,
        "free": max(
            total -
            used -
            corrupted -
            recovered -
            reserved,
            0
        ),
        "corrupted": corrupted,
        "recovered": recovered,
        "reserved": reserved,
        "utilization":
            round(
                utilization,
                2
            ),
        "blocks": result
    }


# =========================================================
# RECOVERY STATUS
# =========================================================

def get_recovery_success_rate():

    transactions = (
        get_transactions()
    )


    recovery_transactions = [
        tx
        for tx in transactions
        if tx.get(
            "recovery_required"
        ) is True
    ]


    if not recovery_transactions:
        return 0.0


    successful = sum(
        1
        for tx in recovery_transactions
        if _normalise_status(
            tx.get(
                "status",
                ""
            )
        ) == "RECOVERED"
    )


    return round(
        (
            successful /
            len(recovery_transactions)
        ) * 100,
        2
    )


def get_crash_status():

    disk = get_disk_state()

    if disk["corrupted"] > 0:
        return "CRASHED"


    for transaction in get_transactions():

        status = _normalise_status(
            transaction.get(
                "status",
                ""
            )
        )

        if status in (
            "PENDING",
            "INCOMPLETE"
        ):
            return "CRASHED"


    return "NORMAL"


# =========================================================
# CONSISTENCY
# =========================================================

def get_consistency_summary():

    try:

        result = (
            system.check_consistency()
        )


        if isinstance(
            result,
            dict
        ):
            return result


        return {
            "status":
                str(result)
        }


    except Exception as exc:

        return {
            "status":
                "ERROR",
            "healthy":
                False,
            "errors": [
                str(exc)
            ]
        }


# =========================================================
# PERFORMANCE
# =========================================================

def get_performance_report():

    try:

        return (
            system
            .performance_analyzer
            .generate_report(
                system.disk,
                system.journal_manager
            )
        )

    except Exception as exc:

        return {
            "error":
                str(exc)
        }


# =========================================================
# COMPLETE STATE
# =========================================================

def get_state():

    disk = get_disk_state()

    files = get_file_data()

    directories = (
        get_directories()
    )

    transactions = (
        get_transactions()
    )

    performance = (
        get_performance_report()
    )

    consistency = (
        get_consistency_summary()
    )


    return {
        "disk": disk,

        "files": files,

        "file_count":
            len(files),

        "directories":
            directories,

        "transactions":
            transactions,

        "transaction_count":
            len(transactions),

        "crash_status":
            get_crash_status(),

        "recovery_success":
            get_recovery_success_rate(),

        "consistency":
            consistency,

        "performance":
            performance,

        "activity_log":
            activity_log
    }


# =========================================================
# HOME
# =========================================================

@app.get("/")
def index():

    return render_template(
        "index.html"
    )


# =========================================================
# STATE
# =========================================================

@app.get("/api/state")
def state():

    return jsonify(
        {
            "success": True,
            "state": get_state()
        }
    )


# =========================================================
# CREATE FILE
# =========================================================

@app.post("/api/create-file")
def create_file():

    data = (
        request.get_json(
            silent=True
        ) or {}
    )


    file_name = str(
        data.get(
            "file_name",
            ""
        )
    ).strip()


    try:
        size = int(
            data.get(
                "size",
                0
            )
        )

    except (
        ValueError,
        TypeError
    ):
        size = 0


    content = str(
        data.get(
            "content",
            ""
        )
    )


    directory = str(
        data.get(
            "directory",
            "/"
        )
    ).strip() or "/"


    if not file_name:
        return jsonify(
            {
                "success": False,
                "message":
                    "Enter a file name."
            }
        ), 400


    if size <= 0:
        return jsonify(
            {
                "success": False,
                "message":
                    "File size must be greater than 0."
            }
        ), 400


    try:

        transaction_id = (
            system.create_file(
                file_name=file_name,
                size=size,
                content=content,
                directory=directory
            )
        )


        add_activity(
            f"{file_name} created successfully."
        )


        return jsonify(
            {
                "success": True,
                "message":
                    f"{file_name} created successfully.",
                "transaction_id":
                    transaction_id,
                "state":
                    get_state()
            }
        )


    except Exception as exc:

        return jsonify(
            {
                "success": False,
                "message":
                    str(exc)
            }
        ), 400


# =========================================================
# MODIFY FILE
# =========================================================

@app.post("/api/modify-file")
def modify_file():

    data = (
        request.get_json(
            silent=True
        ) or {}
    )


    file_name = str(
        data.get(
            "file_name",
            ""
        )
    ).strip()


    content = str(
        data.get(
            "content",
            ""
        )
    )


    if not file_name:
        return jsonify(
            {
                "success": False,
                "message":
                    "Enter a file name."
            }
        ), 400


    try:

        transaction_id = (
            system.modify_file(
                file_name,
                content
            )
        )


        add_activity(
            f"{file_name} modified successfully."
        )


        return jsonify(
            {
                "success": True,
                "message":
                    f"{file_name} modified successfully.",
                "transaction_id":
                    transaction_id,
                "state":
                    get_state()
            }
        )


    except Exception as exc:

        return jsonify(
            {
                "success": False,
                "message":
                    str(exc)
            }
        ), 400


# =========================================================
# DELETE FILE
# =========================================================

@app.post("/api/delete-file")
def delete_file():

    data = (
        request.get_json(
            silent=True
        ) or {}
    )


    file_name = str(
        data.get(
            "file_name",
            ""
        )
    ).strip()


    if not file_name:
        return jsonify(
            {
                "success": False,
                "message":
                    "Enter a file name."
            }
        ), 400


    try:

        transaction_id = (
            system.delete_file(
                file_name
            )
        )


        add_activity(
            f"{file_name} deleted successfully."
        )


        return jsonify(
            {
                "success": True,
                "message":
                    f"{file_name} deleted successfully.",
                "transaction_id":
                    transaction_id,
                "state":
                    get_state()
            }
        )


    except Exception as exc:

        return jsonify(
            {
                "success": False,
                "message":
                    str(exc)
            }
        ), 400


# =========================================================
# CREATE DIRECTORY
# =========================================================

@app.post("/api/create-directory")
def create_directory():

    data = (
        request.get_json(
            silent=True
        ) or {}
    )


    path = str(
        data.get(
            "path",
            ""
        )
    ).strip()


    if not path:
        return jsonify(
            {
                "success": False,
                "message":
                    "Enter a directory path."
            }
        ), 400


    try:

        system.create_directory(
            path
        )


        add_activity(
            f"Directory {path} created successfully."
        )


        return jsonify(
            {
                "success": True,
                "message":
                    f"Directory {path} created successfully.",
                "state":
                    get_state()
            }
        )


    except Exception as exc:

        return jsonify(
            {
                "success": False,
                "message":
                    str(exc)
            }
        ), 400


# =========================================================
# DELETE DIRECTORY
# =========================================================

@app.post("/api/delete-directory")
def delete_directory():

    data = (
        request.get_json(
            silent=True
        ) or {}
    )


    path = str(
        data.get(
            "path",
            ""
        )
    ).strip()


    if not path:
        return jsonify(
            {
                "success": False,
                "message":
                    "Enter a directory path."
            }
        ), 400


    try:

        system.directory_manager.delete_directory(
            path
        )


        add_activity(
            f"Directory {path} deleted successfully."
        )


        return jsonify(
            {
                "success": True,
                "message":
                    f"Directory {path} deleted successfully.",
                "state":
                    get_state()
            }
        )


    except Exception as exc:

        return jsonify(
            {
                "success": False,
                "message":
                    str(exc)
            }
        ), 400


# =========================================================
# CRASH
# =========================================================

@app.post("/api/crash")
def simulate_crash():

    try:

        if (
            get_crash_status()
            == "CRASHED"
        ):

            return jsonify(
                {
                    "success": False,
                    "message":
                        "The file system is already crashed. "
                        "Recover it before starting another crash simulation."
                }
            ), 400


        crash_blocks = (
            system.disk
            .get_free_blocks()[:3]
        )


        if len(crash_blocks) < 3:

            return jsonify(
                {
                    "success": False,
                    "message":
                        "Not enough free blocks "
                        "for crash simulation."
                }
            ), 400


        result = (
            system.simulate_crash(
                "crash_demo.txt",
                crash_blocks
            )
        )


        add_activity(
            "Crash simulated. "
            "File system is now in a failed state."
        )


        return jsonify(
            {
                "success": True,
                "message":
                    "Crash simulation completed.",
                "result":
                    result,
                "blocks":
                    crash_blocks,
                "state":
                    get_state()
            }
        )


    except Exception as exc:

        return jsonify(
            {
                "success": False,
                "message":
                    str(exc)
            }
        ), 400


# =========================================================
# RECOVERY
# =========================================================

@app.post("/api/recover")
def recover():

    try:

        result = (
            system.recover()
        )


        add_activity(
            "File system recovery completed."
        )


        return jsonify(
            {
                "success": True,
                "message":
                    "File system recovery completed.",
                "result":
                    result,
                "state":
                    get_state()
            }
        )


    except Exception as exc:

        return jsonify(
            {
                "success": False,
                "message":
                    str(exc)
            }
        ), 400


# =========================================================
# CONSISTENCY
# =========================================================

@app.post("/api/consistency")
def consistency():

    try:

        result = (
            get_consistency_summary()
        )


        if (
            isinstance(result, dict)
            and
            result.get("healthy")
            is True
        ):

            add_activity(
                "Consistency check passed. "
                "File system is healthy."
            )

        else:

            add_activity(
                "Consistency check detected problems."
            )


        return jsonify(
            {
                "success": True,
                "result":
                    result,
                "state":
                    get_state()
            }
        )


    except Exception as exc:

        return jsonify(
            {
                "success": False,
                "message":
                    str(exc)
            }
        ), 500


# =========================================================
# PERFORMANCE
# =========================================================

@app.get("/api/performance")
def performance():

    try:

        report = (
            get_performance_report()
        )


        return jsonify(
            {
                "success": True,
                "report":
                    report
            }
        )


    except Exception as exc:

        return jsonify(
            {
                "success": False,
                "message":
                    str(exc)
            }
        ), 500


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )