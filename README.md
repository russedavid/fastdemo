# Frontline - Maintenance Report Generator

A lightweight FastHTML application that transforms unstructured frontline inputs (voice notes, text, images) into structured maintenance and inspection reports using AI.

## Features

### Current Functionality ✅
- **Workspace System**: Create and manage multiple workspaces for different projects
- **Multi-Modal Input**: Drag-and-drop interface for audio (.webm/.mp3/.wav), text files, and images
- **Live Audio Recording**: Record audio directly in the browser with WebM format
- **AI-Powered Transcription**: Real-time audio transcription using OpenAI Whisper API
- **Interactive Transcription Editing**: 
  - Click-to-edit transcription previews with modal interface
  - 500ms debounced auto-save for seamless editing
  - Real-time updates across all views
- **Unified Input Item Display**: Consistent presentation across workspace and all-inputs views
- **Report Generation**: AI-powered maintenance report creation from processed inputs
- **User Authentication**: Secure session-based authentication system

### Technical Architecture

- **Backend**: FastHTML (Python) with reactive components and HTMX integration
- **Database**: SQLite with FastLite ORM for rapid prototyping
- **Frontend**: HTMX for dynamic interactions, Hyperscript for client-side logic
- **AI Integration**: OpenAI Whisper API and GPT-3.5-turbo via httpx
- **File Storage**: Organized local storage with audio/image/text separation
- **State Management**: Window object pattern for persistent client-side state

## Getting Started

### Prerequisites
- Python 3.8+
- OpenAI API key

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```

4. Run the application:
   ```bash
   python main.py
   ```

5. Open your browser to `http://localhost:5001`

### First Steps
1. Register a new account or login
2. Create a new workspace or select an existing one
3. Upload files via drag-and-drop or record audio directly
4. For audio files, click "Transcribe Audio" to generate transcriptions
5. Edit transcriptions by clicking on the preview text
6. Click "Generate Report" to create an AI-powered maintenance report
7. View and manage all your input items in the "View All Inputs" section

## Key Routes

### Content Routes (HTMX Fragments)
- `GET /content/workspace` - Create new workspace  
- `GET /content/workspace/{id}` - Load existing workspace
- `GET /content/workspaces` - View all workspaces
- `GET /content/inputs` - View all input items
- `GET /content/view-input/{id}` - Individual input item view
- `GET /content/reports` - View all reports
- `GET /content/dashboard` - Analytics dashboard

### API Routes
- `POST /upload` - Handle file uploads with workspace context
- `POST /transcribe-audio/{id}` - Transcribe audio files
- `PUT /update-transcription/{id}` - Update transcription with debounced saves
- `DELETE /delete-input/{id}` - Delete input items
- `POST /generate-report` - Generate AI report from workspace items

### Modal Routes
- `GET /modal/edit-transcription/{id}` - Transcription editing modal
- `GET /modal/add-input/{workspace_id}` - Add existing items to workspace modal
- `GET /modal/close` - Close modal

## Database Schema

### Users
- `id`, `username`, `email`, `password_hash`, `created_at`, `active`

### Workspaces  
- `id`, `user_id`, `name`, `created_at`, `updated_at`, `status`, `input_item_ids` (JSON array)

### Input Items
- `id`, `user_id`, `filename`, `original_filename`, `file_path`, `file_type`, `mime_type`, `file_size`, `transcription`, `extracted_data`, `processed`

### Maintenance Reports
- `id`, `workspace_id`, `user_id`, `title`, `description`, `equipment_id`, `part_numbers`, `defect_codes`, `corrective_action`, `priority`, `status`

## Architecture Highlights

### Key Patterns Implemented
- **Unified Fragment Pattern**: Single `build_input_item_fragment()` function ensures consistent display across all views
- **Out-of-Band Updates**: Real-time UI updates across multiple views using `hx_swap_oob="true"`
- **Modal System**: Centralized modal container with backdrop click-to-close functionality
- **Debounced Updates**: 500ms delay auto-save for smooth transcription editing
- **Window Object State**: Client-side state persistence across HTMX navigation

### Technology Choices
- **FastHTML**: Rapid development with Python-native reactive components
- **HTMX**: Dynamic interactions without complex JavaScript frameworks
- **Hyperscript**: Declarative client-side logic for UI interactions
- **SQLite + FastLite**: Simple, file-based database with ORM integration
- **OpenAI APIs**: Industry-standard Whisper and GPT integration
- **WebM Audio**: Modern format with good browser support and Whisper compatibility

### Deferred for Production
- Advanced error handling and logging
- Input validation and sanitization
- Rate limiting and API quotas
- Advanced UI/UX polish
- Mobile-responsive design optimization
- Unit and integration tests
- Production deployment configuration
- Advanced photo annotation tools
- Real-time notifications

## Future Enhancements
- Photo annotation with bounding boxes
- Advanced analytics and trend analysis
- Export functionality (PDF, CSV)
- Integration with maintenance management systems
- Mobile app development
- Advanced AI prompt engineering
- Multi-language support

## Security Considerations
- Password hashing with SHA-256
- Session-based authentication
- Input sanitization for file uploads
- Secure file storage with unique filenames
- Environment variable configuration for API keys

---

Built with ❤️ using FastHTML in under 20 hours.