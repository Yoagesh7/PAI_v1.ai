# 🎨 Block Editor: Drag & Drop + Resize Features - Visual Guide

## 1️⃣ Block Structure with New Elements

```
┌─────────────────────────────────────────────────┐
│ ⋮⋮ ✕  Block Content Here...       [👁️] [💾]   │ ◄── Topbar (unchanged)
└─────────────────────────────────────────────────┘
        │   │
        │   └─ Delete Button
        └───── Drag Handle (⋮⋮)

┌─────────────────────────────────────────────────────┐
│ ⋮⋮ ✕  Lorem ipsum dolor sit amet.               ▔▔│
│      consectetur adipiscing elit.                 ▐█│ ◄── Resize Handle
│      sed do eiusmod tempor incididunt ut...       ▐█│     (Bottom-Right)
│                                                   ▔▔│
└─────────────────────────────────────────────────────┘
  ▲                                                    ▲
  └────── Min width: 200px                ────────────┘
                                          Min height: 80px
```

---

## 2️⃣ Dragging Blocks (Reordering)

### Step 1: Grab the Drag Handle
```
Block 1  ⋮⋮ ✕  First block...
         ↓ (user clicks & holds ⋮⋮)
         
Block 2  ⋮⋮ ✕  Second block...

Block 3  ⋮⋮ ✕  Third block...
```

### Step 2: Drag Over Another Block
```
Block 1 (dragging - semi-transparent)
         ┌─ First block... ─┐
         │ opacity: 0.6     │
         │ dashed border    │
         └──────────────────┘
         
Block 2 (drag-over - hover indicator)
         ┌───────────────────┬── Top border highlight (3px solid accent)
         │ Second block...  │ Padding shows drop zone
         └──────────────────┘
         
Block 3
         ⋮⋮ ✕  Third block...
```

### Step 3: Release to Swap
```
After drop:
Block 1  ⋮⋮ ✕  Second block...     ◄── Swapped! (was Block 2)
Block 2  ⋮⋮ ✕  First block...      ◄── Swapped! (was Block 1)
Block 3  ⋮⋮ ✕  Third block...
```

---

## 3️⃣ Resizing Blocks

### Before Hover (Default)
```
┌──────────────────────────────────┐
│ ⋮⋮ ✕  Block content...          │
│      Lorem ipsum dolor...         │
│      Sed do eiusmod...           │
│                                  │  ◄── Resize handle invisible
└──────────────────────────────────┘
```

### On Hover (Handle Appears)
```
┌──────────────────────────────────┐
│ ⋮⋮ ✕  Block content...          │
│      Lorem ipsum dolor...         │
│      Sed do eiusmod...           │
│                                ▔▔│  ◄── Resize handle visible (opacity: 0.5)
└──────────────────────────────────┘
                                   ▐█
```

### During Resize (Visual Feedback)
```
┌─────────────────────────────────────────┐
│ ⋮⋮ ✕  Block content...                 │
│      Lorem ipsum dolor sit amet          │
│      consectetur adipiscing elit...      │
│      Sed do eiusmod tempor incididunt... │
│                                       ▔▔▔│  ◄── Resize handle bright (opacity: 1)
└─────────────────────────────────────────┘  ◄── Box-shadow: glow effect
 ▐███████████████████████████████████████  ◄── New width/height
 ▐█
 ▐█ (Accent border shows resizing state)
```

### After Release (Changes Saved)
```
┌─────────────────────────────────────────┐
│ ⋮⋮ ✕  Block content...                 │
│      Lorem ipsum dolor sit amet          │  ◄── New size persisted
│      consectetur adipiscing elit...      │
│      Sed do eiusmod tempor incididunt... │
│                                          │
└─────────────────────────────────────────┘
(Automatically saved to block data)
```

---

## 4️⃣ CSS Classes Applied During Interactions

### Drag & Drop States
| State | CSS Class | Visual Effect |
|-------|-----------|---------------|
| Normal | `.ed-block` | Default style |
| Being Dragged | `.ed-block.dragging` | Opacity 0.6, dashed border, lighter bg |
| Over Drop Zone | `.ed-block.drag-over` | Top border highlight, padding |
| Drag Ended | N/A (class removed) | Back to default |

### Resize States
| State | CSS Class | Visual Effect |
|-------|-----------|---------------|
| Normal Hover | `.ed-block:hover .ed-block-resize` | Handle opacity 0.5 |
| Resize Handle Hover | `.ed-block-resize:hover` | Handle opacity 1.0 |
| Resizing | `.ed-block.resizing` | Box-shadow glow, accent border |
| Resize Complete | N/A (class removed) | Back to default |

---

## 5️⃣ Event Flow Diagram

### Dragging Blocks
```
User clicks ⋮⋮ on Block A
    ↓
dragstart event fires
    ↓
onBlockDragStart(e, indexA)
    ├─ draggedBlockIndex = indexA
    ├─ .dragging class added
    └─ dataTransfer.effectAllowed = 'move'
    ↓
User drags mouse over Block B
    ↓
dragover event fires on Block B
    ├─ onBlockDragOver(e)
    ├─ .drag-over class added
    └─ dropEffect = 'move'
    ↓
User releases mouse
    ↓
drop event fires on Block B
    ├─ onBlockDrop(e, indexB)
    ├─ Swap: blocks[indexA] ↔ blocks[indexB]
    ├─ renderBlocks() called
    └─ markUnsaved() called
    ↓
dragend event fires
    ├─ onBlockDragEnd(e)
    ├─ All classes removed
    └─ draggedBlockIndex = null
```

### Resizing Blocks
```
User mousedown on .ed-block-resize handle
    ↓
startBlockResize(e, blockElement, index)
    ├─ isResizing = true
    ├─ Capture startX, startY, startWidth, startHeight
    ├─ .resizing class added
    └─ Register mousemove + mouseup listeners
    ↓
User moves mouse (resize)
    ↓
mousemove event fires repeatedly
    ├─ doBlockResize(e)
    ├─ Calculate deltaX = e.clientX - startX
    ├─ Calculate deltaY = e.clientY - startY
    ├─ newWidth = max(200, startWidth + deltaX)
    ├─ newHeight = max(80, startHeight + deltaY)
    └─ Apply to blockElement.style
    ↓
User releases mouse
    ↓
mouseup event fires
    ├─ stopBlockResize()
    ├─ Save: blocks[index].width = width
    ├─ Save: blocks[index].minHeight = minHeight
    ├─ markUnsaved() called
    ├─ .resizing class removed
    └─ Remove event listeners
```

---

## 6️⃣ Color & Visual Scheme

### Drag & Drop Colors
- **Dragging Block**: 
  - Border: `2px dashed rgba(139, 120, 204, 0.5)` (purple accent, dashed)
  - Background: `rgba(139, 120, 204, 0.1)` (light purple tint)
  - Opacity: `0.6` (dimmed)

- **Drop Zone**: 
  - Border-top: `3px solid var(--ed-accent)` (solid purple)
  - Padding-top: `8px` (visual spacer)

### Resize Colors
- **Resize Handle (Idle)**:
  - Background: `linear-gradient(135deg, transparent 50%, var(--ed-accent) 50%)` (corner triangle)
  - Opacity: `0` (invisible by default)
  - Cursor: `nwse-resize` (diagonal arrows)

- **Resize Handle (Hover)**:
  - Opacity: `0.5` (semi-visible)

- **Resize Handle (Active Hover)**:
  - Opacity: `1` (fully visible)

- **Resizing Block**:
  - Box-shadow: `0 8px 32px rgba(139, 120, 204, 0.25)` (glow effect)
  - Border-color: `var(--ed-accent)` (accent colored border)

---

## 7️⃣ Size Constraints

### Minimum Sizes
```javascript
Minimum Width:  200px  // Prevents unreadably narrow blocks
Minimum Height:  80px  // Prevents collapsed blocks
```

### No Maximum
- Users can resize to very large sizes
- Vertical scrolling allowed
- Content wraps naturally

---

## 8️⃣ Keyboard & Accessibility Notes

### Current Support
- ✅ Drag using mouse
- ✅ Resize using mouse
- ✅ Keyboard shortcuts: Delete key (⋮⋮ → Delete Block)
- ❌ Keyboard-only drag/resize (future enhancement)
- ❌ Touch events for mobile (future enhancement)

---

## 9️⃣ Data Persistence

### Block Data Structure
```javascript
block = {
  id: 123,
  type: 'text',
  content: '...',
  width: '350px',        // NEW: Set by resize
  minHeight: '150px'     // NEW: Set by resize
}
```

### Persistence Flow
```
User resizes block
    ↓
doBlockResize() updates DOM
    ↓
User releases mouse
    ↓
stopBlockResize() saves to blocks array:
    ├─ blocks[index].width = "350px"
    └─ blocks[index].minHeight = "150px"
    ↓
markUnsaved() triggers
    ↓
Auto-save timer fires (existing mechanism)
    ↓
saveBlock() sends to backend:
    └─ POST /workspace/{id}/save
       └─ Includes width & minHeight in JSON
    ↓
On page reload:
    ├─ Fetch block from server
    ├─ renderBlocks() applies saved dimensions
    └─ Block renders at saved size
```

---

## 🔟 Common User Scenarios

### Scenario 1: Organizing Multiple Blocks
```
1. User opens editor with 5 blocks in wrong order
2. User drags Block 4 over Block 1 and drops
3. Blocks swap: positions 1↔4
4. User continues dragging to final order
5. Order auto-saves
6. Page reload: Order persists ✓
```

### Scenario 2: Making Room for Content
```
1. Block with code snippet is too narrow
2. User hovers bottom-right, sees resize handle
3. User drags handle down-right: 200px → 500px width
4. Code snippet now readable on single lines
5. Size auto-saves
6. Page reload: Width persists as 500px ✓
```

### Scenario 3: Creating Layout
```
1. Multiple tall blocks crammed together
2. User resizes blocks to different heights
3. Creates visual hierarchy:
   - Summary block: 120px
   - Details block: 300px
   - Code block: 500px
4. Layout auto-saves
5. Next session: Custom layout loads ✓
```

---

## 📊 Browser Compatibility

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| Drag & Drop API | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| Mouse Events | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| CSS Calc/Variables | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| Touch Events | ⚠️ Limited | ❌ No | ⚠️ Limited | ⚠️ Limited |

---

## 🎓 Developer Notes

### For Extending Functionality

1. **Add Animation**:
   ```css
   .ed-block {
     transition: all 0.3s ease;
   }
   ```

2. **Add Keyboard Support**:
   ```javascript
   document.addEventListener('keydown', (e) => {
     if (e.key === 'ArrowUp' && selectedBlockIndex > 0) {
       // Swap with block above
       [blocks[selectedBlockIndex], blocks[selectedBlockIndex - 1]] = 
       [blocks[selectedBlockIndex - 1], blocks[selectedBlockIndex]];
     }
   });
   ```

3. **Add Grid Snapping**:
   ```javascript
   const GRID_SIZE = 10;
   newWidth = Math.round(newWidth / GRID_SIZE) * GRID_SIZE;
   ```

4. **Add Max Size Constraints**:
   ```javascript
   const MAX_WIDTH = 1200;
   const MAX_HEIGHT = 2000;
   const newWidth = Math.min(1200, Math.max(200, startWidth + deltaX));
   ```

---

## ✨ Summary

✅ **Drag & Drop**: Reorder blocks intuitively
✅ **Resize**: Adjust block dimensions (min 200px × 80px)
✅ **Visual Feedback**: Clear indicators during interactions
✅ **Auto-Save**: Changes persist automatically
✅ **Notion-Like**: Familiar interaction pattern
✅ **Accessible**: Easy to discover (handles visible on hover)

Ready for production! 🚀
