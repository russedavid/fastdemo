class User:
    id: int
    username: str
    email: str
    password_hash: str
    created_at: str
    active: bool = True

class Workspace:
    id: str  # UUID
    user_id: int
    name: str
    created_at: str
    updated_at: str
    status: str = "draft"  # draft, processing, completed
    input_item_ids: str = "[]"  # JSON array of input item IDs

class InputItem:
    id: str  # UUID
    user_id: int
    filename: str
    original_filename: str
    file_path: str
    file_type: str  # audio, image, text
    mime_type: str
    file_size: int
    uploaded_at: str
    processed: bool = False
    transcription: str = ""
    extracted_data: str = ""  # JSON string

class MaintenanceReport:
    id: str  # UUID
    workspace_id: str
    user_id: int
    title: str
    description: str
    equipment_id: str
    part_numbers: str  # JSON array as string
    defect_codes: str  # JSON array as string  
    corrective_action: str
    parts_used: str  # JSON array as string
    next_service_date: str
    priority: str = "medium"  # low, medium, high, critical
    status: str = "open"  # open, in_progress, completed, closed
    created_at: str
    updated_at: str
    finalized: bool = False

class ReportAnnotation:
    id: str  # UUID
    report_id: str
    input_item_id: str
    annotation_type: str  # bounding_box, pin, note
    coordinates: str  # JSON string for x,y or bbox coords
    note: str
    created_at: str