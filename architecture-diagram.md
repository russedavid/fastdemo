# FastHTML Maintenance Report Application - Architecture Diagram

## System Architecture

```mermaid
graph TB
    subgraph ClientLayer["Client Layer"]
        Browser[Web Browser]
        HTMX[HTMX/Hyperscript]
    end
    
    subgraph FastHTMLApp["FastHTML Application"]
        Routes["Route Handlers<br/>main.py"]
        
        subgraph Components["Components"]
            Dashboard[Dashboard Components]
            Workspaces[Workspace Views]
            Reports[Report Views]
            Modals[Modal System]
        end
        
        subgraph Services["Services"]
            AI["AI Services<br/>ai_services.py"]
            Utils["Utilities<br/>utils.py"]
            CSS["Styles<br/>css.py"]
        end
        
        subgraph DataLayer["Data Layer"]
            Models["Data Models<br/>models.py"]
            FastLite[FastLite ORM]
        end
    end
    
    subgraph ExternalServices["External Services"]
        OpenAI[OpenAI API]
        Whisper["Whisper API<br/>Audio Transcription"]
        GPT["GPT-3.5-turbo<br/>Text Generation"]
    end
    
    subgraph Storage["Storage"]
        SQLite[("SQLite DB<br/>data/frontline.db")]
        FileSystem["File System<br/>uploads/"]
        
        subgraph UploadDirs["Upload Dirs"]
            Audio[audio/]
            Images[images/]
            Text[text/]
        end
    end
    
    Browser -->|HTTP/WebSockets| Routes
    HTMX -->|AJAX| Routes
    
    Routes --> Dashboard
    Routes --> Workspaces
    Routes --> Reports
    Routes --> Modals
    
    Dashboard --> Models
    Workspaces --> Models
    Reports --> Models
    
    Models --> FastLite
    FastLite --> SQLite
    
    Routes --> AI
    AI --> OpenAI
    OpenAI --> Whisper
    OpenAI --> GPT
    
    Routes --> Utils
    Routes --> CSS
    
    Routes --> FileSystem
    FileSystem --> Audio
    FileSystem --> Images
    FileSystem --> Text
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant Browser
    participant FastHTML
    participant AI_Service
    participant Database
    participant FileSystem
    
    User->>Browser: Upload File
    Browser->>FastHTML: POST /upload
    FastHTML->>FileSystem: Save File
    FastHTML->>Database: Create InputItem
    
    alt Audio File
        FastHTML->>AI_Service: Transcribe Audio
        AI_Service->>FastHTML: Return Transcription
        FastHTML->>Database: Update InputItem
    end
    
    FastHTML->>Browser: Return Updated UI (OOB Swap)
    
    User->>Browser: Generate Report
    Browser->>FastHTML: POST /generate-report
    FastHTML->>Database: Get Workspace Items
    FastHTML->>AI_Service: Generate Report (GPT-3.5)
    AI_Service->>FastHTML: Return Report
    FastHTML->>Database: Save Report
    FastHTML->>Browser: Display Report
```

## Component Interaction Pattern

```mermaid
graph LR
    subgraph UIPattern["UI Update Pattern"]
        Action[User Action]
        Route[Route Handler]
        Fragment[build_input_item_fragment]
        OOB[OOB Swap Updates]
        Multi[Multiple Views Updated]
    end
    
    Action --> Route
    Route --> Fragment
    Fragment --> OOB
    OOB --> Multi
```

## Database Schema

```mermaid
erDiagram
    User ||--o{ Workspace : creates
    User ||--o{ InputItem : uploads
    User ||--o{ MaintenanceReport : generates
    Workspace ||--o{ InputItem : contains
    Workspace ||--o{ MaintenanceReport : generates
    MaintenanceReport ||--o{ ReportAnnotation : has
    
    User {
        int id PK
        string username
        string email
        string password_hash
        datetime created_at
    }
    
    Workspace {
        int id PK
        int user_id FK
        string name
        string description
        datetime created_at
    }
    
    InputItem {
        int id PK
        int user_id FK
        int workspace_id FK
        string file_type
        string file_path
        string original_filename
        string transcription
        float file_size
        datetime uploaded_at
    }
    
    MaintenanceReport {
        int id PK
        int user_id FK
        int workspace_id FK
        string title
        text content
        string status
        string priority
        datetime created_at
    }
    
    ReportAnnotation {
        int id PK
        int report_id FK
        string annotation_type
        text content
        datetime created_at
    }
```

## Key Architectural Patterns

1. **Unified Fragment Pattern**: Single source of truth for UI components
2. **Out-of-Band (OOB) Updates**: Real-time updates across multiple views
3. **Modal System**: Centralized modal container with backdrop functionality
4. **Debounced Updates**: 500ms delay for auto-save operations
5. **Window Object State**: Global state management for audio recording