# 📥 Chart Export Feature - Quick Reference

## How to Export Charts

### Via Chat (Easiest)

Simply ask the agent in Portuguese:

```
"Exportar o gráfico em CSV"
"Exportar em XML"
"Baixar gráfico como HTML"
"Salvar gráfico como PNG"
```

Or in English:

```
"Export chart to CSV"
"Export to XML"
"Export as HTML"
"Save as PNG"
```

### What Happens Next

1. **Agent generates chart** in your chosen format
2. **Download button appears** below the response
3. **Click to download** the file to your computer
4. **Done!** File ready to use

---

## 📊 Supported Formats

### 1. **CSV** (Comma-Separated Values)

- **Best for**: Spreadsheets, Excel, analysis
- **File size**: ~100 KB typical
- **Data**: Chart data in table format
- **Usage**: Import into Excel, Google Sheets, etc.

### 2. **XML** (Structured Data)

- **Best for**: Data interchange, integration
- **File size**: ~300 KB typical
- **Data**: Chart data + metadata
- **Usage**: Processing by other systems

### 3. **HTML** (Interactive)

- **Best for**: Reports, presentations, web sharing
- **File size**: ~4 MB typical
- **Data**: Fully interactive Plotly chart
- **Features**:
  - Hover to see values
  - Zoom and pan
  - Toggle series on/off
  - Download screenshot
  - Works offline in any browser

### 4. **PNG** (Image)

- **Best for**: Print, social media, presentations
- **File size**: ~1 MB typical
- **Data**: Static image
- **Resolution**: High quality
- **Note**: Requires `kaleido` (usually pre-installed)

---

## 💡 Tips & Tricks

### For CSV Exports

```
📋 Column headers included automatically
✅ UTF-8 encoding (handles special characters)
🔢 All numeric data preserved
✨ Ready to import into any spreadsheet
```

### For XML Exports

```
📦 Structured with title, series, data points
✅ Standard XML format
🔗 Can be parsed by other tools
📝 Includes metadata
```

### For HTML Exports

```
🎨 Beautiful interactive charts
✅ No dependencies needed (offline compatible)
🖱️ Full Plotly interactivity
💾 Self-contained single file
🌐 Open in any modern browser
```

### For PNG Exports

```
📸 High-resolution image
✅ Universal format
🖨️ Print-friendly
📧 Easy to email/share
⚠️ Static snapshot (not interactive)
```

---

## ❓ FAQ

**Q: How large can the exported files be?**
A: Typically:

- CSV: 50-500 KB
- XML: 100-1 MB
- HTML: 2-8 MB (interactive, includes full Plotly library)
- PNG: 500 KB - 2 MB

**Q: Can I export multiple charts at once?**
A: Yes! Ask the agent:

```
"Exportar todos os gráficos em CSV"
"Enviar 3 gráficos em HTML"
```

You'll get multiple download buttons.

**Q: What if the download button doesn't appear?**
A:

- Wait a moment (processing can take a few seconds)
- Refresh the page
- Try a simpler request
- Check your browser console for errors

**Q: Can I use the exported file on Streamlit Cloud?**
A: Yes! All exports work both locally and on Streamlit Cloud. No files are stored on the server - everything happens in your browser.

**Q: Is there a file size limit?**
A: Very large charts (>100 MB) might fail. For huge datasets, consider:

- Filtering data first
- Exporting by date range
- Using CSV instead of HTML

**Q: What encoding are CSV/XML files in?**
A: UTF-8 (UTF-8-sig for CSV) - supports all languages and special characters.

**Q: Can I schedule exports to email?**
A: Not yet, but you can:

1. Export the file
2. Open in your email
3. Attach and send

**Q: Do exported files get saved on the server?**
A: No! Everything happens in your browser. No data is stored after you download.

---

## 🔧 Troubleshooting

### Download button doesn't appear

✅ Solutions:

- Wait 2-3 seconds (export can be slow)
- Refresh the page
- Try export again
- Check browser console (F12)

### File is corrupted/won't open

✅ Solutions:

- Re-download the file
- Check file format (open with correct app)
- Try a different format
- Report the issue

### Export takes too long

✅ Solutions (by format):

- **CSV**: Usually fast (<1s)
- **XML**: Usually fast (<1s)
- **HTML**: Can take 5-10s (includes full Plotly)
- **PNG**: Can take 10-30s (requires image rendering)

### PNG export fails

✅ Solution:

- Install kaleido: `pip install kaleido`
- Or use HTML format instead

---

## 📱 Using on Different Devices

### Desktop Browser ✅

- All formats work
- Recommended for large files
- Best experience

### Mobile Browser ⚠️

- CSV/XML work great
- HTML works but may be slow
- PNG works but takes longer
- Consider WiFi for large files

### Streamlit Cloud ✅

- All formats work
- No file size restrictions
- Download directly to your device
- No server storage

---

## 🎯 Use Cases

### Marketing Report

```
1. Generate sales chart
2. Ask: "Exportar gráfico como PNG"
3. Download and add to presentation
```

### Data Analysis

```
1. Generate data chart
2. Ask: "Exportar em CSV"
3. Download and analyze in Excel
```

### Client Report

```
1. Generate multiple charts
2. Ask: "Exportar gráficos em HTML"
3. Download and email to client
```

### Integration

```
1. Generate chart
2. Ask: "Exportar em XML"
3. Download and feed to other system
```

---

## 📞 Support

If you encounter issues:

1. **Check this guide** - Most common questions answered
2. **Try another format** - Different format might work better
3. **Clear browser cache** - Sometimes helps
4. **Report the issue** - Include:
   - What format you tried
   - What went wrong
   - Browser/device info

---

## 🔐 Privacy & Security

### Your Data is Safe ✅

- No files stored on servers
- Downloads go directly to your device
- No tracking or analytics
- No cookies or personal data collected

### Files are Temporary ✅

- Deleted immediately after download
- Not accessible to other users
- Not backed up or archived
- Completely private

---

## 📚 Examples

### Example 1: Export Sales Chart as CSV

```
User: "Quero exportar o gráfico de vendas em CSV"
Agent: ✅ **Gráfico Exportado para CSV**
       📊 **Arquivo:** `sales_chart_20251030_115747.csv`
       📋 **Linhas:** 12
       [📥 Download Button]
User: [Clicks download]
File: Opens in Excel automatically
```

### Example 2: Export Monthly Report as HTML

```
User: "Exportar relatório mensal em HTML"
Agent: ✅ **Gráfico Exportado para HTML**
       📊 **Arquivo:** `monthly_report_20251030_115747.html`
       📁 **Formato:** HTML interativo
       [📥 Download Button]
User: [Clicks download, opens in browser]
Browser: Shows interactive chart with zoom, hover, etc.
```

### Example 3: Export Taxes Data as XML

```
User: "Dados de impostos em XML por favor"
Agent: ✅ **Gráfico Exportado para XML**
       📊 **Arquivo:** `taxes_data_20251030_115747.xml`
       📈 **Séries:** 3
       [📥 Download Button]
User: [Clicks download]
File: Ready for processing by accounting software
```

---

## ✨ Pro Tips

1. **HTML exports are best for sharing** - Open in any browser, fully interactive
2. **CSV exports are fastest** - Great for quick analysis
3. **Export with meaningful names** - Agent includes timestamp automatically
4. **Keep downloads organized** - Create folders by date/type
5. **XML is for integration** - Feed into other systems or databases

---

**Need help?** Ask the agent directly in your language:

- Portuguese 🇧🇷: "Como fazer download do gráfico?"
- English 🇺🇸: "How do I export the chart?"
- Spanish 🇪🇸: "¿Cómo exporto el gráfico?"
