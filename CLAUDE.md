# FastHTML Maintenance Report Application - Development Guide

## Project Overview
This is a maintenance report application built with FastHTML that allows users to create workspaces, upload audio/image/text files, transcribe audio, and generate AI-powered maintenance reports.

## Technology Stack

### Core Framework
- **FastHTML**: Modern Python web framework with reactive components
- **FastLite**: SQLite ORM integration with FastHTML
- **HTMX**: For dynamic content loading and interactions
- **Hyperscript**: For client-side interactions and event handling

### APIs & Services
- **OpenAI Whisper API**: Audio transcription
- **OpenAI GPT-3.5-turbo**: Entity extraction and report generation

### File Handling
- **aiofiles**: Async file operations
- **Pathlib**: File path management
- **Audio formats**: WebM (primary), MP3, WAV supported

## Architecture Patterns

### Component Structure
- **Unified Fragment Pattern**: All input items use `build_input_item_fragment(item, workspace_id=None)` for consistent display across contexts
- **Modal System**: Centralized modal container with backdrop click-to-close
- **Out-of-Band Updates**: Use `hx_swap_oob="true"` for real-time updates across views

### Data Flow
1. **Upload** → **Storage** → **Database** → **UI Update via OOB swap**
2. **Transcription** → **Modal Edit** → **500ms Debounced Update** → **OOB Updates Across Views**
3. **Recording** → **WebM Blob** → **Upload** → **Transcription** → **UI Update**

### State Management
- **Window Object Pattern**: Global state stored on `window` object to persist across HTMX navigation
- **Workspace Context**: Each workspace has isolated state and items
- **Session-based Auth**: Simple session authentication with user context

## File Organization

### Core Files
- `main.py`: Main application with all routes and components
- `models.py`: Data models (User, Workspace, InputItem, MaintenanceReport, etc.)
- `ai_services.py`: OpenAI API integrations
- `utils.py`: Helper functions (UUID generation, timestamps, password hashing)
- `css.py`: Application styles

### Directory Structure
```
/uploads/
  /audio/    - Audio file storage
  /images/   - Image file storage  
  /text/     - Text file storage
/data/
  generator.db - SQLite database
```

## Key Patterns & Best Practices

### 1. Unified Component Generation
**Problem**: Duplicate HTML generation for input items across different views
**Solution**: Single `build_input_item_fragment()` function that generates consistent Article elements

```python
def build_input_item_fragment(item, workspace_id=None):
    """Build a unified input item fragment for any context"""
    # Returns Article with:
    # - File info (name, type, size, date)
    # - Transcription (preview + edit OR transcribe button)  
    # - Actions (View, Delete with workspace context)
```

### 2. Out-of-Band Updates Pattern
**Use Case**: Update multiple views when data changes
**Implementation**: Use `hx_swap_oob="true"` to update elements by ID across the page

```python
# Update both workspace and all-inputs views
workspace_article = build_input_item_fragment(item, workspace.id)
workspace_article.attrs["hx_swap_oob"] = "true"
all_inputs_article = build_input_item_fragment(item)  
all_inputs_article.attrs["hx_swap_oob"] = "true"
return [workspace_article, all_inputs_article]
```

### 3. Modal System Pattern
**Structure**: Central modal container with backdrop functionality
```python
Div(id="modal-container")  # Always present in views that need modals

# Modal content with backdrop close
Div(
    # Modal content here
    style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000;",
    _="on click if event.target == me then trigger click on the first button in #modal-container end"
)
```

### 4. Debounced Updates Pattern
**Use Case**: Auto-save text changes without overwhelming the server
**Implementation**: 500ms delay with HTMX

```python
Textarea(
    value,
    hx_put=f"/update-route/{id}",
    hx_target="this", 
    hx_swap="none",
    hx_trigger="keyup changed delay:500ms",
    name="field_name"
)
```

### 5. Audio Recording Pattern
**State Management**: Use window object for persistence across navigation
```javascript
window.mediaRecorder = window.mediaRecorder || null;
window.audioChunks = window.audioChunks || [];
window.recordingWorkspaceId = window.workspaceId; // Lock to workspace at recording start
```

**Navigation Handling**: Discard recordings when navigating away
```javascript
document.addEventListener('htmx:beforeSwap', (evt) => {
    if (window.mediaRecorder && window.mediaRecorder.state === 'recording') {
        window.discarding = true;
        window.mediaRecorder.stop();
    }
});
```

## Route Patterns

### Content Routes
- `/content/{view_name}` - Return HTML fragments for main content area
- `/content/{view_name}/{id}` - Return HTML fragments with entity context

### API Routes  
- `POST /upload` - File upload with workspace context
- `PUT /update-{entity}/{id}` - Update entity fields
- `DELETE /delete-{entity}/{id}` - Delete entities
- `POST /transcribe-audio/{id}` - Transcribe audio files

### Modal Routes
- `/modal/{modal_name}/{id}` - Return modal content
- `/modal/close` - Close modal (return empty content)

## Testing Commands
```bash
# Run the application
python main.py

# Check file permissions
ls -la uploads/

# Database inspection  
sqlite3 data/frontline.db ".tables"
```

## Development Workflow

### Adding New Views
1. Create route handler in `main.py`
2. Use existing component patterns (`build_input_item_fragment`, modal system)
3. Add navigation links in sidebar
4. Test HTMX interactions and OOB updates

### Adding New Entity Types
1. Define model in `models.py`
2. Create table in database initialization
3. Add CRUD routes following existing patterns
4. Create unified fragment builder if needed for display

### Debugging HTMX Issues
- Use browser dev tools Network tab to see HTMX requests
- Check `hx-target` and `hx-swap` attributes
- Verify `hx_swap_oob` elements have correct IDs
- Test navigation between views to ensure state consistency