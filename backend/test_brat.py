import os

print("Starting")

count = 0

for root, dirs, files in os.walk("data/raw/DDICorpusBrat 2"):
    print(root)
    for f in files:
        if f.endswith(".txt"):
            count += 1

print("TXT files:", count)