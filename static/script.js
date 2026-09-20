let refreshTimer = null;
let refreshInProgress = false;
let operationInProgress = false;


/* =========================================================
   UTILITY
========================================================= */

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


async function api(url, options = {}) {

    const response = await fetch(url, {
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        ...options
    });


    let data = {};

    try {
        data = await response.json();
    }
    catch {
        throw new Error(
            `Server returned HTTP ${response.status}.`
        );
    }


    if (
        !response.ok ||
        data.success === false
    ) {
        throw new Error(
            data.message ||
            "Operation failed."
        );
    }


    return data;
}


function showMessage(message) {
    alert(String(message ?? ""));
}


/* =========================================================
   SIDEBAR NAVIGATION
========================================================= */

function setupNavigation() {

    const buttons =
        document.querySelectorAll(
            ".nav-item"
        );


    const titles = {

        overview: {
            title: "System Overview",
            subtitle:
                "Monitor filesystem, journal and recovery state"
        },

        files: {
            title: "File System Management",
            subtitle:
                "Create, modify, delete and organize files"
        },

        journal: {
            title: "Journal Monitor",
            subtitle:
                "Track transaction state and crash consistency"
        },

        recovery: {
            title: "Crash & Recovery",
            subtitle:
                "Simulate filesystem failure and restore consistency"
        },

        performance: {
            title: "Performance Analysis",
            subtitle:
                "Runtime measurements collected by the simulator"
        }
    };


    buttons.forEach(button => {

        button.addEventListener(
            "click",
            () => {

                const sectionName =
                    button.dataset.section;


                buttons.forEach(item => {

                    item.classList.remove(
                        "active"
                    );

                });


                button.classList.add(
                    "active"
                );


                document
                    .querySelectorAll(
                        ".page-section"
                    )
                    .forEach(section => {

                        section.classList.remove(
                            "active-section"
                        );

                    });


                const target =
                    document.getElementById(
                        sectionName
                    );


                if (target) {

                    target.classList.add(
                        "active-section"
                    );

                }


                const info =
                    titles[sectionName];


                if (info) {

                    const pageTitle =
                        document.getElementById(
                            "pageTitle"
                        );

                    const pageSubtitle =
                        document.getElementById(
                            "pageSubtitle"
                        );


                    if (pageTitle) {
                        pageTitle.textContent =
                            info.title;
                    }


                    if (pageSubtitle) {
                        pageSubtitle.textContent =
                            info.subtitle;
                    }

                }

            }
        );

    });

}


/* =========================================================
   SYSTEM STATUS
========================================================= */

function setSystemStatus(status) {

    const statusBox =
        document.getElementById(
            "systemStatus"
        );

    const statusText =
        document.getElementById(
            "systemStatusText"
        );


    if (
        !statusBox ||
        !statusText
    ) {
        return;
    }


    const normalized =
        String(
            status || "NORMAL"
        ).toUpperCase();


    statusText.textContent =
        normalized;


    statusBox.classList.remove(
        "normal",
        "crashed",
        "recovering"
    );


    if (
        normalized.includes(
            "CRASH"
        )
    ) {

        statusBox.classList.add(
            "crashed"
        );

    }
    else if (
        normalized.includes(
            "RECOVER"
        )
    ) {

        statusBox.classList.add(
            "recovering"
        );

    }
    else {

        statusBox.classList.add(
            "normal"
        );

    }

}


/* =========================================================
   METRICS
========================================================= */

function updateMetrics(state) {

    const disk =
        state.disk || {};


    const diskUtilization =
        document.getElementById(
            "diskUtilization"
        );

    const diskUsageText =
        document.getElementById(
            "diskUsageText"
        );

    const fileCount =
        document.getElementById(
            "fileCount"
        );

    const transactionCount =
        document.getElementById(
            "transactionCount"
        );

    const corruptedCount =
        document.getElementById(
            "corruptedCount"
        );

    const recoverySuccess =
        document.getElementById(
            "recoverySuccess"
        );


    if (diskUtilization) {

        diskUtilization.textContent =
            `${Number(
                disk.utilization || 0
            )}%`;

    }


    if (diskUsageText) {

        diskUsageText.textContent =
            `${Number(
                disk.used || 0
            )} / ${Number(
                disk.total || 0
            )} blocks used`;

    }


    if (fileCount) {

        fileCount.textContent =
            String(
                state.file_count ?? 0
            );

    }


    if (transactionCount) {

        transactionCount.textContent =
            String(
                state.transaction_count ?? 0
            );

    }


    if (corruptedCount) {

        corruptedCount.textContent =
            String(
                disk.corrupted ?? 0
            );

    }


    if (recoverySuccess) {

        recoverySuccess.textContent =
            `${Number(
                state.recovery_success ?? 0
            )}%`;

    }

}


/* =========================================================
   VIRTUAL DISK
========================================================= */

function updateDisk(state) {

    const grid =
        document.getElementById(
            "diskGrid"
        );


    if (!grid) {
        return;
    }


    grid.innerHTML = "";


    const blocks =
        Array.isArray(
            state?.disk?.blocks
        )
            ? state.disk.blocks
            : [];


    if (blocks.length === 0) {

        grid.innerHTML =
            `
            <div class="empty-state">
                No disk blocks available.
            </div>
            `;

        return;
    }


    blocks.forEach(block => {

        const element =
            document.createElement(
                "div"
            );


        const status =
            String(
                block.status ||
                "FREE"
            ).toLowerCase();


        element.className =
            `disk-block ${status}`;


        element.title =
            block.file
                ? `Block ${block.id} • ${block.status} • ${block.file}`
                : `Block ${block.id} • ${block.status}`;


        element.innerHTML = `
            <strong>
                ${escapeHtml(block.id)}
            </strong>

            <span>
                ${escapeHtml(block.status)}
            </span>

            ${
                block.file
                    ? `
                        <small
                            title="${escapeHtml(block.file)}"
                        >
                            ${escapeHtml(block.file)}
                        </small>
                      `
                    : ""
            }
        `;


        grid.appendChild(
            element
        );

    });

}


/* =========================================================
   FILE SYSTEM TREE
========================================================= */

function renderFileSystemTree(
    tree,
    state
) {

    if (!tree) {
        return;
    }


    tree.innerHTML = "";


    const root =
        document.createElement(
            "div"
        );


    root.className =
        "tree-item root";


    root.innerHTML = `
        <span>📁</span>
        <strong>/</strong>
    `;


    tree.appendChild(
        root
    );


    const directories =
        state?.directories &&
        typeof state.directories === "object"
            ? state.directories
            : {};


    const files =
        state?.files &&
        typeof state.files === "object"
            ? state.files
            : {};


    const directoryNames =
        Object.keys(
            directories
        ).sort();


    const knownFiles =
        new Set();


    directoryNames.forEach(path => {

        const directory =
            directories[path];


        if (
            directory &&
            Array.isArray(
                directory.files
            )
        ) {

            directory.files.forEach(
                file => {
                    knownFiles.add(
                        String(file)
                    );
                }
            );

        }

    });


    if (
        directoryNames.length === 0 &&
        Object.keys(files).length === 0
    ) {

        const empty =
            document.createElement(
                "div"
            );


        empty.className =
            "tree-empty";


        empty.textContent =
            "No files or directories";


        tree.appendChild(
            empty
        );


        return;
    }


    directoryNames.forEach(path => {

        if (path === "/") {
            return;
        }


        const item =
            document.createElement(
                "div"
            );


        item.className =
            "tree-item child";


        item.innerHTML = `
            <span>📁</span>
            <span>
                ${escapeHtml(path)}
            </span>
        `;


        tree.appendChild(
            item
        );


        const directory =
            directories[path];


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
                        <span>
                            ${escapeHtml(fileName)}
                        </span>
                    `;


                    tree.appendChild(
                        file
                    );

                }
            );

        }

    });


    Object.keys(files)
        .filter(
            fileName =>
                !knownFiles.has(
                    fileName
                )
        )
        .sort()
        .forEach(fileName => {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "tree-item child";


            item.innerHTML = `
                <span>📄</span>
                <span>
                    ${escapeHtml(fileName)}
                </span>
            `;


            tree.appendChild(
                item
            );

        });

}


function updateFileSystem(state) {

    const trees =
        document.querySelectorAll(
            ".filesystem-tree"
        );


    trees.forEach(
        tree => {
            renderFileSystemTree(
                tree,
                state
            );
        }
    );

}


/* =========================================================
   TRANSACTION HELPERS
========================================================= */

function getTransactionId(
    transaction
) {

    const raw =
        transaction?.id ??
        transaction?.transaction_id ??
        "";


    if (raw === "") {
        return "-";
    }


    const text =
        String(raw);


    if (
        text
            .toUpperCase()
            .startsWith("TX")
    ) {
        return text;
    }


    return (
        `TX${text.padStart(
            3,
            "0"
        )}`
    );

}


function getBlocks(
    transaction
) {

    const blocks =
        transaction?.blocks;


    if (
        Array.isArray(
            blocks
        )
    ) {

        return blocks.length
            ? blocks.join(", ")
            : "-";

    }


    if (
        blocks !== undefined &&
        blocks !== null
    ) {

        return String(
            blocks
        );

    }


    return "-";

}


function statusClass(
    status
) {

    const value =
        String(
            status || ""
        ).toLowerCase();


    if (
        value.includes(
            "commit"
        )
    ) {
        return "committed";
    }


    if (
        value.includes(
            "recover"
        )
    ) {
        return "recovered";
    }


    if (
        value.includes(
            "incomplete"
        ) ||
        value.includes(
            "pending"
        )
    ) {
        return "incomplete";
    }


    if (
        value.includes(
            "rollback"
        ) ||
        value.includes(
            "undo"
        )
    ) {
        return "rollback";
    }


    return "";

}


/* =========================================================
   JOURNAL TABLE
========================================================= */

function renderJournalTable(
    body,
    transactions
) {

    if (!body) {
        return;
    }


    body.innerHTML = "";


    if (
        !transactions ||
        transactions.length === 0
    ) {

        body.innerHTML = `
            <tr>
                <td
                    colspan="5"
                    class="empty-table"
                >
                    No journal transactions yet.
                </td>
            </tr>
        `;

        return;
    }


    transactions
        .slice()
        .reverse()
        .forEach(
            transaction => {

                const row =
                    document.createElement(
                        "tr"
                    );


                const status =
                    String(
                        transaction?.status ??
                        "-"
                    );


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
                            transaction?.operation ??
                            "-"
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            transaction?.file_name ??
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

                        <span
                            class="badge ${statusClass(status)}"
                        >
                            ${escapeHtml(
                                status
                            )}
                        </span>

                    </td>

                `;


                body.appendChild(
                    row
                );

            }
        );

}


function updateJournal(state) {

    const transactions =
        Array.isArray(
            state?.transactions
        )
            ? state.transactions
            : [];


    const body =
        document.getElementById(
            "journalBody"
        );


    const bodyFull =
        document.getElementById(
            "journalBodyFull"
        );


    renderJournalTable(
        body,
        transactions
    );


    renderJournalTable(
        bodyFull,
        transactions
    );

}


/* =========================================================
   CRASH INFORMATION
========================================================= */

function updateCrashBlocks(
    state
) {

    const target =
        document.getElementById(
            "crashBlocks"
        );


    if (!target) {
        return;
    }


    const blocks =
        Array.isArray(
            state?.disk?.blocks
        )
            ? state.disk.blocks
            : [];


    const corrupted =
        blocks
            .filter(
                block =>
                    String(
                        block.status ||
                        ""
                    ).toUpperCase()
                    ===
                    "CORRUPTED"
            )
            .map(
                block => block.id
            );


    if (
        corrupted.length > 0
    ) {

        target.innerHTML = `
            <strong>
                Corrupted blocks:
            </strong>

            ${escapeHtml(
                corrupted.join(", ")
            )}
        `;

    }
    else {

        target.textContent =
            "No corrupted blocks detected.";

    }

}


/* =========================================================
   CONSISTENCY
========================================================= */

function setConsistencyHealthy() {

    const box =
        document.getElementById(
            "consistencyStatus"
        );


    if (!box) {
        return;
    }


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

            <span>
                No consistency problems detected.
            </span>

        </div>

    `;

}


function setConsistencyBad(
    message
) {

    const box =
        document.getElementById(
            "consistencyStatus"
        );


    if (!box) {
        return;
    }


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

            <span>
                ${escapeHtml(message)}
            </span>

        </div>

    `;

}


function updateConsistency(
    state
) {

    const result =
        state?.consistency;


    if (!result) {
        return;
    }


    if (
        result.healthy === true
    ) {

        setConsistencyHealthy();

        return;
    }


    const errors =
        Array.isArray(
            result.errors
        )
            ? result.errors
            : [];


    const message =
        errors.length > 0
            ? errors.join(" • ")
            : (
                result.status ||
                result.message ||
                "Consistency problems detected."
            );


    setConsistencyBad(
        message
    );

}


/* =========================================================
   ACTIVITY LOG
========================================================= */

function updateActivityLog(
    state
) {

    const log =
        document.getElementById(
            "activityLog"
        );


    if (!log) {
        return;
    }


    const entries =
        Array.isArray(
            state?.activity_log
        )
            ? state.activity_log
            : [];


    log.innerHTML = "";


    if (
        entries.length === 0
    ) {

        log.innerHTML = `

            <div class="log-entry">

                <span class="log-time">
                    --:--:--
                </span>

                <span>
                    No activity recorded yet.
                </span>

            </div>

        `;

        return;
    }


    entries
        .slice(
            0,
            20
        )
        .forEach(
            entry => {

                const row =
                    document.createElement(
                        "div"
                    );


                row.className =
                    "log-entry";


                row.innerHTML = `

                    <span class="log-time">
                        ${escapeHtml(
                            entry?.time ?? ""
                        )}
                    </span>

                    <span>
                        ${escapeHtml(
                            entry?.message ?? ""
                        )}
                    </span>

                `;


                log.appendChild(
                    row
                );

            }
        );

}


/* =========================================================
   PERFORMANCE
========================================================= */

function formatTime(
    value
) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "-";
    }


    if (
        typeof value === "number" &&
        Number.isFinite(value)
    ) {

        return (
            `${value.toFixed(6)} s`
        );

    }


    return String(value);

}


function findOperationTime(
    operationTimes,
    names
) {

    for (
        const name
        of names
    ) {

        if (
            Object.prototype.hasOwnProperty.call(
                operationTimes,
                name
            )
        ) {

            return operationTimes[name];

        }

    }


    return null;

}


function updatePerformance(
    report
) {

    if (
        !report ||
        typeof report !== "object"
    ) {
        return;
    }


    const operationTimes =
        report.operation_times ||
        report.operations ||
        {};


    const create =
        findOperationTime(
            operationTimes,
            [
                "Create File",
                "create_file",
                "CREATE"
            ]
        );


    const modify =
        findOperationTime(
            operationTimes,
            [
                "Modify File",
                "modify_file",
                "MODIFY"
            ]
        );


    const recovery =
        findOperationTime(
            operationTimes,
            [
                "Recovery",
                "recovery",
                "RECOVER"
            ]
        );


    const crash =
        findOperationTime(
            operationTimes,
            [
                "Crash Simulation",
                "crash_simulation",
                "Crash",
                "CRASH"
            ]
        );


    const createElement =
        document.getElementById(
            "createTime"
        );


    const modifyElement =
        document.getElementById(
            "modifyTime"
        );


    const recoveryElement =
        document.getElementById(
            "recoveryTime"
        );


    const crashElement =
        document.getElementById(
            "crashTime"
        );


    if (createElement) {

        createElement.textContent =
            formatTime(
                create
            );

    }


    if (modifyElement) {

        modifyElement.textContent =
            formatTime(
                modify
            );

    }


    if (recoveryElement) {

        recoveryElement.textContent =
            formatTime(
                recovery
            );

    }


    if (crashElement) {

        crashElement.textContent =
            formatTime(
                crash
            );

    }


    const placeholder =
        document.getElementById(
            "chartPlaceholder"
        );


    if (!placeholder) {
        return;
    }


    const diskUtilization =
        report.disk_utilization ??
        report.disk?.utilization ??
        "-";


    const transactions =
        report.transactions ??
        report.transaction_count ??
        "-";


    const corruptedBlocks =
        report.corrupted_blocks ??
        report.corrupted ??
        "-";


    const recoveredBlocks =
        report.recovered_blocks ??
        report.recovered ??
        "-";


    const recoverySuccess =
        report.recovery_success_rate ??
        report.recovery_success ??
        "-";


    placeholder.innerHTML = `

        <div>

            <span>
                Disk Utilization
            </span>

            <strong>
                ${escapeHtml(
                    diskUtilization
                )}%
            </strong>

        </div>


        <div>

            <span>
                Transactions
            </span>

            <strong>
                ${escapeHtml(
                    transactions
                )}
            </strong>

        </div>


        <div>

            <span>
                Corrupted Blocks
            </span>

            <strong>
                ${escapeHtml(
                    corruptedBlocks
                )}
            </strong>

        </div>


        <div>

            <span>
                Recovered Blocks
            </span>

            <strong>
                ${escapeHtml(
                    recoveredBlocks
                )}
            </strong>

        </div>


        <div>

            <span>
                Recovery Success
            </span>

            <strong>
                ${escapeHtml(
                    recoverySuccess
                )}%
            </strong>

        </div>

    `;

}


/* =========================================================
   CRASH / RECOVERY BUTTON STATE
========================================================= */

function updateRecoveryControls(
    state
) {

    const crashed =
        String(
            state?.crash_status ||
            ""
        )
            .toUpperCase()
            .includes(
                "CRASH"
            );


    const recoverButton =
        document.getElementById(
            "recoverBtn"
        );


    const crashButton =
        document.getElementById(
            "crashBtn"
        );


    if (recoverButton) {

        recoverButton.disabled =
            !crashed;

    }


    if (crashButton) {

        crashButton.disabled =
            crashed;

    }


    const recoveryIcon =
        document.getElementById(
            "recoveryIcon"
        );


    if (recoveryIcon) {

        if (crashed) {

            recoveryIcon.textContent =
                "!";

            recoveryIcon.style.background =
                "#2c1015";

            recoveryIcon.style.color =
                "#fca5a5";

        }
        else {

            recoveryIcon.textContent =
                "✓";

            recoveryIcon.style.background =
                "#0d241b";

            recoveryIcon.style.color =
                "#86efac";

        }

    }

}


/* =========================================================
   MASTER STATE UPDATE
========================================================= */

function updateState(
    state
) {

    if (
        !state ||
        typeof state !== "object"
    ) {
        return;
    }


    updateMetrics(
        state
    );


    updateDisk(
        state
    );


    updateFileSystem(
        state
    );


    updateJournal(
        state
    );


    updateCrashBlocks(
        state
    );


    updateConsistency(
        state
    );


    updatePerformance(
        state.performance
    );


    updateActivityLog(
        state
    );


    setSystemStatus(
        state.crash_status
    );


    updateRecoveryControls(
        state
    );

}


/* =========================================================
   REFRESH
========================================================= */

async function refreshDashboard() {

    if (
        refreshInProgress
    ) {
        return;
    }


    refreshInProgress =
        true;


    try {

        const response =
            await api(
                "/api/state"
            );


        updateState(
            response.state
        );

    }
    catch (error) {

        console.error(
            "Dashboard refresh:",
            error
        );

    }
    finally {

        refreshInProgress =
            false;

    }

}


/* =========================================================
   OPERATION CONTROL
========================================================= */

async function runOperation(
    requestFactory,
    busyButtonId
) {

    if (
        operationInProgress
    ) {
        return;
    }


    operationInProgress =
        true;


    const button =
        document.getElementById(
            busyButtonId
        );


    let originalText =
        "";


    if (button) {

        originalText =
            button.textContent;


        button.disabled =
            true;


        button.textContent =
            "Working...";

    }


    try {

        const response =
            await requestFactory();


        if (response.state) {

            updateState(
                response.state
            );

        }
        else {

            await refreshDashboard();

        }


        if (response.message) {

            showMessage(
                response.message
            );

        }

    }
    catch (error) {

        showMessage(
            error.message
        );

    }
    finally {

        operationInProgress =
            false;


        if (button) {

            button.disabled =
                false;

            button.textContent =
                originalText;

        }


        await refreshDashboard();

    }

}


/* =========================================================
   INPUT
========================================================= */

function inputValue(
    id
) {

    const element =
        document.getElementById(
            id
        );


    return element
        ? element.value
        : "";

}


/* =========================================================
   FILE OPERATIONS
========================================================= */

async function createFile() {

    const fileName =
        inputValue(
            "fileName"
        ).trim();


    const size =
        Number(
            inputValue(
                "fileSize"
            )
        );


    const directory =
        inputValue(
            "fileDirectory"
        ).trim() || "/";


    const content =
        inputValue(
            "fileContent"
        );


    if (!fileName) {

        showMessage(
            "Enter a file name."
        );

        return;
    }


    if (
        !Number.isFinite(
            size
        ) ||
        size <= 0
    ) {

        showMessage(
            "File size must be greater than 0."
        );

        return;
    }


    await runOperation(

        () =>
            api(
                "/api/create-file",
                {
                    method: "POST",

                    body:
                        JSON.stringify(
                            {
                                file_name:
                                    fileName,

                                size:
                                    size,

                                content:
                                    content,

                                directory:
                                    directory
                            }
                        )
                }
            ),

        "createFileBtn"

    );

}


async function modifyFile() {

    const fileName =
        inputValue(
            "fileName"
        ).trim();


    const content =
        inputValue(
            "fileContent"
        );


    if (!fileName) {

        showMessage(
            "Enter a file name."
        );

        return;
    }


    await runOperation(

        () =>
            api(
                "/api/modify-file",
                {
                    method: "POST",

                    body:
                        JSON.stringify(
                            {
                                file_name:
                                    fileName,

                                content:
                                    content
                            }
                        )
                }
            ),

        "modifyFileBtn"

    );

}


async function deleteFile() {

    const fileName =
        inputValue(
            "fileName"
        ).trim();


    if (!fileName) {

        showMessage(
            "Enter a file name."
        );

        return;
    }


    await runOperation(

        () =>
            api(
                "/api/delete-file",
                {
                    method: "POST",

                    body:
                        JSON.stringify(
                            {
                                file_name:
                                    fileName
                            }
                        )
                }
            ),

        "deleteFileBtn"

    );

}


/* =========================================================
   DIRECTORY OPERATIONS
========================================================= */

async function createDirectory() {

    const path =
        inputValue(
            "directoryPath"
        ).trim();


    if (!path) {

        showMessage(
            "Enter a directory path."
        );

        return;
    }


    await runOperation(

        () =>
            api(
                "/api/create-directory",
                {
                    method: "POST",

                    body:
                        JSON.stringify(
                            {
                                path:
                                    path
                            }
                        )
                }
            ),

        "createDirectoryBtn"

    );

}


async function deleteDirectory() {

    const path =
        inputValue(
            "directoryPath"
        ).trim();


    if (!path) {

        showMessage(
            "Enter a directory path."
        );

        return;
    }


    await runOperation(

        () =>
            api(
                "/api/delete-directory",
                {
                    method: "POST",

                    body:
                        JSON.stringify(
                            {
                                path:
                                    path
                            }
                        )
                }
            ),

        "deleteDirectoryBtn"

    );

}


/* =========================================================
   CRASH
========================================================= */

async function simulateCrash() {

    await runOperation(

        async () => {

            const response =
                await api(
                    "/api/crash",
                    {
                        method:
                            "POST"
                    }
                );


            if (
                Array.isArray(
                    response.blocks
                ) &&
                response.blocks.length
            ) {

                showMessage(
                    `${response.message}\n\n` +
                    `Crash blocks: ` +
                    `${response.blocks.join(", ")}`
                );

            }


            return response;

        },

        "crashBtn"

    );

}


/* =========================================================
   RECOVERY
========================================================= */

async function recoverFileSystem() {

    await runOperation(

        () =>
            api(
                "/api/recover",
                {
                    method:
                        "POST"
                }
            ),

        "recoverBtn"

    );

}


/* =========================================================
   CONSISTENCY
========================================================= */

async function runConsistencyCheck() {

    await runOperation(

        () =>
            api(
                "/api/consistency",
                {
                    method:
                        "POST"
                }
            ),

        "consistencyBtn"

    );

}


/* =========================================================
   START
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    async () => {

        setupNavigation();


        const handlers = {

            createFileBtn:
                createFile,

            modifyFileBtn:
                modifyFile,

            deleteFileBtn:
                deleteFile,

            createDirectoryBtn:
                createDirectory,

            deleteDirectoryBtn:
                deleteDirectory,

            crashBtn:
                simulateCrash,

            recoverBtn:
                recoverFileSystem,

            consistencyBtn:
                runConsistencyCheck

        };


        Object.entries(
            handlers
        ).forEach(
            ([id, handler]) => {

                const button =
                    document.getElementById(
                        id
                    );


                if (button) {

                    button.addEventListener(
                        "click",
                        handler
                    );

                }

            }
        );


        await refreshDashboard();


        refreshTimer =
            setInterval(
                refreshDashboard,
                2000
            );

    }
);