# Responsive Layout Validation Checklist
## CalendarView.vue - Subtask Validation
**Date**: February 8, 2026  
**Component**: `frontend/src/views/CalendarView.vue`  
**Related**: `frontend/src/components/Sidebar.vue`

---

## Test Environment
- ✅ Backend: http://localhost:8000/tours (5 tours available)
- ✅ Frontend: http://localhost:5173/calendar
- Browser: Edge/Chrome DevTools
- Test Device Emulation: Responsive mode + specific devices

---

## 📱 Mobile Layout (<768px) - Tests

### Viewport & Overflow
- [ ] **No horizontal scrollbar** at 375px width (iPhone SE)
- [ ] **No horizontal scrollbar** at 320px width (small phone)
- [ ] Root container uses `overflow-x-hidden`
- [ ] All content fits within viewport width

### Navigation (Sidebar/Drawer)
- [ ] **Hamburger menu button** visible in top-left corner
- [ ] Hamburger button has proper spacing (left-4 top-4)
- [ ] Hamburger accessible with `aria-label="Open menu"`
- [ ] **Click hamburger → drawer slides in** from left
- [ ] **Backdrop appears** behind drawer (bg-black/50)
- [ ] **Click backdrop → drawer closes**
- [ ] **Click close (X) button → drawer closes**
- [ ] Drawer covers full height
- [ ] Drawer z-index correct (above content, below controls)

### Content Layout
- [ ] Main content has **extra top padding** (pt-14) for hamburger space
- [ ] Responsive padding: `px-4 py-6` on mobile
- [ ] Calendar title readable at `text-xl`
- [ ] Date headings readable at `text-base`
- [ ] Tour cards use `flex-col` (stacked vertically)
- [ ] Card padding: `p-3`
- [ ] Spacing between list items: `space-y-3`

### Typography
- [ ] Title: `text-xl` (readable, not too large)
- [ ] Date headings: `text-base`
- [ ] Tour names: font-semibold, no overflow
- [ ] Guide names: text-sm, no overflow
- [ ] Time/ID: text-sm, right-aligned on desktop but inline on mobile
- [ ] Loading/error messages: `text-sm`

### Text Overflow Protection
- [ ] Long tour names **truncate with ellipsis**
- [ ] Hover on truncated tour name shows **full text** (title attribute)
- [ ] Long guide names truncate correctly
- [ ] Long error messages wrap (`wrap-break-word`)
- [ ] No text extends beyond card boundaries

### Interactions
- [ ] Touch targets ≥44px (buttons, nav items)
- [ ] Tap hamburger menu works smoothly
- [ ] Tap drawer backdrop closes drawer
- [ ] Navigate to another page → drawer closes automatically
- [ ] No broken tap zones or overlapping elements

---

## 💻 Desktop Layout (≥768px) - Tests

### Navigation (Sidebar)
- [ ] **Sidebar always visible** (not a drawer)
- [ ] Sidebar has fixed width (w-80)
- [ ] **Hamburger menu button hidden** (`md:hidden`)
- [ ] **No backdrop shown**
- [ ] Sidebar uses gradient background
- [ ] Logo displays correctly in sidebar

### Content Layout
- [ ] Main content has comfortable left margin (sidebar space)
- [ ] Main content padding: `sm:px-6 sm:py-10 md:pt-10`
- [ ] No extra top padding for hamburger (pt-14 removed on md+)
- [ ] Max-width constraint: `max-w-4xl mx-auto`
- [ ] Proper spacing between sidebar and content

### Typography
- [ ] Title: `sm:text-2xl` (larger, more prominent)
- [ ] Date headings: `sm:text-lg`
- [ ] Tour cards: text remains readable
- [ ] Loading/error: `sm:text-base`

### Tour Cards
- [ ] Cards use `sm:flex-row` (horizontal layout)
- [ ] Tour info on left, time/ID on right
- [ ] `sm:justify-between` creates proper spacing
- [ ] Card padding: `sm:p-4` (more spacious)
- [ ] Time/ID block uses `shrink-0` (doesn't compress)
- [ ] Text alignment: time/ID `sm:text-right`

### Visual Balance
- [ ] No excessive white space
- [ ] Comfortable reading width (max-w-4xl)
- [ ] Proper visual hierarchy (title → dates → tours)
- [ ] Consistent spacing throughout

---

## 🔄 Responsive Transitions - Tests

### Breakpoint Changes (768px)
- [ ] **Resize from 767px → 768px**: hamburger disappears, sidebar appears
- [ ] **Resize from 768px → 767px**: sidebar disappears, hamburger appears
- [ ] Open drawer at 767px, resize to 768px → no visual glitches
- [ ] Smooth transition animations (no jumps or flashes)
- [ ] Text scales smoothly (no sudden jumps)
- [ ] Card layout transitions cleanly (col → row)

### Viewport Resize
- [ ] Start at 320px, slowly increase to 1920px → all transitions smooth
- [ ] No layout breaks at intermediate sizes (600px, 900px, 1200px)
- [ ] Content reflows correctly at all widths
- [ ] No content clipping during resize

### State Persistence
- [ ] Open drawer, navigate to Settings, back to Calendar → drawer closed
- [ ] Scroll position maintained during viewport resize
- [ ] Tour data remains visible through all breakpoints

---

## 📊 Specific Device Tests

### iPhone SE (375x667)
- [ ] All content visible
- [ ] Hamburger tappable
- [ ] Drawer opens fully
- [ ] No horizontal scroll
- [ ] Text readable
- [ ] Tour cards fit within width

### iPhone 12 Pro (390x844)
- [ ] Layout consistent with iPhone SE
- [ ] Extra vertical space used well
- [ ] No wasted space

### iPad Mini (768x1024)
- [ ] **Sidebar switches to fixed** at this breakpoint
- [ ] Comfortable layout with sidebar visible
- [ ] Tour cards in row layout
- [ ] Good use of wider screen

### Desktop (1920x1080)
- [ ] Content centered with max-w-4xl
- [ ] Sidebar on left, content centered
- [ ] No excessive stretching
- [ ] Proper negative space

---

## 🎯 Accessibility Tests

### Keyboard Navigation
- [ ] Tab through all interactive elements
- [ ] Hamburger menu keyboard accessible
- [ ] Drawer close button keyboard accessible
- [ ] Focus indicators visible
- [ ] Logical tab order

### Screen Reader
- [ ] Hamburger has `aria-label="Open menu"`
- [ ] Close button has `aria-label="Close menu"`
- [ ] Backdrop has `aria-hidden="true"`
- [ ] Semantic HTML structure (nav, main, aside)

### Touch/Pointer
- [ ] Touch targets ≥44px on mobile
- [ ] No hover-only interactions on touch devices
- [ ] Tap/click feedback visible

---

## 🐛 Edge Cases

### Content Variations
- [ ] **Empty state**: "No tours found" displays correctly on all sizes
- [ ] **Loading state**: "Loading tours..." centered and visible
- [ ] **Error state**: Long error message wraps, doesn't overflow
- [ ] **Many tours**: Scrolling works, layout doesn't break
- [ ] **Single tour**: Layout looks balanced
- [ ] **Very long tour name**: Truncates with ellipsis, shows full on hover

### Extreme Viewports
- [ ] 320px width (smallest mobile)
- [ ] 1920px width (full HD desktop)
- [ ] Short height (landscape phone): scrolling works
- [ ] Very tall viewport: footer/bottom spacing correct

### Browser Zoom
- [ ] 50% zoom: layout scales down, readable
- [ ] 100% zoom: default, perfect
- [ ] 150% zoom: layout scales up, no overflow
- [ ] 200% zoom: usable, responsive design adapts

---

## 📝 Implementation Verification

### CalendarView.vue Styles
```vue
✅ Root: flex min-h-screen bg-gray-50 overflow-x-hidden
✅ Main: flex-1 min-w-0 px-4 py-6 pt-14 sm:pt-10 sm:px-6 sm:py-10 md:pt-10
✅ Title: text-xl sm:text-2xl
✅ Date heading: text-base sm:text-lg
✅ Card: p-3 sm:p-4
✅ List item: flex-col gap-1 sm:flex-row sm:justify-between sm:items-start
✅ Tour name: truncate with title attribute
✅ Time/ID: shrink-0 sm:text-right
✅ Error: wrap-break-word
```

### Sidebar.vue Styles
```vue
✅ Hamburger: fixed left-4 top-4 z-30 md:hidden
✅ Backdrop: fixed inset-0 z-40 bg-black/50 md:hidden
✅ Sidebar: fixed md:static w-80 z-50 -translate-x-full md:translate-x-0
✅ Open state: translate-x-0 when mobileOpen
✅ Close button: absolute right-3 top-3 md:hidden
✅ Route watcher: closes drawer on navigation
```

---

## ✅ Success Criteria

All checkboxes must be checked for validation to pass:

1. **Zero horizontal overflow** at all viewport widths
2. **Hamburger menu works** on mobile (<768px)
3. **Sidebar always visible** on desktop (≥768px)
4. **Text truncation** prevents overflow
5. **Smooth transitions** between breakpoints
6. **Touch targets** meet accessibility standards (≥44px)
7. **Responsive typography** scales appropriately
8. **Card layout** adapts (col → row)
9. **No visual glitches** during resize
10. **Content readable** at all zoom levels

---

## 🎬 Manual Test Procedure

1. **Open DevTools** (F12) → Toggle device toolbar
2. **Set to 375px width** (iPhone SE)
3. **Check hamburger menu**: visible, functional
4. **Open drawer**: slides in smoothly
5. **Check content**: no horizontal scroll, text readable
6. **Close drawer**: backdrop works, X button works
7. **Navigate**: drawer closes automatically
8. **Resize to 768px**: sidebar appears, hamburger disappears
9. **Check desktop layout**: cards horizontal, proper spacing
10. **Test intermediate sizes**: 600px, 900px, 1200px
11. **Test extreme sizes**: 320px, 1920px
12. **Check zoom levels**: 50%, 100%, 150%, 200%
13. **Test landscape orientation**
14. **Test keyboard navigation**
15. **Verify truncation**: long tour names show ellipsis

---

## 📸 Screenshots Needed

- [ ] Mobile (375px): drawer closed
- [ ] Mobile (375px): drawer open
- [ ] Mobile (375px): tour cards
- [ ] Tablet (768px): transition point
- [ ] Desktop (1920px): full layout
- [ ] Extreme narrow (320px)
- [ ] Tour name truncation example
- [ ] Error message wrapping

---

## Results Summary

**Status**: 🔄 IN PROGRESS

### Passed Tests: 0 / TBD
### Failed Tests: 0
### Blockers: None

---

**Next Steps**: Execute manual tests and check all boxes above.
