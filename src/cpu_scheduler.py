def fcfs(processes):
    processes = sorted(processes, key=lambda x: x["arrival"])
    time = 0
    result = []

    for p in processes:
        if time < p["arrival"]:
            time = p["arrival"]

        start = time
        completion = start + p["burst"]

        result.append({
            "pid": p["pid"],
            "arrival": p["arrival"],
            "burst": p["burst"],
            "start": start,
            "completion": completion,
            "waiting": start - p["arrival"],
            "turnaround": completion - p["arrival"],
            "response": start - p["arrival"]
        })

        time = completion

    return result


def sjf(processes):
    remaining = [p.copy() for p in processes]
    result = []
    time = 0

    while remaining:
        available = [p for p in remaining if p["arrival"] <= time]

        if not available:
            time = min(p["arrival"] for p in remaining)
            continue

        p = min(available, key=lambda x: (x["burst"], x["arrival"]))
        remaining.remove(p)

        start = time
        completion = start + p["burst"]

        result.append({
            "pid": p["pid"],
            "arrival": p["arrival"],
            "burst": p["burst"],
            "start": start,
            "completion": completion,
            "waiting": start - p["arrival"],
            "turnaround": completion - p["arrival"],
            "response": start - p["arrival"]
        })

        time = completion

    return result


def priority_non_preemptive(processes):
    remaining = [p.copy() for p in processes]
    result = []
    time = 0

    while remaining:
        available = [p for p in remaining if p["arrival"] <= time]

        if not available:
            time = min(p["arrival"] for p in remaining)
            continue

        p = min(
            available,
            key=lambda x: (x["priority"], x["arrival"])
        )

        remaining.remove(p)

        start = time
        completion = start + p["burst"]

        result.append({
            "pid": p["pid"],
            "arrival": p["arrival"],
            "burst": p["burst"],
            "priority": p["priority"],
            "start": start,
            "completion": completion,
            "waiting": start - p["arrival"],
            "turnaround": completion - p["arrival"],
            "response": start - p["arrival"]
        })

        time = completion

    return result


def srtf(processes):
    processes = [p.copy() for p in processes]

    remaining = {
        p["pid"]: p["burst"]
        for p in processes
    }

    first_start = {}
    completion = {}

    time = 0
    completed = 0
    n = len(processes)

    while completed < n:
        available = [
            p for p in processes
            if p["arrival"] <= time
            and remaining[p["pid"]] > 0
        ]

        if not available:
            time += 1
            continue

        p = min(
            available,
            key=lambda x: (
                remaining[x["pid"]],
                x["arrival"]
            )
        )

        pid = p["pid"]

        if pid not in first_start:
            first_start[pid] = time

        remaining[pid] -= 1
        time += 1

        if remaining[pid] == 0:
            completion[pid] = time
            completed += 1

    result = []

    for p in processes:
        pid = p["pid"]
        turnaround = completion[pid] - p["arrival"]
        waiting = turnaround - p["burst"]

        result.append({
            "pid": pid,
            "arrival": p["arrival"],
            "burst": p["burst"],
            "start": first_start[pid],
            "completion": completion[pid],
            "waiting": waiting,
            "turnaround": turnaround,
            "response": first_start[pid] - p["arrival"]
        })

    return sorted(result, key=lambda x: x["completion"])


def priority_preemptive(processes):
    processes = [p.copy() for p in processes]

    remaining = {
        p["pid"]: p["burst"]
        for p in processes
    }

    first_start = {}
    completion = {}

    time = 0
    completed = 0
    n = len(processes)

    while completed < n:
        available = [
            p for p in processes
            if p["arrival"] <= time
            and remaining[p["pid"]] > 0
        ]

        if not available:
            time += 1
            continue

        p = min(
            available,
            key=lambda x: (
                x["priority"],
                x["arrival"]
            )
        )

        pid = p["pid"]

        if pid not in first_start:
            first_start[pid] = time

        remaining[pid] -= 1
        time += 1

        if remaining[pid] == 0:
            completion[pid] = time
            completed += 1

    result = []

    for p in processes:
        pid = p["pid"]
        turnaround = completion[pid] - p["arrival"]
        waiting = turnaround - p["burst"]

        result.append({
            "pid": pid,
            "arrival": p["arrival"],
            "burst": p["burst"],
            "priority": p["priority"],
            "start": first_start[pid],
            "completion": completion[pid],
            "waiting": waiting,
            "turnaround": turnaround,
            "response": first_start[pid] - p["arrival"]
        })

    return sorted(result, key=lambda x: x["completion"])


def round_robin(processes, quantum):
    processes = sorted(
        [p.copy() for p in processes],
        key=lambda x: x["arrival"]
    )

    remaining = {
        p["pid"]: p["burst"]
        for p in processes
    }

    first_start = {}
    completion = {}

    queue = []
    time = 0
    index = 0
    completed = 0

    while completed < len(processes):

        while index < len(processes) and processes[index]["arrival"] <= time:
            queue.append(processes[index])
            index += 1

        if not queue:
            time = processes[index]["arrival"]
            continue

        p = queue.pop(0)
        pid = p["pid"]

        if pid not in first_start:
            first_start[pid] = time

        execution = min(quantum, remaining[pid])

        time += execution
        remaining[pid] -= execution

        while index < len(processes) and processes[index]["arrival"] <= time:
            queue.append(processes[index])
            index += 1

        if remaining[pid] > 0:
            queue.append(p)
        else:
            completion[pid] = time
            completed += 1

    result = []

    for p in processes:
        pid = p["pid"]
        turnaround = completion[pid] - p["arrival"]
        waiting = turnaround - p["burst"]

        result.append({
            "pid": pid,
            "arrival": p["arrival"],
            "burst": p["burst"],
            "start": first_start[pid],
            "completion": completion[pid],
            "waiting": waiting,
            "turnaround": turnaround,
            "response": first_start[pid] - p["arrival"]
        })

    return result


def calculate_averages(result):
    n = len(result)

    return {
        "average_waiting": sum(p["waiting"] for p in result) / n,
        "average_turnaround": sum(p["turnaround"] for p in result) / n,
        "average_response": sum(p["response"] for p in result) / n
    }


def display_result(name, result):
    print("\n" + name)
    print("-" * 85)

    print(
        f"{'PID':<8}"
        f"{'Arrival':<10}"
        f"{'Burst':<8}"
        f"{'Start':<8}"
        f"{'Completion':<12}"
        f"{'Waiting':<10}"
        f"{'Turnaround':<12}"
        f"{'Response':<10}"
    )

    for p in result:
        print(
            f"{p['pid']:<8}"
            f"{p['arrival']:<10}"
            f"{p['burst']:<8}"
            f"{p['start']:<8}"
            f"{p['completion']:<12}"
            f"{p['waiting']:<10}"
            f"{p['turnaround']:<12}"
            f"{p['response']:<10}"
        )

    averages = calculate_averages(result)

    print(f"\nAverage Waiting Time    : {averages['average_waiting']:.2f}")
    print(f"Average Turnaround Time : {averages['average_turnaround']:.2f}")
    print(f"Average Response Time   : {averages['average_response']:.2f}")


def main():
    processes = []

    n = int(input("Enter number of processes: "))

    for i in range(n):
        pid = f"P{i + 1}"

        arrival = int(input(f"Enter arrival time for {pid}: "))
        burst = int(input(f"Enter burst time for {pid}: "))
        priority = int(
            input(f"Enter priority for {pid} (lower = higher): ")
        )

        processes.append({
            "pid": pid,
            "arrival": arrival,
            "burst": burst,
            "priority": priority
        })

    quantum = int(input("Enter time quantum for Round Robin: "))

    algorithms = {
        "FCFS (Non-Preemptive)": fcfs(processes),
        "SJF (Non-Preemptive)": sjf(processes),
        "Priority (Non-Preemptive)": priority_non_preemptive(processes),
        "SRTF (Preemptive)": srtf(processes),
        "Priority (Preemptive)": priority_preemptive(processes),
        "Round Robin (Preemptive)": round_robin(processes, quantum)
    }

    for name, result in algorithms.items():
        display_result(name, result)


if __name__ == "__main__":
    main()