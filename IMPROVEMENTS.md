# Suggested Improvements for AMC Problem Shop

Given: 10 users, school internal use, teaching aid (doesn't need to be overly robust)

## High Priority - Quick Wins

### 1. **Search Functionality** ⭐⭐⭐
- **Why**: Teachers often remember "that geometry problem from 2020" but don't remember the exact number
- **Implementation**: Add a search box that filters by:
  - Problem number (e.g., "17")
  - Year (e.g., "2020")
  - Category keywords
  - Test type (e.g., "AMC10A")
- **Effort**: Low (client-side filtering)
- **Impact**: High - saves time browsing

### 2. **Worksheet Reordering** ⭐⭐⭐
- **Why**: Teachers want to control problem order in worksheets
- **Implementation**: Drag-and-drop or up/down arrows for problems in worksheet
- **Effort**: Medium (add sortable.js or similar lightweight library)
- **Impact**: High - essential for creating logical problem sequences

### 3. **Multiple Worksheets / Save Worksheets** ⭐⭐
- **Why**: Teachers create different worksheets for different classes/units
- **Implementation**: 
  - Save worksheet with name/description
  - Load saved worksheets
  - Store in localStorage or simple JSON file
- **Effort**: Low-Medium
- **Impact**: High - prevents re-creating same worksheets

### 4. **Quick Filters / Presets** ⭐⭐
- **Why**: Common filter combinations (e.g., "AMC10 2020-2024", "Geometry problems")
- **Implementation**: Buttons for common filter combinations
- **Effort**: Low
- **Impact**: Medium-High - faster workflow

### 5. **Problem Preview Thumbnails** ⭐⭐
- **Why**: Faster scanning without clicking each problem
- **Implementation**: Show small thumbnail on hover or in list
- **Effort**: Medium (image optimization needed)
- **Impact**: Medium - improves browsing speed

## Medium Priority - Teaching-Specific Features

### 6. **Worksheet Notes/Description** ⭐
- **Why**: Add context like "Unit 3 Review" or "Midterm Practice"
- **Implementation**: Text area in worksheet info section
- **Effort**: Low
- **Impact**: Medium - helps organize worksheets

### 7. **Bulk Operations** ⭐
- **Why**: Add multiple problems at once (e.g., all problems 1-10 from a test)
- **Implementation**: Checkboxes or "Add all filtered" button
- **Effort**: Low-Medium
- **Impact**: Medium - saves clicks

### 8. **Export Options Enhancement** ⭐
- **Why**: More control over PDF output
- **Implementation**:
  - Include answer key option
  - Page numbers
  - Custom header/footer (e.g., "Name: ___________")
  - Problem numbering restart option
- **Effort**: Medium
- **Impact**: Medium - better print quality

### 9. **Problem Statistics** ⭐
- **Why**: Track which problems are used most (helps identify favorites)
- **Implementation**: Simple counter in localStorage
- **Effort**: Low
- **Impact**: Low-Medium - nice to have

### 10. **Keyboard Shortcuts** ⭐
- **Why**: Faster workflow for power users
- **Implementation**: 
  - `+` to add current problem
  - `-` to remove
  - Arrow keys to navigate list
- **Effort**: Low
- **Impact**: Medium - speeds up workflow

## Lower Priority - Nice to Have

### 11. **Problem Difficulty Tags**
- **Why**: Help select appropriate problems for different skill levels
- **Implementation**: Add difficulty field to labels (Easy/Medium/Hard)
- **Effort**: Medium (requires labeling or manual input)
- **Impact**: Low-Medium

### 12. **Favorites/Bookmarks**
- **Why**: Mark frequently used problems
- **Implementation**: Star icon, store in localStorage
- **Effort**: Low
- **Impact**: Low-Medium

### 13. **Recent Problems History**
- **Why**: Quick access to recently viewed problems
- **Implementation**: Store last 10-20 viewed problems
- **Effort**: Low
- **Impact**: Low

### 14. **Dark Mode Toggle**
- **Why**: Eye comfort during long sessions
- **Implementation**: CSS toggle, store preference
- **Effort**: Low-Medium
- **Impact**: Low

### 15. **Problem Sets / Collections**
- **Why**: Pre-made problem sets by topic (e.g., "All Geometry Problems")
- **Implementation**: Saved filter combinations or manual collections
- **Effort**: Medium
- **Impact**: Medium (if teachers create/share sets)

## Technical Improvements (Low User Impact, Better Maintainability)

### 16. **Error Handling & User Feedback**
- Better error messages
- Loading indicators
- Success confirmations

### 17. **Performance Optimization**
- Lazy load images
- Virtual scrolling for long lists
- Debounce filter inputs

### 18. **Mobile Responsiveness**
- **Why**: Teachers might want to browse on tablets
- **Effort**: Medium
- **Impact**: Low (desktop-focused use case)

## Recommended Implementation Order

**Phase 1 (Immediate Value)**:
1. Search functionality
2. Worksheet reordering
3. Save/load worksheets

**Phase 2 (Enhanced Workflow)**:
4. Quick filters/presets
5. Bulk operations
6. Export enhancements

**Phase 3 (Polish)**:
7. Keyboard shortcuts
8. Problem preview thumbnails
9. Worksheet notes

## Notes

- **Keep it simple**: For 10 users, avoid over-engineering
- **Focus on workflow**: What slows teachers down?
- **Iterate based on feedback**: Ask users what they actually need
- **Maintainability**: Choose simple solutions over complex ones
- **No need for**: User roles, advanced permissions, analytics dashboards, etc.

