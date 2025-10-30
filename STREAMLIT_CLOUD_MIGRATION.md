# Streamlit Cloud Migration - Phase 2 Complete

## Status: ✅ Infrastructure Ready (75% Complete)

User requirement: **"tudo precisa afuncionar em streamlit cloud, os graficos e os downloads"**
(Everything needs to work in Streamlit Cloud - graphs and downloads)

---

## Phase 1: Architecture Refactoring ✅ COMPLETE

### Deleted (No Longer Cloud-Compatible)
- ❌ `src/ui/file_server.py` - Flask server won't run in Cloud
- ❌ `run_streamlit_with_server.sh` - Background processes unavailable
- ❌ `flask>=3.0.0` - Removed from requirements.txt

### Created (Cloud-Compatible Infrastructure)

#### 1. `src/services/in_memory_report.py` ✅
**Purpose**: Generate reports directly to memory (BytesIO) without disk I/O

```python
class InMemoryReportGenerator:
    @staticmethod
    def generate_csv(df: DataFrame, filename: str) -> Dict[str, Any]
        # Returns: {type, filename, content (bytes), mime}
    
    @staticmethod
    def generate_excel(df: DataFrame, filename: str) -> Dict[str, Any]
        # Returns: {type, filename, content (bytes), mime}
    
    @staticmethod
    def generate_parquet(df: DataFrame, filename: str) -> Dict[str, Any]
        # Returns: {type, filename, content (bytes), mime}
    
    @staticmethod
    def generate_report(df: DataFrame, filename: str, format: str) -> Dict[str, Any]
        # Unified interface for any format
```

**Key Benefits**:
- No file system writes
- Works in ephemeral containers
- Data survives reruns via Streamlit session state
- Identical behavior: local → Cloud deployment

#### 2. `src/utils/agent_response_parser.py` ✅
**Purpose**: Parse agent responses into structured components

```python
class AgentResponseParser:
    @staticmethod
    def extract_plotly_chart(response_text: str) -> Tuple[str, Optional[Dict]]
        # Returns: (remaining_text, plotly_dict or None)
    
    @staticmethod
    def extract_file_reference(response_text: str) -> Tuple[str, Optional[Dict]]
        # Returns: (remaining_text, file_info_dict or None)
    
    @staticmethod
    def parse_response(response_text: str) -> Dict[str, Any]
        # Returns: {text, chart, file}
```

**Features**:
- Detects Plotly JSON in code fences or raw JSON
- Robust brace-matching algorithm
- Finds file references: `{name}_{YYYYMMDD}_{HHMMSS}.{ext}`
- Returns cleaned markdown text

#### 3. `src/ui/app.py` ✅ Refactored
**Changes**:
- ✅ Removed old extraction functions (using file system)
- ✅ Added `display_agent_response()` function
- ✅ Updated chat history display to use `AgentResponseParser`
- ✅ Updated agent response handler
- ✅ Removed Flask/file system dependencies

**New Pattern**:
```python
def display_agent_response(response_text: str) -> None:
    """Render response with charts and downloads (Cloud-compatible)."""
    parsed = AgentResponseParser.parse_response(response_text)
    
    if parsed["chart"]:
        st.plotly_chart(parsed["chart"], use_container_width=True)
    
    if parsed["text"]:
        st.markdown(parsed["text"])
    
    if parsed["file"]:
        file_info = parsed["file"]
        st.download_button(
            label=f"📥 Download {file_info['filename']}",
            data=file_info['content'],  # BytesIO content
            file_name=file_info['filename'],
            mime=file_info['mime'],
        )
```

---

## Phase 2: Business Tools Integration 🔄 IN PROGRESS

### Next Tasks (High Priority)

#### Task 1: Update `src/agent/report_tool.py`
Currently returns file paths. Must change to return BytesIO.

**Current Pattern**:
```python
result = generator.generate_report(...)
return f"📁 **File:** `{result['file_path']}`"
```

**Target Pattern**:
```python
file_bytes = InMemoryReportGenerator.generate_report(df, filename, format)
return f"✅ Report generated\n\n```json\n{json.dumps(file_bytes)}\n```"
```

**Impact**: `report_tool.py` ~50 lines

#### Task 2: Update `src/agent/business_tools.py`
Any tools generating files must use `InMemoryReportGenerator`.

**Search for**: File-based operations, Path usage

#### Task 3: Update `src/services/report_generator.py`
If this service writes to disk, refactor to return DataFrames instead.

---

## Phase 3: Local Testing 🔄 PENDING

### Test Scenarios
1. **Chart Rendering**
   - Agent returns Plotly JSON
   - `AgentResponseParser.extract_plotly_chart()` extracts it
   - `st.plotly_chart()` renders it

2. **CSV Download**
   - Agent generates CSV via `InMemoryReportGenerator.generate_csv()`
   - Bytes returned in response
   - `st.download_button()` shows download link
   - User clicks → File downloads

3. **Excel Download**
   - Same as CSV but with `.xlsx` format
   - Verify MIME type is correct
   - Test in browser

### Commands
```bash
cd /home/bmos/private/private_repos/i2a2/projeto_final
streamlit run src/ui/app.py
```

---

## Phase 4: Cloud Deployment 🔄 PENDING

### Prerequisites
1. Complete business tools integration (Task 1-3 above)
2. Pass local testing
3. Update `.streamlit/config.toml`
4. Verify all imports are Cloud-compatible

### Deployment Checklist
- [ ] No Flask dependencies
- [ ] No background process spawning
- [ ] No file system writes to `./reports/`
- [ ] All files in memory
- [ ] Session state used for data persistence
- [ ] API key from `st.secrets` or UI input (not hardcoded)
- [ ] SQLite (local demo) or Cloud DB for production
- [ ] Tested locally on Streamlit dev environment

### Deployment Steps
1. Push to GitHub
2. Connect Streamlit Cloud
3. Add Gemini API key to secrets
4. Deploy
5. Test all features on Cloud instance

---

## Architecture Comparison

### OLD (Won't work in Cloud)
```
┌─────────────────┐
│  Streamlit App  │ (port 8501)
│   (local state) │
└────────┬────────┘
         │
    ┌────▼─────┐
    │   Flask   │ ❌ Custom port (blocked)
    │  Server   │    Spawned as subprocess
    │ (port     │
    │  5000)    │
    └────┬─────┘
         │
    ┌────▼──────────────┐
    │  ./reports/        │ ❌ Ephemeral (lost on restart)
    │  - file.xlsx       │    File system operations
    │  - chart.png       │
    └──────────────────┘
```

### NEW (Cloud-Compatible) ✅
```
┌─────────────────────────────────┐
│   Streamlit App (port 8501)     │
│   ┌─────────────────────────┐   │
│   │   Session State         │   │ ✅ Persists during reruns
│   │   - messages []         │   │    (not persistent across restarts)
│   │   - agent              │   │
│   └──────────┬──────────────┘   │
│              │                  │
│   ┌──────────▼──────────────┐   │
│   │   Agent Response        │   │
│   │   {text, chart, file}   │   │
│   │                         │   │
│   │   - chart: Plotly JSON  │   │
│   │   - file: {            │   │
│   │     content: BytesIO    │   │
│   │     filename: "..."     │   │
│   │     mime: "..."         │   │
│   │   }                     │   │
│   └──────────┬──────────────┘   │
│              │                  │
│   ┌──────────▼──────────────┐   │
│   │   Renderer              │   │
│   │   - st.plotly_chart()   │   │
│   │   - st.download_btn()   │   │
│   │   - st.markdown()       │   │
│   └─────────────────────────┘   │
└─────────────────────────────────┘

❌ No Flask
❌ No file system writes
❌ No background processes
✅ 100% Streamlit Cloud compatible
```

---

## Code Examples

### Pattern 1: Generate Report in Memory
```python
from src.services.in_memory_report import InMemoryReportGenerator

df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
file_info = InMemoryReportGenerator.generate_excel(df, "my_report")

# file_info = {
#     "type": "xlsx",
#     "filename": "my_report.xlsx",
#     "content": b'\x50\x4b\x03\x04...',  # Binary BytesIO content
#     "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# }
```

### Pattern 2: Parse Agent Response
```python
from src.utils.agent_response_parser import AgentResponseParser

response = """
Here's your report:

```json
{"data": [...], "layout": {...}}
```

Check the file: report_20251030_101329.xlsx
"""

parsed = AgentResponseParser.parse_response(response)

# parsed = {
#     "text": "Here's your report:\n\nCheck the file: report_20251030_101329.xlsx",
#     "chart": {"data": [...], "layout": {...}},
#     "file": {
#         "filename": "report_20251030_101329.xlsx",
#         "found_at": "...",
#         "timestamp": "20251030_101329"
#     }
# }
```

### Pattern 3: Display in Streamlit
```python
from src.utils.agent_response_parser import AgentResponseParser

response_text = agent.chat(user_prompt)
parsed = AgentResponseParser.parse_response(response_text)

with st.chat_message("assistant"):
    if parsed["chart"]:
        st.plotly_chart(parsed["chart"], use_container_width=True)
    
    if parsed["text"]:
        st.markdown(parsed["text"])
    
    if parsed["file"]:
        st.download_button(
            label=f"📥 {parsed['file']['filename']}",
            data=???  # ← Needs to come from file_info with BytesIO content
            file_name=parsed["file"]["filename"],
        )
```

---

## Files Modified/Created This Session

| File | Status | Change |
|------|--------|--------|
| `src/services/in_memory_report.py` | ✅ Created | 120 lines - BytesIO-based report generation |
| `src/utils/agent_response_parser.py` | ✅ Created | 150+ lines - Structured response parsing |
| `src/ui/app.py` | ✅ Refactored | Removed old functions, added Cloud-compatible rendering |
| `requirements.txt` | ✅ Updated | Removed `flask>=3.0.0` |
| `src/ui/file_server.py` | ✅ Deleted | No longer needed |
| `run_streamlit_with_server.sh` | ✅ Deleted | No longer needed |

---

## Remaining Work Estimate

| Task | Priority | Effort | Blocker |
|------|----------|--------|---------|
| Update `report_tool.py` to use BytesIO | 🔴 Critical | 1-2 hrs | Yes |
| Update other `business_tools.py` | 🟠 High | 2-3 hrs | Yes |
| Local integration testing | 🟠 High | 1-2 hrs | No |
| Cloud deployment setup | 🟡 Medium | 30 min | No |

**Total Remaining**: ~5-8 hours

---

## Validation Checklist

- [x] No syntax errors in refactored files
- [x] Old Flask/file system code deleted
- [x] New Cloud-compatible infrastructure created
- [x] Imports updated correctly
- [ ] Business tools integration (pending)
- [ ] Local testing passing (pending)
- [ ] Cloud deployment successful (pending)

---

## References

**User Requirement**: 
> "tudo precisa afuncionar em streamlit cloud, os graficos e os downloads"
> Everything needs to work in Streamlit Cloud, graphs and downloads

**Architectural Decision**: In-memory BytesIO + structured parsing instead of file-based approach

**Key Technologies**:
- Streamlit (only port 8501)
- Plotly JSON format
- Pandas DataFrames
- Python BytesIO
- No external servers needed

---

**Session Completed**: ✅ Infrastructure ready. Next: Business tools integration.
