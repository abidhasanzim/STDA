#!/usr/bin/env bash
# Download the UCI HAR dataset into data/raw/ (skipped if already present).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW="${ROOT}/data/raw"
URL="https://archive.ics.uci.edu/static/public/240/human+activity+recognition+using+smartphones.zip"

mkdir -p "${RAW}"

if [ -d "${RAW}/UCI HAR Dataset" ]; then
  echo "UCI HAR already present at ${RAW}/UCI HAR Dataset"
  exit 0
fi

echo "Downloading ${URL}"
curl -sSL --retry 3 -o "${RAW}/har.zip" "${URL}"
unzip -o -q "${RAW}/har.zip" -d "${RAW}"
unzip -o -q "${RAW}/UCI HAR Dataset.zip" -d "${RAW}"
rm -rf "${RAW}/__MACOSX"

test -d "${RAW}/UCI HAR Dataset/train/Inertial Signals"
echo "UCI HAR ready at ${RAW}/UCI HAR Dataset"
