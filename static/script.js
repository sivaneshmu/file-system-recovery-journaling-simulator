let activityEntries = [];


function now() {

    const date = new Date();

    return date.toLocaleTimeString(
        [],
        {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
        }
    );
}


function addActivity(message) {

    activityEntries.unshift({
        time: now(),
        message: message
    });

    activityEntries =
        activityEntries.slice(0, 10);

    const log =
        document.getElementById("activityLog");

    log.innerHTML = "";

    activityEntries.forEach(entry => {

        const row =
            document.createElement("div");

        row.className = "log-entry";

        row.innerHTML = `
            <span class="log-time">
                ${entry.time}
            </span>

            <span>
                ${escapeHtml(entry.message)}
            </span>
        `;

        log.appendChild(row);
    });
}


function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


async function api(url, options = {}) {

    const response = await fetch(
        url,
        {
            headers: {
                "Content-Type":
                    "application/json"
            },
            ...options
        }
    );

    const data =
        await response.json();

    if (!response.ok ||
        data.success === false) {

        throw new Error(
            data.message ||
            "Operation failed."
        );
    }

    return data;
}


function showMessage(message) {

    alert(message);
}


function setSystemStatus(status) {

    const statusBox =
        document.getElementById(
            "systemStatus"
        );

    const statusText =
        document.getElementById(
            "systemStatusText"
        );

    const normalized =
        String(status || "NORMAL")
            .toUpperCase();

    statusText.textContent =
        normalized;

    statusBox.classList.remove(
        "normal",
        "crashed",
        "recovering"
    );

    if (normalized.includes("CRASH")) {

        statusBox.classList.add(
            "crashed"
        );

    } else if (
        normalized.includes("RECOVER")
    ) {

        statusBox.classList.add(
            "recovering"
        );

    } else {

        statusBox.classList.add(
            "normal"
        );
    }
}


function updateMetrics(state) {

    const disk = state.disk;

    document.getElementById(
        "diskUtilization"
    ).textContent =
        `${disk.utilization}%`;

    document.getElementById(
        "diskUsageText"
    ).textContent =
        `${disk.used} / ${disk.total} blocks used`;

    document.getElementById(
        "fileCount"
    ).textContent =
        state.file_count;

    document.getElementById(
        "transactionCount"
    ).textContent =
        state.transaction_count;

    document.getElementById(
        "corruptedCount"
    ).textContent =
        disk.corrupted;

    document.getElementById(
        "recoverySuccess"
    ).textContent =
        `${state.recovery_success}%`;
}


function updateDisk(state) {

    const grid =
        document.getElementById(
            "diskGrid"
        );

    grid.innerHTML = "";

    state.disk.blocks.forEach(
        block => {

            const element =
                document.createElement(
                    "div"
                );

            const status =
                String(
                    block.status || "FREE"
                ).toLowerCase();

            element.className =
                `disk-block ${status}`;

            const blockFile =
                block.file
                    ? escapeHtml(block.file)
                    : "—";

            element.innerHTML = `
                <strong>${block.id}</strong>
                <span>${escapeHtml(block.status)}</span>
                ${
                    block.file
                    ? `<small>${blockFile}</small>`
                    : ""
                }
            `;

            grid.appendChild(element);
        }
    );
}


function updateFileSystem(state) {

    const tree =
        document.getElementById(
            "filesystemTree"
        );

    tree.innerHTML = "";


    // ROOT
    const root =
        document.createElement("div");

    root.className =
        "tree-item root";

    root.innerHTML = `
        <span>📁</span>
        <strong>/</strong>
    `;

    tree.appendChild(root);


    const directories =
        state.directories || {};


    const directoryNames =
        Object.keys(directories)
            .sort();


    if (
        directoryNames.length === 0 &&
        state.file_count === 0
    ) {

        const empty =
            document.createElement(
                "div"
            );

        empty.className =
            "tree-empty";

        empty.textContent =
            "No files or directories";

        tree.appendChild(empty);

        return;
    }


    directoryNames.forEach(
        path => {

            if (path === "/") {
                return;
            }

            const directory =
                directories[path];

            const item =
                document.createElement(
                    "div"
                );

            item.className =
                "tree-item child";

            item.innerHTML = `
                <span>📁</span>
                ${escapeHtml(path)}
            `;

            tree.appendChild(item);


            if (
                directory &&
                Array.isArray(
                    directory.files
                )
            ) {

                directory.files.forEach(
                    fileName => {

                        const file =
                            document.createElement(
                                "div"
                            );

                        file.className =
                            "tree-item grandchild";

                        file.innerHTML = `
                            <span>📄</span>
                            ${escapeHtml(fileName)}
                        `;

                        tree.appendChild(file);
                    }
                );
            }
        }
    );


    // Files not visible through directory
    // structure are still shown.
    const files =
        state.files || {};

    const knownFiles =
        new Set();


    directoryNames.forEach(
        path => {

            const directory =
                directories[path];

            if (
                directory &&
                Array.isArray(
                    directory.files
                )
            ) {

                directory.files.forEach(
                    file => knownFiles.add(file)
                );
            }
        }
    );


    Object.keys(files)
        .filter(
            file =>
                !knownFiles.has(file)
        )
        .forEach(
            fileName => {

                const item =
                    document.createElement(
                        "div"
                    );

                item.className =
                    "tree-item child";

                item.innerHTML = `
                    <span>📄</span>
                    ${escapeHtml(fileName)}
                `;

                tree.appendChild(item);
            }
        );
}


function getTransactionId(transaction) {

    const id =
        transaction.id ??
        transaction.transaction_id ??
        "";

    if (id === "") {
        return "-";
    }

    return `TX${String(id).padStart(3, "0")}`;
}


function getBlocks(transaction) {

    const blocks =
        transaction.blocks || [];

    if (!Array.isArray(blocks)) {
        return "-";
    }

    return blocks.join(", ");
}


function statusClass(status) {

    const value =
        String(status || "")
            .toLowerCase();

    if (value.includes("commit")) {
        return "committed";
    }

    if (value.includes("recover")) {
        return "recovered";
    }

    if (value.includes("incomplete")) {
        return "incomplete";
    }

    if (value.includes("rollback")) {
        return "rollback";
    }

    return "";
}


function updateJournal(state) {

    const body =
        document.getElementById(
            "journalBody"
        );

    body.innerHTML = "";


    const transactions =
        state.transactions || [];


    if (transactions.length === 0) {

        body.innerHTML = `
            <tr>
                <td colspan="5"
                    class="empty-table">
                    No journal transactions yet.
                </td>
            </tr>
        `;

        return;
    }


    transactions
        .slice()
        .reverse()
        .forEach(transaction => {

            const row =
                document.createElement(
                    "tr"
                );

            const status =
                transaction.status || "-";

            row.innerHTML = `
                <td>
                    ${escapeHtml(
                        getTransactionId(
                            transaction
                        )
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        transaction.operation ||
                        "-"
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        transaction.file_name ||
                        "-"
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        getBlocks(
                            transaction
                        )
                    )}
                </td>

                <td>
                    <span class="badge
                        ${statusClass(status)}">
                        ${escapeHtml(status)}
                    </span>
                </td>
            `;

            body.appendChild(row);
        });
}


function updateCrashBlocks(state) {

    const target =
        document.getElementById(
            "crashBlocks"
        );

    const corrupted =
        state.disk.corrupted;

    if (corrupted > 0) {

        const blocks =
            state.disk.blocks
                .filter(
                    block =>
                        block.status ===
                        "CORRUPTED"
                )
                .map(
                    block =>
                        block.id
                );

        target.innerHTML = `
            <strong>
                Corrupted blocks:
            </strong>

            ${blocks.join(", ")}
        `;

    } else {

        target.textContent =
            "No corrupted blocks detected.";
    }
}


function setConsistencyHealthy() {

    const box =
        document.getElementById(
            "consistencyStatus"
        );

    box.className =
        "consistency-status healthy";

    box.innerHTML = `
        <div class="check-icon">
            ✓
        </div>

        <div>

            <strong>
                FILE SYSTEM HEALTHY
            </strong>

            <p>
                No consistency problems detected.
            </p>

        </div>
    `;
}


function setConsistencyBad(message) {

    const box =
        document.getElementById(
            "consistencyStatus"
        );

    box.className =
        "consistency-status unhealthy";

    box.innerHTML = `
        <div class="check-icon bad">
            !
        </div>

        <div>

            <strong>
                INCONSISTENT FILE SYSTEM
            </strong>

            <p>
                ${escapeHtml(message)}
            </p>

        </div>
    `;
}


function consistencyIsHealthy(result) {

    if (!result) {
        return false;
    }

    // The Python ConsistencyChecker directly
    // returns healthy=True/False.
    if (typeof result.healthy === "boolean") {
        return result.healthy;
    }

    // Fallback for older result formats.
    const status = String(
        result.status ||
        result.result ||
        ""
    ).toUpperCase();

    if (
        status.includes("HEALTHY") ||
        status === "CONSISTENT" ||
        status === "OK"
    ) {
        return true;
    }

    return false;
}

function updateState(state) {

    updateMetrics(state);

    updateDisk(state);

    updateFileSystem(state);

    updateJournal(state);

    updateCrashBlocks(state);

    setSystemStatus(
        state.crash_status
    );
}


async function refreshDashboard() {

    try {

        const response =
            await api(
                "/api/state"
            );

        updateState(
            response.state
        );

    } catch (error) {

        console.error(
            error
        );
    }
}


async function createFile() {

    const fileName =
        document.getElementById(
            "fileName"
        ).value.trim();

    const fileSize =
        Number(
            document.getElementById(
                "fileSize"
            ).value
        );

    const directory =
        document.getElementById(
            "fileDirectory"
        ).value.trim();

    const content =
        document.getElementById(
            "fileContent"
        ).value;


    try {

        const response =
            await api(
                "/api/create-file",
                {
                    method: "POST",

                    body: JSON.stringify({
                        file_name: fileName,
                        size: fileSize,
                        content: content,
                        directory:
                            directory || "/"
                    })
                }
            );


        showMessage(
            response.message
        );

        addActivity(
            response.message
        );

        updateState(
            response.state
        );

    } catch (error) {

        showMessage(
            error.message
        );
    }
}


async function modifyFile() {

    const fileName =
        document.getElementById(
            "fileName"
        ).value.trim();

    const content =
        document.getElementById(
            "fileContent"
        ).value;


    try {

        const response =
            await api(
                "/api/modify-file",
                {
                    method: "POST",

                    body: JSON.stringify({
                        file_name: fileName,
                        content: content
                    })
                }
            );


        showMessage(
            response.message
        );

        addActivity(
            response.message
        );

        updateState(
            response.state
        );

    } catch (error) {

        showMessage(
            error.message
        );
    }
}


async function deleteFile() {

    const fileName =
        document.getElementById(
            "fileName"
        ).value.trim();


    try {

        const response =
            await api(
                "/api/delete-file",
                {
                    method: "POST",

                    body: JSON.stringify({
                        file_name: fileName
                    })
                }
            );


        showMessage(
            response.message
        );

        addActivity(
            response.message
        );

        updateState(
            response.state
        );

    } catch (error) {

        showMessage(
            error.message
        );
    }
}


async function createDirectory() {

    const path =
        document.getElementById(
            "directoryPath"
        ).value.trim();


    try {

        const response =
            await api(
                "/api/create-directory",
                {
                    method: "POST",

                    body: JSON.stringify({
                        path: path
                    })
                }
            );


        showMessage(
            response.message
        );

        addActivity(
            response.message
        );

        updateState(
            response.state
        );

    } catch (error) {

        showMessage(
            error.message
        );
    }
}


async function deleteDirectory() {

    const path =
        document.getElementById(
            "directoryPath"
        ).value.trim();


    try {

        const response =
            await api(
                "/api/delete-directory",
                {
                    method: "POST",

                    body: JSON.stringify({
                        path: path
                    })
                }
            );


        showMessage(
            response.message
        );

        addActivity(
            response.message
        );

        updateState(
            response.state
        );

    } catch (error) {

        showMessage(
            error.message
        );
    }
}


async function simulateCrash() {

    try {

        const response =
            await api(
                "/api/crash",
                {
                    method: "POST"
                }
            );


        let message =
            response.message;


        if (
            Array.isArray(
                response.blocks
            )
        ) {

            message +=
                `\n\nCrash blocks: ${
                    response.blocks.join(", ")
                }`;
        }


        showMessage(
            message
        );

        addActivity(
            "Crash simulated. File system is now in a failed state."
        );

        updateState(
            response.state
        );

    } catch (error) {

        showMessage(
            error.message
        );
    }
}


async function recoverFileSystem() {

    try {

        const response =
            await api(
                "/api/recover",
                {
                    method: "POST"
                }
            );


        showMessage(
            response.message
        );

        addActivity(
            "File system recovery completed."
        );

        updateState(
            response.state
        );

    } catch (error) {

        showMessage(
            error.message
        );
    }
}


async function runConsistencyCheck() {

    try {

        const response =
            await api(
                "/api/consistency",
                {
                    method: "POST"
                }
            );


        if (
            consistencyIsHealthy(
                response.result
            )
        ) {

            setConsistencyHealthy();

            showMessage(
                "FILE SYSTEM HEALTHY"
            );

            addActivity(
                "Consistency check passed."
            );

        } else {

            const text =
                JSON.stringify(
                    response.result
                );

            setConsistencyBad(
                text
            );

            showMessage(
                "FILE SYSTEM IS INCONSISTENT"
            );

            addActivity(
                "Consistency check detected problems."
            );
        }


        updateState(
            response.state
        );

    } catch (error) {

        showMessage(
            error.message
        );
    }
}


function updatePerformance(report) {

    if (!report ||
        typeof report !== "object") {

        return;
    }


    const operationTimes =
        report.operation_times ||
        report.operations ||
        {};


    function findTime(
        possibleNames
    ) {

        for (
            const name
            of possibleNames
        ) {

            if (
                operationTimes[name]
                !== undefined
            ) {

                return operationTimes[name];
            }
        }

        return null;
    }


    const create =
        findTime([
            "Create File",
            "create_file"
        ]);

    const modify =
        findTime([
            "Modify File",
            "modify_file"
        ]);

    const recovery =
        findTime([
            "Recovery",
            "recovery"
        ]);

    const crash =
        findTime([
            "Crash Simulation",
            "crash_simulation"
        ]);


    document.getElementById(
        "createTime"
    ).textContent =
        formatTime(create);


    document.getElementById(
        "modifyTime"
    ).textContent =
        formatTime(modify);


    document.getElementById(
        "recoveryTime"
    ).textContent =
        formatTime(recovery);


    document.getElementById(
        "crashTime"
    ).textContent =
        formatTime(crash);


    const placeholder =
        document.getElementById(
            "chartPlaceholder"
        );


    placeholder.innerHTML = `
        <div class="performance-summary">

            <div>
                <span>Disk Utilization</span>
                <strong>
                    ${
                        report.disk_utilization ??
                        "-"
                    }%
                </strong>
            </div>

            <div>
                <span>Transactions</span>
                <strong>
                    ${
                        report.transactions ??
                        "-"
                    }
                </strong>
            </div>

            <div>
                <span>Corrupted Blocks</span>
                <strong>
                    ${
                        report.corrupted_blocks ??
                        "-"
                    }
                </strong>
            </div>

            <div>
                <span>Recovery Success</span>
                <strong>
                    ${
                        report.recovery_success_rate ??
                        "-"
                    }%
                </strong>
            </div>

        </div>
    `;
}


function formatTime(value) {

    if (value === null ||
        value === undefined) {

        return "-";
    }


    if (
        typeof value === "number"
    ) {

        return `${value.toFixed(6)} s`;
    }


    return String(value);
}


async function loadPerformance() {

    try {

        const response =
            await api(
                "/api/performance"
            );

        updatePerformance(
            response.report
        );

    } catch (error) {

        console.error(
            "Performance:",
            error
        );
    }
}


document.addEventListener(
    "DOMContentLoaded",
    () => {

        document.getElementById(
            "createFileBtn"
        ).addEventListener(
            "click",
            createFile
        );


        document.getElementById(
            "modifyFileBtn"
        ).addEventListener(
            "click",
            modifyFile
        );


        document.getElementById(
            "deleteFileBtn"
        ).addEventListener(
            "click",
            deleteFile
        );


        document.getElementById(
            "createDirectoryBtn"
        ).addEventListener(
            "click",
            createDirectory
        );


        document.getElementById(
            "deleteDirectoryBtn"
        ).addEventListener(
            "click",
            deleteDirectory
        );


        document.getElementById(
            "crashBtn"
        ).addEventListener(
            "click",
            simulateCrash
        );


        document.getElementById(
            "recoverBtn"
        ).addEventListener(
            "click",
            recoverFileSystem
        );


        document.getElementById(
            "consistencyBtn"
        ).addEventListener(
            "click",
            runConsistencyCheck
        );


        addActivity(
            "Web dashboard connected to simulator."
        );


        refreshDashboard();

        loadPerformance();

    }
);