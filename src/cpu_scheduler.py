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
            "turnaround": completion - p["arrival"]
        })

        time = completion

    return result


def calculate_averages(result):
    total_waiting = sum(p["waiting"] for p in result)
    total_turnaround = sum(p["turnaround"] for p in result)

    n = len(result)

    return {
        "average_waiting": total_waiting / n,
        "average_turnaround": total_turnaround / n
    }


def display_result(name, result):
    print(f"\n{name}")
    print("-" * 65)

    print(
        f"{'PID':<8}"
        f"{'Arrival':<10}"
        f"{'Burst':<8}"
        f"{'Start':<8}"
        f"{'Completion':<12}"
        f"{'Waiting':<10}"
        f"{'Turnaround':<12}"
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
        )

    averages = calculate_averages(result)

    print(f"\nAverage Waiting Time    : {averages['average_waiting']:.2f}")
    print(f"Average Turnaround Time : {averages['average_turnaround']:.2f}")


def main():
    processes = []

    n = int(input("Enter number of processes: "))

    for i in range(n):
        pid = f"P{i + 1}"
        arrival = int(input(f"Enter arrival time for {pid}: "))
        burst = int(input(f"Enter burst time for {pid}: "))

        processes.append({
            "pid": pid,
            "arrival": arrival,
            "burst": burst
        })

    result = fcfs(processes)
    display_result("FCFS Scheduling", result)


if __name__ == "__main__":
    main()