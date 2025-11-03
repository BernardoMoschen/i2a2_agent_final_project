# 📥 Report Download Fix - October 30, 2025

## Problem
When the agent generated a report and provided a download link like `http://localhost:8501/reports/issues_by_type_20251030_101329.xlsx`, clicking the link showed a blank page instead of downloading the file.

## Root Cause
Streamlit doesn't serve static files via HTTP URLs. The Streamlit server doesn't have routes to serve files from the `/reports` directory.

## Solution Implemented

### 1. **Automatic File Detection in Chat** ✅
The chat interface now automatically:
- Detects when a report is mentioned in the agent's response
- Finds the actual file in the `./reports` directory
- Renders an interactive **Download Button** for immediate access

### 2. **Smart File Pattern Matching**
The system looks for filenames matching the pattern:
```
{name}_{YYYYMMDD}_{HHMMSS}.{ext}
```
Examples:
- `issues_by_type_20251030_101329.xlsx`
- `documents_with_issues_20251029_204433.csv`
- `sales_data_20251030_150000.png`

### 3. **Visual Download UI**
For each file detected, a nice download button appears with:
- 📊 emoji for Excel files
- 📄 emoji for CSV files  
- 🖼️ emoji for PNG images
- Correct MIME type for browser handling

### 4. **Optional: File Server (For External Access)**
If you want to serve files over HTTP for external access, a Flask-based file server is available:

**File:** `src/ui/file_server.py`

**Features:**
- Secure file download with path traversal protection
- Health check endpoint (`/health`)
- MIME type detection
- Runs on port 5000 by default

**To use:**
```python
from src.ui.file_server import ReportFileServer

server = ReportFileServer(reports_dir="./reports")
server.run(host="127.0.0.1", port=5000)
```

## Usage Flow

### Workflow: Generate Report via Chat

1. **User asks in chat:**
   ```
   "Gere um relatório de problemas de validação em CSV"
   ```

2. **Agent responds with:**
   ```
   Aqui está o relatório de problemas:
   
   Arquivo gerado: documents_with_issues_20251030_123456.csv
   Total de problemas: 42
   ...
   ```

3. **Streamlit UI automatically:**
   - ✅ Detects the filename
   - ✅ Finds the file on disk
   - ✅ Shows download button: `📄 Download documents_with_issues_20251030_123456.csv`

4. **User clicks button:**
   - File downloads directly to computer
   - Works immediately without HTTP server

## How to Test

### Test Case 1: Report Generation + Download
1. Open the Reports tab
2. Select "Documents with Validation Issues"
3. Choose CSV format
4. Click "Generate Report"
5. ✅ File appears with download button

### Test Case 2: Chat-Generated Report
1. In Home tab, chat ask: `"Gere um relatório de erros de validação em CSV"`
2. ✅ Agent responds with filename
3. ✅ Download button appears automatically

## Files Modified

| File | Change |
|------|--------|
| `src/ui/app.py` | Added `extract_file_downloads()` function; Updated chat display to auto-detect and render download buttons |
| `src/ui/file_server.py` | NEW: Flask-based file server for HTTP downloads |
| `requirements.txt` | Added `flask>=3.0.0` |

## Architecture

```
User Chat
   ↓
Agent generates report & saves to ./reports/
   ↓
Agent returns response with filename
   ↓
Streamlit chat display:
   ├── Extract plotly charts → render with st.plotly_chart()
   ├── Extract file paths → find on disk
   ├── Display markdown text
   └── Render download buttons (st.download_button)
   ↓
User clicks download → File downloads
```

## Key Benefits

✅ **No External Server Required** - Uses Streamlit's built-in download mechanism  
✅ **Automatic Detection** - No manual button creation needed  
✅ **Clean UX** - Buttons appear right next to the message  
✅ **Correct MIME Types** - Browsers handle files correctly  
✅ **Instant Download** - No page redirects, immediate download  
✅ **Optional HTTP Server** - Can still serve files over HTTP if needed  

## Troubleshooting

### Download button doesn't appear
- Check that the file exists: `ls ./reports/`
- Verify filename matches pattern: `{name}_{YYYYMMDD}_{HHMMSS}.{ext}`
- Check browser console for errors (F12)

### File appears to download but is empty
- Verify file size: `ls -lh ./reports/{filename}`
- Try generating a new report

### Want to use HTTP server for external access
1. Update `src/ui/file_server.py` to use `0.0.0.0` instead of `127.0.0.1`
2. Run: `python3 -m src.ui.file_server` on port 5000
3. Access: `http://{server-ip}:5000/download/{filename}`

## Future Improvements

- [ ] Add file cleanup (delete old reports after X days)
- [ ] Add download analytics (track which reports are downloaded)
- [ ] Add sharing URLs (generate shareable download links)
- [ ] Add file preview (show file contents before download)
- [ ] Add batch download (zip multiple reports)
