echo "CSV created: ${CSV_FILE}"
ls -l "${CSV_FILE}"

# ---------------------------------
# 2) Convert CSV -> Excel using Python
# Requires: python3, pandas, openpyxl
# Install once on agent:
#   pip3 install --user pandas openpyxl
# ---------------------------------
python3 - << PY
import pandas as pd

csv_file = "${CSV_FILE}"
xlsx_file = "${XLSX_FILE}"

df = pd.read_csv(csv_file)
df.to_excel(xlsx_file, index=False)

print("Excel created:", xlsx_file)
PY

# Remove temp CSV so only Excel remains
rm -f "${CSV_FILE}"

echo "Final output:"
ls -l "${XLSX_FILE}"
