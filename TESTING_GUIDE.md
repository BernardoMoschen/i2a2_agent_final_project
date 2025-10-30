# 🧪 Testing Guide - Report Downloads & Charts

## Quick Start Test

### Prerequisites
```bash
cd /home/bmos/private/private_repos/i2a2/projeto_final

# Ensure latest packages
pip install -q -r requirements.txt

# Start Streamlit (if not already running)
streamlit run src/ui/app.py --server.port=8503
```

---

## Test 1: Plotly Chart Rendering ✨

### Scenario: Generate validation error chart

**Steps:**
1. Open http://localhost:8503 in browser
2. Go to **Home** tab 💬
3. In chat, type:
   ```
   Gere um gráfico de distribuição de erros de validação
   ```
4. Watch the response...

**Expected Result:**
- ✅ Agent responds with analysis text
- ✅ Interactive chart appears with:
  - Bar chart showing error counts
  - Hover tooltips with values
  - Title: "Problemas de Validação por Severidade"
  - X-axis: Severity levels (error, warning, info)
  - Y-axis: Count of problems
- ✅ Text summary below chart

**If it doesn't work:**
```
1. Check browser console (F12 → Console tab)
2. Look for JavaScript errors
3. Try refreshing (F5)
4. Check terminal for Python errors
```

---

## Test 2: File Download Detection 📥

### Scenario: Generate validation report as CSV

**Steps:**
1. Open http://localhost:8503 in browser
2. Go to **Home** tab 💬
3. In chat, type:
   ```
   Gere um relatório de documentos com problemas em CSV
   ```
4. Wait for agent response...

**Expected Result:**
- ✅ Agent responds with filename like: `documents_with_issues_20251030_XXXXXX.csv`
- ✅ Below the text, a download button appears:
  ```
  📄 Download documents_with_issues_20251030_XXXXXX.csv
  ```
- ✅ Click button → file downloads immediately

**If no button appears:**
1. Check that file exists:
   ```bash
   ls ./reports/ | grep csv
   ```
2. Verify filename matches pattern: `{name}_{YYYYMMDD}_{HHMMSS}.csv`
3. Check browser console for errors

---

## Test 3: Excel File Download 📊

### Scenario: Generate report as Excel

**Steps:**
1. Open http://localhost:8503 in browser
2. Go to **Reports** tab 📈
3. Select report type: "Issues Grouped by Type"
4. Output format: **Excel**
5. Click "Generate Report" button
6. Wait for generation...

**Expected Result:**
- ✅ Report generates successfully
- ✅ Message: "✅ Report generated successfully!"
- ✅ Displays row count and other metrics
- ✅ Download button appears:
  ```
  📊 Download issues_by_type_YYYYMMDD_HHMMSS.xlsx
  ```
- ✅ Click button → Excel file downloads

**If download fails:**
1. Check file size:
   ```bash
   ls -lh ./reports/*.xlsx | tail -1
   ```
2. File should be > 1KB
3. Try a different report type

---

## Test 4: Multiple Downloads in One Chat 🎯

### Scenario: Generate multiple reports

**Steps:**
1. In chat, ask:
   ```
   Gere 3 coisas: 
   1) Um gráfico de vendas
   2) Um relatório de compras em CSV
   3) Um gráfico de impostos
   ```

**Expected Result:**
- ✅ Multiple charts and/or buttons appear
- ✅ Each one functional
- ✅ All download buttons work independently

---

## Test 5: File Format Detection 🔍

### Scenario: Verify correct MIME types

**Steps:**
1. Generate different file types:
   - CSV file
   - Excel file
   - PNG image
2. Click each download button
3. Check file properties

**Expected Result:**
- ✅ CSV downloads as text/csv
- ✅ Excel downloads as spreadsheet
- ✅ PNG downloads as image
- ✅ Browser recognizes correct file type

**How to verify:**
```bash
# Check file type on disk
file ./reports/issues_by_type_*.xlsx
file ./reports/documents_with_issues_*.csv
file ./reports/*.png
```

---

## Test 6: Chat History Persistence 💾

### Scenario: Verify files persist in chat history

**Steps:**
1. Generate a report (e.g., CSV file)
2. Download button appears ✅
3. Refresh the page (F5)
4. Scroll up in chat history

**Expected Result:**
- ✅ Message still there
- ✅ Download button still works
- ✅ Can download again
- ✅ No errors on refresh

---

## Test 7: Error Handling 🛑

### Scenario: Test error cases

**Steps:**
1. Delete a file that should exist:
   ```bash
   rm ./reports/documents_with_issues_*.csv
   ```
2. Scroll up to see old message with that file
3. Try clicking download button

**Expected Result:**
- ✅ Graceful error message
- OR
- ✅ Button disappears (file not found)
- ✅ No crash or console errors

**Re-create the file:**
```bash
# Generate a new report to recreate files
```

---

## Test 8: Performance Test ⚡

### Scenario: Large file download

**Steps:**
1. Generate a large report (100+ MB)
2. Click download button
3. Monitor network tab (F12 → Network)

**Expected Result:**
- ✅ Download starts immediately
- ✅ Progress shows in browser
- ✅ File downloads completely
- ✅ No timeout or memory issues

---

## Test 9: Browser Compatibility 🌐

### Test in different browsers

| Browser | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| Charts render | ✅ | ✅ | ✅ | ✅ |
| Files download | ✅ | ✅ | ✅ | ✅ |
| Status | Works | Works | Works | Works |

---

## Test 10: Mobile Testing 📱

### Scenario: Test on mobile browser

**Steps:**
1. Open http://{server-ip}:8503 on mobile
2. Go to chat
3. Generate report
4. Try to download

**Expected Result:**
- ✅ Works on mobile too
- ✅ Download button visible
- ✅ File downloads to device

---

## Automated Test Script

```python
#!/usr/bin/env python3
"""Automated test for file detection."""

import re
from pathlib import Path

def test_file_detection():
    """Test that file detection works."""
    from src.ui.app import extract_file_downloads
    
    # Test cases
    test_cases = [
        {
            'input': 'Arquivo: issues_by_type_20251030_101329.xlsx',
            'expected': 1,
            'name': 'Single XLSX file'
        },
        {
            'input': '''
            Arquivo 1: documents_20251030_120000.csv
            Arquivo 2: issues_20251030_120001.xlsx
            ''',
            'expected': 2,
            'name': 'Multiple files'
        },
        {
            'input': 'Nenhum arquivo aqui',
            'expected': 0,
            'name': 'No files'
        },
    ]
    
    print("🧪 Running file detection tests...\n")
    
    for i, test in enumerate(test_cases, 1):
        _, files = extract_file_downloads(test['input'])
        passed = len(files) == test['expected']
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"Test {i}: {test['name']}")
        print(f"  {status} - Found {len(files)} files (expected {test['expected']})")
        if files:
            for f in files:
                print(f"    - {f['name']}")
        print()

if __name__ == '__main__':
    test_file_detection()
```

**Run the test:**
```bash
cd /home/bmos/private/private_repos/i2a2/projeto_final
python3 << 'EOF'
import re
from pathlib import Path

response = '''Arquivo gerado: issues_by_type_20251030_101329.xlsx'''

file_pattern = r'([a-zA-Z0-9_]+_\d{8}_\d{6}\.(xlsx|csv|png))'
matches = list(re.finditer(file_pattern, response))
print(f"✅ Found {len(matches)} files")
for m in matches:
    print(f"  - {m.group(1)}")
EOF
```

---

## Troubleshooting Checklist

| Issue | Check | Fix |
|-------|-------|-----|
| Charts not rendering | Browser console | Refresh page (F5) |
| Buttons not showing | File exists in ./reports/ | Generate new report |
| Download fails | File permissions | `chmod 644 ./reports/*` |
| Wrong file type | MIME detection | Update src/ui/app.py |
| Slow downloads | File size | Check with `ls -lh` |
| Mobile not working | Server IP | Use `0.0.0.0` in config |

---

## Success Criteria ✅

All tests should pass:
- ✅ Charts render interactively
- ✅ Files detected automatically
- ✅ Download buttons appear
- ✅ Downloads complete
- ✅ Correct file types
- ✅ No errors or crashes
- ✅ Works in chat history
- ✅ Works after refresh
- ✅ Works across browsers

---

## Reporting Issues

If a test fails, collect:
1. **Browser console errors** (F12)
2. **Server terminal output**
3. **File listing**: `ls -la ./reports/`
4. **Test case** that failed
5. **Browser type** and version

Then report with this info to get help.

---

## Quick Reference

```bash
# Start Streamlit
streamlit run src/ui/app.py

# Check reports
ls -la ./reports/

# Check file permissions
chmod 644 ./reports/*

# Check Python errors
python3 -c "from src.ui.app import extract_file_downloads; print('✅ OK')"

# View database
sqlite3 fiscal_documents.db "SELECT COUNT(*) FROM invoices;"
```

---

**Happy Testing!** 🎉
