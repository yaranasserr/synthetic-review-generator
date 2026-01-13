import csv

def generate_report(csv_path, output_md):
    total = passed = forced_fail = 0
    by_metric = {}

    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for r in reader:
            total += 1
            if r["low_quality_forced"] == "True":
                forced_fail += 1
            if r["passed"] == "True":
                passed += 1
            if r["failed_metric"]:
                by_metric[r["failed_metric"]] = by_metric.get(r["failed_metric"], 0) + 1

    with open(output_md, "w") as f:
        f.write("# Quality Generation Report\n\n")
        f.write(f"- Total attempts: {total}\n")
        f.write(f"- Passed reviews: {passed}\n")
        f.write(f"- Forced low-quality attempts: {forced_fail}\n\n")
        f.write("## Failure Breakdown\n")
        for k, v in by_metric.items():
            f.write(f"- {k}: {v}\n")
