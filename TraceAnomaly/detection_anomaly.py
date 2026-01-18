import csv
import math

# --- Bước 1: Đọc dữ liệu từ CSV ---
data = []
with open(os.path.join(os.getcwd(), "webankdata", "rnvp_result.csv"), newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        data.append({"id": row["id"], "score": float(row["score"])})

# --- Bước 2: Tính trung bình và độ lệch chuẩn (Z-score) ---
scores = [d["score"] for d in data]
mean = sum(scores) / len(scores)
std = math.sqrt(sum((s - mean) ** 2 for s in scores) / len(scores))

# --- Phát hiện outlier theo Z-score ---
z_threshold = -2
outliers_z = [d for d in data if (d["score"] - mean)/std < z_threshold]

# --- Bước 3: Phát hiện outlier theo IQR ---
sorted_scores = sorted(scores)
n = len(sorted_scores)

def quantile(sorted_list, q):
    # simple linear interpolation
    pos = q * (len(sorted_list) - 1)
    lower = int(math.floor(pos))
    upper = int(math.ceil(pos))
    if lower == upper:
        return sorted_list[int(pos)]
    return sorted_list[lower] + (sorted_list[upper] - sorted_list[lower]) * (pos - lower)

Q1 = quantile(sorted_scores, 0.25)
Q3 = quantile(sorted_scores, 0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR

outliers_iqr = [d for d in data if d["score"] < lower_bound]

# --- Bước 4: Kết hợp hai tập outlier ---
outliers = {d["id"]: d["score"] for d in outliers_z + outliers_iqr}  # dùng dict để loại trùng

# --- Bước 5: Xuất ra file CSV ---
with open("faults_TraceAnomaly.csv", "w", newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["id", "score"])
    for id_, score in outliers.items():
        writer.writerow([id_, score])

print(f"Exported {len(outliers)} outlier to file 'faults_TraceAnomaly.csv'")
import matplotlib.pyplot as plt

scores = [d["score"] for d in data]

plt.boxplot(scores)
plt.title("Boxplot của score")
plt.ylabel("Score")
plt.show()
