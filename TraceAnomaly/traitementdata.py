import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

input_dirs = [
    os.path.join(BASE_DIR, "..", "NetMob23", "Facebook"),
    os.path.join(BASE_DIR, "..", "NetMob23", "Netflix")
]
output_file = os.path.join(os.getcwd(), "merged_flows")

with open(output_file, "w", encoding="utf-8") as fout:
    for input_dir in input_dirs:  
        for filename in os.listdir(input_dir):
            if not filename.endswith(".txt"):
                continue

            input_path = os.path.join(input_dir, filename)

            #  region_id
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


# import os

# input_path = r"C:\Users\USER\OneDrive\Máy tính\3TC\SIR\CleUSB\Dataset NetMob23\Facebook1\DL\Facebook_DL_Tile_62968.txt"
# filename_no_ext = os.path.splitext(os.path.basename(input_path))[0]
# output_path = os.path.join(os.getcwd(), filename_no_ext)

# with open(input_path, "r", encoding="utf-8") as f:
#     lines = f.readlines()

# with open(output_path, "w", encoding="utf-8") as f:
#     for line in lines:
#         parts = line.strip().split()
#         if len(parts) < 2:
#             continue
        
#         id_value =  parts[0]
#         numbers = parts[1:]
#         formatted = id_value + ":" + ",".join(numbers)

#         f.write(formatted + "\n")

# print("✔ Đã tạo file:", output_path)