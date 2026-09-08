class User:
    id: int
    username: str
    email: str
    password_hash: str
    created_at: str
    active: bool = True
    demo_expires_at: str = ""

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
    text_origin: str = "user"

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
    created_at: str
    updated_at: str
    priority: str = "medium"  # low, medium, high, critical
    status: str = "open"  # open, in_progress, completed, closed
    finalized: bool = False
    evidence_json: str = ""
    sources_json: str = ""
    model_id: str = ""
    generation_usage: str = ""
    review_notes: str = ""

class Generation:
    id: str
    user_id: int
    workspace_id: str
    created_at: str
    updated_at: str
    status: str = "queued"
    report_id: str = ""
    error: str = ""
    sources_json: str = ""

class ReportAnnotation:
    id: str  # UUID
    report_id: str
    input_item_id: str
    annotation_type: str  # bounding_box, pin, note
    coordinates: str  # JSON string for x,y or bbox coords
    note: str
    created_at: str
