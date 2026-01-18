import os
import csv
import random
import datetime
from collections import defaultdict
import math
import json
# À modifier si necessaire
input_file = os.path.join(os.getcwd(), "faults_TraceAnomaly.csv")
input_dirs = [
    "/data/facebook",
    "/data/netflix"
]
output_file = os.path.join(os.getcwd(), "merged_flows")

with open(output_file, "w", encoding="utf-8") as fout:
    for input_dir in input_dirs:  
        for filename in os.listdir(input_dir):
            if not filename.endswith(".txt"):
                continue

            input_path = os.path.join(input_dir, filename)

            # Lấy phần số cuối cùng làm region_id
            region_id = os.path.splitext(filename)[0].split("_")[-1]
            application = os.path.splitext(filename)[0].split("_")[0]
            with open(input_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) < 2:
                        continue
                    date = parts[0]
                    parts = ['0' if x.lower() == 'nan' else x for x in parts]
                    numbers = parts[1:]
                    flow_id = f"{application}_{region_id}_{date}"
                    formatted = flow_id + ":" + ",".join(numbers)
                    fout.write(formatted + "\n")

print("File created:", output_file)



merged_flows_file = os.path.join(os.getcwd(), "merged_flows")

def yyyymmdd_to_timestamp(date_str):
    dt = datetime.datetime.strptime(date_str, "%Y%m%d")
    timestamp = int(dt.replace(tzinfo=datetime.timezone.utc).timestamp())
    return timestamp

script_dir = os.path.dirname(os.path.abspath(__file__))
script_dir = os.path.join(script_dir, "A_NetMob")
output_file = os.path.join(script_dir, "faults_alertRCA.csv")
# output_file = "faults_alertRCA.csv"

with open(input_file, "r", newline="") as f_in, open(output_file, "w", newline="") as f_out:
    reader = csv.DictReader(f_in)
    writer = csv.writer(f_out)
    
    # Write header
    writer.writerow([
        "timestamp","object","fault_description",
        "kpi","name","node_type","root_cause_node"
    ])
    
    for row in reader:
        parts = row["id"].split("_")
        zone = parts[0]
        zone_id = parts[1]
        date = parts[2]
        
        timestamp = yyyymmdd_to_timestamp(date)
        
        node_id = f"{zone}_{zone_id}"
        writer.writerow([   
            timestamp,
            zone,
            "Traffic anomaly",
            "traffic_volume",
            node_id,
            "Zone",
            node_id
        ])

print("✔ faults_alertRCA.csv created. 1/6")


# ================================================================
# 0. INPUT FILES
# ================================================================
faults_alert_file = output_file

# ================================================================
# 1. TẠO faults_5_root_cause.csv, faults.csv, graph.yml
# ================================================================
data = defaultdict(list)

with open(faults_alert_file, "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        ts = int(row['timestamp'])
        data[ts].append(row)

SERVICE_QUOTA = {
    "Netflix": 2,
    "Facebook": 2
}

filtered = []   # top-5
faults = []     # top-1
timestamp_dict = {}
nodes = set()           # <<< NODES sẽ dùng để filter metric, không cần đọc YAML
edges = []

# Lọc root cause nodes
# for ts in sorted(data.keys()):
#     rows = sorted(data[ts], key=lambda x: int(x['root_cause_node']))
#     selected = rows[:5]
#     filtered.extend(selected)
#     faults.append(rows[0])

#     node_list = [r['root_cause_node'] for r in selected]
#     timestamp_dict[ts] = node_list
#     nodes.update(node_list)    # <<< Danh sách node có ở đây luôn
for ts in sorted(data.keys()):
    rows = data[ts]

    # Group theo service
    service_groups = defaultdict(list)
    for r in rows:
        service_groups[r['object']].append(r)

    selected = []

    # Lấy root cause theo quota mỗi service
    for service, quota in SERVICE_QUOTA.items():
        if service not in service_groups:
            continue

        sorted_rows = sorted(
            service_groups[service],
            key=lambda x: int(x['root_cause_node'].split('_')[1])  # split lấy số ID
        )
        selected.extend(sorted_rows[:quota])


    if not selected:
        continue

    # Top-1 fault = root_cause_node nhỏ nhất trong selected
    top1 = min(selected, key=lambda x: int(x['root_cause_node'].split('_')[1]))
    faults.append(top1)

    filtered.extend(selected)

    node_list = [r['root_cause_node'] for r in selected]
    timestamp_dict[ts] = node_list
    nodes.update(node_list)

# Sinh edges
for ts, selected in timestamp_dict.items():  # timestamp_dict chứa node_list đã lọc
    if not selected:
        continue

    # Chọn source = node nhỏ nhất
    source_node_str = min(selected, key=lambda x: int(x.split('_')[1]))

    # Tạo edges star
    for dst_node in selected:
        if dst_node != source_node_str:
            edges.append((source_node_str, dst_node))
    # nodes đã có trong selected
    nodes.update(selected)

#Save faults_4_root_cause.csv
# with open("faults_5_root_cause.csv", "w", newline='') as f:
#     writer = csv.DictWriter(f, fieldnames=filtered[0].keys())
#     writer.writeheader()
#     writer.writerows(filtered)

# Save faults.csv
with open(os.path.join(script_dir, "faults.csv"), "w", newline='') as f:
    writer = csv.DictWriter(f, fieldnames=faults[0].keys())
    writer.writeheader()
    writer.writerows(faults)

# Save graph.yml
with open(os.path.join(script_dir, "graph.yml"), "w") as f:
    f.write("- class: node\n")
    f.write("  type: Zone\n")
    f.write("  params:\n")
    f.write("    zone:\n")
    for node in sorted(nodes):
        f.write(f"      - {node}\n")
    f.write("  id: \"{zone}\"\n")
    f.write("  metrics:\n")
    f.write("    - \"{zone}##traffic_volume\"\n\n")

    f.write("- class: edge\n")
    f.write("  type: relation\n")
    f.write("  params:\n")
    f.write("    src:\n")
    for s, _ in edges:
        f.write(f"      - {s}\n")
    f.write("    dst:\n")
    for _, d in edges:
        f.write(f"      - {d}\n")
    f.write("  src: \"{src}\"\n")
    f.write("  dst: \"{dst}\"\n")

print("✔ Created faults_5_root_cause.csv, faults.csv, graph.yml 2/6")

# ================================================================
# 2. TRAIN / VALID / TEST SPLIT TỪ faults[] (KHÔNG cần đọc lại)
# ================================================================
fault_list = [(i, int(f['timestamp'])) for i, f in enumerate(faults)]

random.seed(31)
random.shuffle(fault_list)

n = len(fault_list)
n_train = int(n * 0.7)
n_valid = int(n * 0.15)

train_data = fault_list[:n_train]
valid_data = fault_list[n_train:n_train+n_valid]
test_data = fault_list[n_train+n_valid:]

def write_csv(name, arr):
    with open(os.path.join(script_dir, name), "w", newline='') as f:
        w = csv.writer(f)
        w.writerow(["id", "timestamp"])
        w.writerows(arr)

write_csv("train.csv", train_data)
write_csv("valid.csv", valid_data)
write_csv("test.csv", test_data)

print("✔ Created train.csv, valid.csv, test.csv 3/6")

# ================================================================
# 3. CHỈ TẠO METRIC CHO NODE TRONG *nodes* (không đọc yml)
# ================================================================
granularity = 900  # 15 minutes
out_metric = os.path.join(script_dir, "metrics_filtered.csv")

with open(merged_flows_file, "r") as f_in, open(out_metric, "w", newline="") as f_out:
    writer = csv.writer(f_out)
    writer.writerow(["name", "timestamp", "value", "metric_type"])

    for line in f_in:
        line = line.strip()
        if not line:
            continue

        id_part, values_part = line.split(":")
        values = values_part.split(",")

        # Parse ID
        parts = id_part.split("_")
        object = parts[0]        # example: "Facebook" or "Netflix"
        zone = parts[1]          # example: "100006"
        node_id = f"{object}_{zone}"
        date_str = parts[2]      # 20190430

        # ❗ Chỉ giữ node nằm trong graph.yml — DÙNG nodes, không đọc yml
        if node_id not in nodes:
            continue

        dt = datetime.datetime.strptime(date_str, "%Y%m%d")
        ts_base = int(dt.replace(tzinfo=datetime.timezone.utc).timestamp())

        name = f"{node_id}##traffic_volume"
        metric_type = "traffic_volume"

        # write each 15-minute granularity
        for i, val in enumerate(values):
            ts = ts_base + i * granularity
            writer.writerow([name, ts, val, metric_type])

print("✔ Created metrics_filtered.csv (filtered by nodes) 4/6")

data = defaultdict(list)  # lưu dạng {name: [(timestamp, value, metric_type)]}

with open(out_metric, "r") as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        name = row[0]
        timestamp = int(row[1])
        value = float(row[2])
        metric_type = row[3]
        data[name].append((timestamp, value, metric_type))

# Step 2: tính mean và std cho từng metric
stats = {}
for name, values in data.items():
    vals = [v[1] for v in values]
    mean = sum(vals) / len(vals)
    std = math.sqrt(sum((x - mean)**2 for x in vals) / len(vals))
    stats[name] = (mean, std)

# Step 3: ghi lại file với value đã chuẩn hóa
with open(os.path.join(script_dir, "metrics.norm.csv"), "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["name", "timestamp", "value", "metric_type"])
    for name, values in data.items():
        mean, std = stats[name]
        for timestamp, value, metric_type in values:
            norm_value = (value - mean) / std if std != 0 else 0.0
            writer.writerow([name, timestamp, norm_value, metric_type])
print("✔ Created metrics.norm.csv (filtered by nodes) 5/6")

with open(os.path.join(script_dir, "anomaly_direction_constraint.json"), "w") as f:
    json.dump({"traffic_volume": "b"}, f)

print(f"✔ Created anomaly_direction_constraint.json 6/6")

print("\n🎉 DONE — FULL PIPELINE")
