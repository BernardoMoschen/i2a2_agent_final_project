# UI Layout - Fiscal Document Agent

**Design Philosophy:** Apple-inspired minimalism — clean, elegant, functional  
**Theme:** iOS blue (#007AFF) with subtle grays and near-black text  
**Last Updated:** October 28, 2025

---

## Tab Structure

### 🏠 Home

**Purpose:** Primary interaction point for users

**Components:**

- **Chat Interface** (main feature)

  - Natural language queries in Portuguese or English
  - Conversational history with agent
  - Direct access to all 16 agent tools
  - Real-time responses with formatted outputs

- **Quick Actions** (4 buttons below chat)
  - ⬆️ Upload XMLs → Navigate to Documents tab
  - 🔍 Search Documents → Navigate to Documents tab
  - 📊 View Statistics → Navigate to Statistics tab
  - 📈 Generate Report → Navigate to Reports tab

**User Flow:** Land on Home → Chat with agent → Quick actions guide to other tabs as needed

---

### 📄 Documents

**Purpose:** Upload, browse, search, and export fiscal documents

**Components:**

- **Upload Section** (collapsed by default)

  - Async file upload (single/batch/zip)
  - Background processing with job monitoring
  - Progress tracking

- **Documents Explorer**
  - Server-side pagination
  - Advanced filters (type, operation, date range, CNPJ)
  - Export to CSV/Parquet/gzip
  - View document details
  - Full-text search (FTS5)

**User Flow:** Upload XMLs → Browse/search → Filter → Export

---

### 📈 Reports

**Purpose:** Generate analytical reports and exports

**Components:**

- **Report Categories:**

  - Validation Reports (issues, approved docs, by severity)
  - Financial Reports (taxes, values, suppliers, costs)
  - Operational Reports (volume, document types, operations)
  - Classification Reports (cache effectiveness, unclassified)
  - Product Reports (NCM, CFOP, items with issues)

- **Filters:**

  - Date range (all time, last 7/30/90 days, custom)
  - Document type (NFe, NFCe, CTe, MDFe)
  - Operation type (purchase, sale, transfer, return)
  - Severity (error, warning, info)
  - Issuer CNPJ

- **Output Options:**
  - Excel (.xlsx) or CSV
  - Optional visualization charts
  - Download ready files

**User Flow:** Select report type → Apply filters → Generate → Download

---

### 📊 Statistics

**Purpose:** High-level overview and system health metrics

**Components:**

- **Overview Metrics** (4 key stats)

  - 📄 Total Documents
  - 🛒 Total Items
  - ⚠️ Validation Issues
  - 💵 Total Value Processed

- **Documents by Type Chart**

  - Bar chart showing NFe, NFCe, CTe, MDFe distribution
  - Interactive visualization

- **Classification Cache Stats**
  - 🗄️ Cache Entries
  - 🎯 Cache Hits
  - 📈 Effectiveness (%)
  - 💰 Estimated Savings ($)
  - Success message or prompt to process docs

**User Flow:** Quick glance at system health → Dive into specific metrics

---

## Design Tokens

### Colors

```css
Primary:    #007AFF  /* iOS blue - buttons, links, accents */
Background: #FFFFFF  /* Pure white */
Secondary:  #F5F5F7  /* Subtle gray for cards/sections */
Text:       #1D1D1F  /* Near-black for readability */
Muted:      #6e6e73  /* Gray for captions/labels */
Divider:    #e5e5e7  /* Very light gray for separators */
```

### Typography

- **Font:** System sans-serif (matches OS)
- **Headings:** Bold, near-black (#1D1D1F)
- **Body:** Regular, near-black
- **Captions:** Small, muted gray (#6e6e73)

### Components

- **Buttons:** Rounded (10px), padding 0.5rem 1rem
- **Dividers:** Subtle 1px solid #e5e5e7
- **Metrics:** Clean labels with emphasized values
- **Cards:** Minimal borders, subtle backgrounds

---

## Navigation Patterns

### Primary Path (Chat-First)

```
User lands → Home (Chat) → Ask questions → Get answers
```

### Secondary Paths

```
Home → Quick Actions → Navigate to specialized tab
Statistics → Overview → Dive into Reports/Documents for details
Documents → Upload → Search → Export
Reports → Configure → Generate → Download
```

### Cross-Tab References

- Quick Actions link to other tabs explicitly
- Chat can recommend "Go to Reports tab for detailed analytics"
- Statistics provides context before detailed operations

---

## Accessibility

- Clear hierarchy (h1, h2, h3, h4)
- Descriptive button labels
- Helper text for complex operations
- Status indicators (success, warning, error)
- Loading states ("🤔 Pensando...")
- Empty states with guidance

---

## Mobile Considerations

- Sidebar collapses on small screens
- Tabs stack vertically
- Metrics flow to single column
- Chat input remains accessible
- Buttons use full width on mobile

---

## Best Practices

1. **Minimize Clicks:** Primary action (chat) is immediately visible
2. **Progressive Disclosure:** Advanced features (upload, filters) are collapsed by default
3. **Clear Feedback:** Every action has visual confirmation
4. **Guided Navigation:** Quick actions and helper text guide users
5. **Consistency:** Same design tokens across all tabs
6. **Performance:** Lazy loading, pagination, async processing

---

## Future Enhancements (Optional)

- [ ] Keyboard shortcuts for power users
- [ ] Saved searches/filters in Documents
- [ ] Custom dashboard in Home (user-configurable widgets)
- [ ] Dark mode toggle
- [ ] Export templates for Reports
- [ ] Batch operations from Documents tab
