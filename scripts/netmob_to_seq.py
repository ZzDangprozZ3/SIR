import os, glob, argparse
import numpy as np
import torch

def read_tile_txt(path: str):
    # Each line: YYYYMMDD v1 v2 ... v96 (97 fields total)
    # Some lines may end with 'nan'
    dates = []
    rows = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()  # space-separated
            if len(parts) < 2:
                continue
            dates.append(parts[0])
            vals = []
            for x in parts[1:]:
                if x.lower() == "nan":
                    vals.append(np.nan)
                else:
                    try:
                        vals.append(float(x))
                    except:
                        vals.append(np.nan)
            rows.append(vals)

    X = np.array(rows, dtype=np.float32)  # shape (T, n)
    # Fix NaNs: forward fill per feature, then 0
    # forward-fill
    for j in range(X.shape[1]):
        last = np.nan
        for i in range(X.shape[0]):
            if np.isnan(X[i, j]):
                if not np.isnan(last):
                    X[i, j] = last
            else:
                last = X[i, j]
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    # ts: use 0..T-1 (simple, stable)
    ts = np.arange(X.shape[0], dtype=np.int64)
    # label: all zeros (unsupervised)
    label = np.zeros((X.shape[0],), dtype=np.int64)
    return ts, label, X

def make_windows(ts, label, X, win_size=36, l=10, T=20):
    """
    Mimic rectangle sampling idea:
    - For each offset j in [0..l-1]
    - slide start i from 0..len-win_size step l
    - take window length win_size, then split into T-chunks? (SGmVRNN expects T=20 time steps)
    In SMD preprocess_2nd, they construct rectangles then reshape to (T, ?, n, 1).
    Here we will:
    - take window of length win_size
    - downsample/partition it into exactly T time steps by uniform sampling.
    """
    N = X.shape[0]
    out = []
    for j in range(l):
        for i in range(0, N - win_size + 1, l):
            start = i + j
            end = start + win_size
            if end > N:
                continue
            xw = X[start:end]          # (win_size, n)
            tw = ts[start:end]         # (win_size,)
            lw = label[start:end]      # (win_size,)

            # pick T indices uniformly from the window
            if T == win_size:
                idx = np.arange(win_size)
            else:
                idx = np.linspace(0, win_size - 1, T).round().astype(int)

            xT = xw[idx]   # (T, n)
            tT = tw[idx]   # (T,)
            lT = lw[idx]   # (T,)

            out.append((tT, lT, xT))
    return out

def save_seq(samples, out_dir, start_id=1):
    os.makedirs(out_dir, exist_ok=True)
    k = start_id
    for (tT, lT, xT) in samples:
        # SGmVRNN format: (T, 1, n, 1)
        value = torch.tensor(xT, dtype=torch.float32).view(len(tT), 1, xT.shape[1], 1)
        ts = torch.tensor(tT, dtype=torch.int64).view(len(tT), 1, 1)
        label = torch.tensor(lT, dtype=torch.int64).view(len(tT), 1, 1)
        torch.save({"ts": ts, "label": label, "value": value}, os.path.join(out_dir, f"{k}.seq"))
        k += 1
    return k

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input_glob", required=True, help="glob to tile txt files")
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--max_files", type=int, default=0, help="0 = all, else limit")
    ap.add_argument("--win_size", type=int, default=36)
    ap.add_argument("--l", type=int, default=10)
    ap.add_argument("--T", type=int, default=20)
    ap.add_argument("--start_id", type=int, default=1)
    args = ap.parse_args()

    files = sorted(glob.glob(args.input_glob))
    if args.max_files and args.max_files > 0:
        files = files[:args.max_files]

    seq_id = args.start_id
    total_samples = 0

    for idx, fp in enumerate(files, 1):
        ts, lab, X = read_tile_txt(fp)

        # Sanity: expect 97 fields -> 96 features
        if X.shape[1] != 96:
            print(f"[WARN] {fp} has n={X.shape[1]} (expected 96). Skipping.")
            continue
        if X.shape[0] < args.win_size:
            print(f"[WARN] {fp} too short T={X.shape[0]}. Skipping.")
            continue

        samples = make_windows(ts, lab, X, win_size=args.win_size, l=args.l, T=args.T)
        seq_id = save_seq(samples, args.out_dir, start_id=seq_id)
        total_samples += len(samples)

        if idx % 200 == 0:
            print(f"[{idx}/{len(files)}] processed, total seq={total_samples}")

    print(f"DONE. Wrote {total_samples} seq files into {args.out_dir}")

if __name__ == "__main__":
    main()
