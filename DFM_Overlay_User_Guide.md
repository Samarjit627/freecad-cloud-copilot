# Professional DFM Overlay/Tooltip System - User Guide

## Overview

The StandaloneCoPilot.FCMacro now includes a professional DFM (Design for Manufacturing) overlay and tooltip system that provides precise, interactive visualization of manufacturing issues directly in the FreeCAD 3D view.

## Key Features

### ✨ **Per-Issue Mesh Overlays**
- Each manufacturing issue gets its own colored mesh overlay
- Overlays are precisely aligned to the surface geometry
- Surface-projected triangles for accurate highlighting
- Severity-based color coding (Critical=Red, High=Orange, Medium=Yellow, Low=Blue)

### 🎯 **3D View Tooltips**
- **Hover**: Move mouse over any colored overlay to see issue details
- **Click**: Click on overlay to pin/unpin the tooltip
- **Pinned tooltips**: Stay visible until clicked again
- **Rich content**: Shows exact issue title and description from Manufacturing Issues section

### 🔄 **Transform Synchronization**
- Overlays automatically follow the base object when moved/rotated
- App::Part grouping ensures perfect transform inheritance
- Real-time synchronization with FreeCAD's document observer

### 🎨 **Professional Styling**
- Severity-based transparency (30-35%)
- Modern Qt-styled tooltips with dark theme
- Subtle visual cues for pinned tooltips
- Non-intrusive overlay appearance

## How to Use

### 1. **Load the Macro**
```python
# In FreeCAD Python console or macro editor
exec(open('/path/to/StandaloneCoPilot.FCMacro').read())
```

### 2. **Run DFM Analysis**
- Open or create a CAD object (mesh or solid)
- Use the macro's DFM analysis feature
- The system will automatically generate overlays for detected issues

### 3. **Interact with Overlays**
- **Hover** over any colored area to see the tooltip
- **Click** on an overlay to pin the tooltip in place
- **Click again** to unpin and hide the tooltip
- **Move/rotate** your object - overlays will follow automatically

### 4. **Toggle Overlays**
```python
# Hide all overlays for an object
dfm_toggle_overlays("YourObjectName", visible=False)

# Show overlays again
dfm_toggle_overlays("YourObjectName", visible=True)
```

## Technical Details

### **Supported Object Types**
- **Mesh::Feature** objects (STL, OBJ imports)
- **Part::Feature** objects (STEP, native FreeCAD solids)
- Automatic tessellation for solid objects

### **Issue Data Format**
The system expects issues in this format:
```python
issues = [
    {
        "position": [x, y, z],           # 3D coordinates
        "severity": "critical",          # critical/high/medium/low
        "title": "Thin Wall",           # Issue title
        "description": "Wall thickness 0.5mm < 1.0mm minimum",  # Details
        "tooltip": "Custom tooltip text"  # Optional override
    }
]
```

### **API Functions**

#### **Main Entry Point**
```python
dfm_draw_per_issue_overlays(obj_name, issues, radius_mm=3.0, clear=True, lin_def=0.1, ang_def=0.5)
```
- `obj_name`: FreeCAD object name
- `issues`: List of issue dictionaries
- `radius_mm`: Highlight radius around each issue (3.0mm default)
- `clear`: Clear existing overlays first
- `lin_def/ang_def`: Tessellation quality for solids

#### **Toggle Visibility**
```python
dfm_toggle_overlays(obj_name, visible=True)
```

#### **Manual Synchronization**
```python
sync_overlay_part_to_base(base_obj_name)
```

#### **Enable/Disable System**
```python
enable_auto_sync_and_tooltips()   # Enable hover tooltips and auto-sync
disable_auto_sync_and_tooltips()  # Disable system
```

## Color Coding

| Severity | Color | RGB | Use Case |
|----------|-------|-----|----------|
| **Critical** | Red | (1.0, 0.0, 0.0) | Structural failures, impossible to manufacture |
| **High** | Orange | (1.0, 0.302, 0.0) | Major issues, expensive to fix |
| **Medium** | Yellow | (1.0, 0.702, 0.0) | Moderate issues, may increase cost |
| **Low** | Blue | (0.0, 0.5, 1.0) | Minor optimizations, suggestions |

## Troubleshooting

### **Overlays Not Appearing**
- Check that the object exists: `FreeCAD.ActiveDocument.getObject("ObjectName")`
- Verify issues have valid 3D positions
- Ensure object is meshable (has geometry)

### **Tooltips Not Working**
- Make sure `enable_auto_sync_and_tooltips()` was called
- Check FreeCAD console for error messages
- Verify you're hovering over the actual overlay mesh

### **Transform Issues**
- Overlays should automatically follow base object
- If not syncing, call `sync_overlay_part_to_base("ObjectName")` manually
- Check that the base object hasn't been renamed

### **Performance**
- For complex meshes, increase `lin_def` (e.g., 0.2) for faster tessellation
- Reduce `radius_mm` for smaller highlight areas
- Use `clear=True` to remove old overlays before creating new ones

## Example Usage

```python
# Example: Create overlays for a part with manufacturing issues
issues = [
    {
        "position": [10.0, 5.0, 2.0],
        "severity": "critical",
        "title": "Thin Wall",
        "description": "Wall thickness 0.5mm is below minimum 1.0mm for injection molding"
    },
    {
        "position": [15.0, 8.0, 3.0],
        "severity": "medium",
        "title": "Sharp Corner",
        "description": "Internal corner radius 0.2mm should be ≥0.5mm to avoid stress concentration"
    }
]

# Apply overlays to object named "MyPart"
overlays = dfm_draw_per_issue_overlays("MyPart", issues)
print(f"Created {len(overlays)} overlay objects")

# Later: hide overlays
dfm_toggle_overlays("MyPart", visible=False)

# Show them again
dfm_toggle_overlays("MyPart", visible=True)
```

## Integration with Existing Workflow

The professional DFM overlay system is fully integrated with the existing StandaloneCoPilot.FCMacro workflow:

1. **Automatic Activation**: Overlays are created automatically during DFM analysis
2. **Manufacturing Issues Sync**: Tooltip content matches the Manufacturing Issues section
3. **Hybrid Analysis**: Works with both cloud and local DFM engines
4. **Object Management**: Proper cleanup when objects are deleted
5. **Document Integration**: Respects FreeCAD's document structure and naming

## Advanced Features

### **Custom Styling**
Modify `SEVERITY_STYLE` dictionary to customize colors and transparency:
```python
SEVERITY_STYLE["critical"]["color"] = (1.0, 0.0, 1.0)  # Magenta
SEVERITY_STYLE["critical"]["transparency"] = 50         # More transparent
```

### **Precision Control**
- Adjust `radius_mm` for issue highlight size
- Modify `lin_def`/`ang_def` for tessellation quality vs. performance
- Use `faces_within_radius()` for custom face selection logic

### **Event Handling**
The system uses FreeCAD's SoEvent callback for mouse interaction:
- `MOUSEMOVE`: Hover detection and tooltip display
- `BUTTONDOWN`: Click-to-pin functionality
- Automatic cleanup and error handling

---

**🎉 The professional DFM overlay/tooltip system provides an intuitive, precise, and user-friendly way to visualize and interact with manufacturing issues directly in the FreeCAD 3D environment!**
