from fasthtml.common import *
from fastlite import *
from pathlib import Path
import json
from datetime import datetime
import aiofiles
from ai_services import *
from models import *
from utils import *
from monsterui.all import *
from css import css

# Create necessary directories
upload_dir = Path("uploads")
upload_dir.mkdir(exist_ok=True)
(upload_dir / "audio").mkdir(exist_ok=True)
(upload_dir / "images").mkdir(exist_ok=True)
(upload_dir / "text").mkdir(exist_ok=True)
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

db = database("data/frontline.db")

users = db.create(User, pk="id", transform=True)
workspaces = db.create(Workspace, pk="id", transform=True)
input_items = db.create(InputItem, pk="id", transform=True)
maintenance_reports = db.create(MaintenanceReport, pk="id", transform=True)
report_annotations = db.create(ReportAnnotation, pk="id", transform=True)

# SPA Components
def create_recent_reports_section(user_id: int, swap_oob: bool = False):
    recent_reports = sorted(maintenance_reports(where=f"user_id = {user_id}"), key=lambda r: r.created_at, reverse=True)[:3]
    return Div(
        *(
            [
                Div(
                    Div(
                        (
                            report.title[:30] + "..."
                            if len(report.title) > 30
                            else report.title
                        ),
                        cls=TextT.medium,
                    ),
                    Div(
                        f"{report.priority} • {datetime.fromisoformat(report.created_at).strftime('%m/%d')}",
                        cls=TextPresets.muted_sm,
                    ),
                    hx_get=f"/content/view-report/{report.id}",
                    hx_target="#main-content",
                    cls="p-3 mb-2 rounded-md cursor-pointer transition-colors hover:bg-secondary border border-transparent",
                )
                for report in recent_reports
            ]
            if recent_reports
            else [
                P("No reports yet", cls=TextPresets.muted_sm)
            ]
        ),
        id="recent-reports",
        hx_swap_oob="true" if swap_oob else "false",
    )


def create_dashboard_stats_section(user_id: int, swap_oob: bool = False):
    user_reports = maintenance_reports(where=f"user_id = {user_id}")
    dashboard_stats =  {"total": len(user_reports), "open": len([r for r in user_reports if r.status == "open"]),
                        "critical": len([r for r in user_reports if r.priority == "critical"])}
    return Div(
        Div(f"Total Reports: {dashboard_stats['total']}", cls="mb-2"),
        Div(f"Open: {dashboard_stats['open']}", cls="mb-2"),
        Div(f"Critical: {dashboard_stats['critical']}", cls="mb-2"),
        hx_get="/content/dashboard",
        hx_target="#main-content",
        cls="p-3 mb-2 rounded-md cursor-pointer transition-colors hover:bg-secondary border border-transparent",
        id="dashboard-stats",
        hx_swap_oob="true" if swap_oob else "false",
    )


def create_recent_uploads_section(user_id: int, swap_oob: bool = False):
    """Create recent uploads section with optional swap-oob"""
    recent_uploads = sorted(input_items(where=f"user_id = {user_id}"), key=lambda i: i.uploaded_at, reverse=True)[:3]
    return Div(
        *(
            [
                Div(
                    Div(
                        (
                            upload.original_filename[:25] + "..."
                            if len(upload.original_filename) > 25
                            else upload.original_filename
                        ),
                        cls=TextT.medium,
                    ),
                    Div(
                        f"{upload.file_type.title()} • {datetime.fromisoformat(upload.uploaded_at).strftime('%m/%d')}",
                        cls=TextPresets.muted_sm,
                    ),
                    hx_get=f"/content/view-input/{upload.id}",
                    hx_target="#main-content",
                    cls="p-3 mb-2 rounded-md cursor-pointer transition-colors hover:bg-secondary border border-transparent",
                )
                for upload in recent_uploads
            ]
            if recent_uploads
            else [
                P("No uploads yet", cls=TextPresets.muted_sm)
            ]
        ),
        id="recent-uploads",
        hx_swap_oob="true" if swap_oob else "false",
    )


def create_recent_workspaces_section(user_id: int, swap_oob: bool = False):
    """Create recent workspaces section with optional swap-oob"""
    recent_workspaces = sorted(workspaces(where=f"user_id = {user_id}"), key=lambda w: w.updated_at, reverse=True)[:3]
    return Div(
        *(
            [
                Div(
                    Div(
                        (
                            workspace.name[:25] + "..."
                            if len(workspace.name) > 25
                            else workspace.name
                        ),
                        cls=TextT.medium,
                    ),
                    Div(
                        f"{workspace.status.title()} • {len(json.loads(workspace.input_item_ids or '[]'))} items",
                        cls=TextPresets.muted_sm,
                    ),
                    hx_get=f"/content/workspace/{workspace.id}",
                    hx_target="#main-content",
                    cls="p-3 mb-2 rounded-md cursor-pointer transition-colors hover:bg-secondary border border-transparent",
                )
                for workspace in recent_workspaces
            ]
            if recent_workspaces
            else [
                Div("No workspaces yet.", cls=TextPresets.muted_sm)
            ]
        ),
        id="recent-workspaces",
        hx_swap_oob="true" if swap_oob else "false",
    )


def build_input_item_fragment(item, workspace_id=None):
    """Build a unified input item fragment for any context"""
    
    # File type icon mapping
    file_icons = {
        "audio": "mic",
        "image": "image", 
        "text": "file-text"
    }
    icon = file_icons.get(item.file_type, "file")
    
    # Build content sections
    content_sections = []
    
    # Transcription/content section for audio and text files
    if item.file_type == "audio":
        if item.transcription:
            # Show preview of transcription (clickable to edit)
            preview = item.transcription[:80] + "..." if len(item.transcription) > 80 else item.transcription
            content_sections.append(
                Div(
                    Strong("Transcription", cls=TextT.medium),
                    P(f'"{preview}"',
                        hx_get=f"/modal/edit-transcription/{item.id}",
                        hx_target="#modal-container",
                        cls="cursor-pointer hover:text-primary mt-1",
                        title="Click to edit transcription"
                    ),
                    cls="mb-4"
                )
            )
        else:
            # Show transcribe button
            content_sections.append(
                Button(
                    UkIcon("mic", height=14, width=14, cls="mr-2"),
                    "Transcribe Audio",
                    hx_post=f"/transcribe-audio/{item.id}",
                    hx_target="closest article",
                    hx_swap="outerHTML",
                    cls=(ButtonT.primary, "mb-4")
                )
            )
    
    elif item.file_type == "text":
        if item.transcription:
            # Show preview of text content (clickable to edit)
            preview = item.transcription[:80] + "..." if len(item.transcription) > 80 else item.transcription
            content_sections.append(
                Div(
                    Strong("Content", cls=TextT.medium),
                    P(f'"{preview}"',
                        hx_get=f"/modal/edit-transcription/{item.id}",
                        hx_target="#modal-container",
                        cls="cursor-pointer hover:text-primary mt-1",
                        title="Click to edit text content"
                    ),
                    cls="mb-4"
                )
            )
        else:
            content_sections.append(
                P("No content available", cls=(TextPresets.muted_sm, "italic mb-4"))
            )
    
    # Image preview for image files
    elif item.file_type == "image":
        content_sections.append(
            Center(
                Img(
                    src=f"uploads/images/{Path(item.file_path).name}",
                    alt=f"Preview of {item.original_filename}",
                    cls="max-w-32 max-h-24 rounded object-cover shadow-sm"
                ),
                cls="mb-4"
            )
        )
    
    # Action buttons
    action_buttons = []
    
    # View button
    action_buttons.append(
        Button(
            UkIcon("eye", height=14, width=14, cls="mr-1"),
            "View",
            hx_get=f"/content/view-input/{item.id}",
            hx_target="#main-content",
            cls=(ButtonT.secondary, "text-xs")
        )
    )
    
    # Detect Entity button for image files
    if item.file_type == "image":
        action_buttons.append(
            Button(
                UkIcon("search", height=14, width=14, cls="mr-1"),
                "Detect",
                hx_get=f"/modal/detect-entity/{item.id}",
                hx_target="#modal-container",
                cls=(ButtonT.secondary, "text-xs")
            )
        )
    
    # Delete/Remove button with workspace context
    if workspace_id:
        # In workspace context: "Remove" button that only removes from workspace
        action_buttons.append(
            Button(
                UkIcon("x", height=14, width=14),
                hx_delete=f"/remove-from-workspace/{workspace_id}/{item.id}",
                hx_target=f"#input-article-{item.id}",
                hx_swap="outerHTML",
                hx_confirm="Remove this item from the workspace?",
                cls=(ButtonT.ghost, "text-destructive hover:text-destructive text-xs p-1"),
                title="Remove from workspace"
            )
        )
    else:
        # In all-items context: "Delete" button that permanently deletes
        action_buttons.append(
            Button(
                UkIcon("trash-2", height=14, width=14),
                hx_delete=f"/delete-input/{item.id}",
                hx_target=f"#input-article-{item.id}",
                hx_swap="outerHTML",
                hx_confirm="Are you sure you want to permanently delete this input item?",
                cls=(ButtonT.ghost, "text-destructive hover:text-destructive text-xs p-1"),
                title="Delete permanently"
            )
        )
    
    # Return unified Card format
    return Card(
        CardHeader(
            DivFullySpaced(
                DivLAligned(
                    UkIcon(icon, height=16, width=16, cls="mr-2 text-muted-foreground"),
                    Strong(item.original_filename, cls=TextT.medium)
                ),
                DivLAligned(
                    *action_buttons,
                    cls="space-x-1"
                )
            )
        ),
        CardBody(
            DivVStacked(
                DivLAligned(
                    Label(item.file_type.title(), cls=LabelT.primary),
                    Label(f"{(item.file_size / 1024):.1f} KB", cls=LabelT.secondary),
                    Small(datetime.fromisoformat(item.uploaded_at).strftime('%m/%d %H:%M'), cls=TextPresets.muted_sm),
                    cls="space-x-2 mb-3"
                ),
                *content_sections
            )
        ),
        cls=(CardT.default, "mb-4"),
        id=f"input-article-{item.id}"
    )


def create_sidebar(user):
    return Div(
        # Quick Actions
        Card(
            CardHeader(H4("Quick Actions")),
            CardBody(
                DivVStacked(
                    Button(
                        UkIcon("plus-circle", height=16, width=16, cls="mr-2"),
                        "Create New Report",
                        hx_get="/content/workspace",
                        hx_target="#main-content",
                        cls=(ButtonT.primary, "w-full justify-start")
                    ),
                    Button(
                        UkIcon("file-text", height=16, width=16, cls="mr-2"),
                        "View All Reports",
                        hx_get="/content/reports",
                        hx_target="#main-content",
                        cls=(ButtonT.secondary, "w-full justify-start")
                    ),
                    Button(
                        UkIcon("inbox", height=16, width=16, cls="mr-2"),
                        "View All Inputs",
                        hx_get="/content/inputs",
                        hx_target="#main-content",
                        cls=(ButtonT.secondary, "w-full justify-start")
                    ),
                    Button(
                        UkIcon("folder", height=16, width=16, cls="mr-2"),
                        "View All Workspaces",
                        hx_get="/content/workspaces",
                        hx_target="#main-content",
                        cls=(ButtonT.secondary, "w-full justify-start")
                    ),
                    Button(
                        UkIcon("bar-chart-3", height=16, width=16, cls="mr-2"),
                        "Dashboard",
                        hx_get="/content/dashboard",
                        hx_target="#main-content",
                        cls=(ButtonT.secondary, "w-full justify-start")
                    ),
                    cls="space-y-2"
                )
            ),
            cls=(CardT.default, "mb-6")
        ),
        # Recent Reports
        Card(
            CardHeader(H4("Recent Reports")),
            CardBody(create_recent_reports_section(user.id)),
            cls=(CardT.default, "mb-6")
        ),
        
        # Recent Uploads
        Card(
            CardHeader(H4("Recent Uploads")),
            CardBody(create_recent_uploads_section(user.id)),
            cls=(CardT.default, "mb-6")
        ),
        
        # Recent Workspaces
        Card(
            CardHeader(H4("Recent Workspaces")),
            CardBody(create_recent_workspaces_section(user.id)),
            cls=(CardT.default, "mb-6")
        ),
        
        # Dashboard Preview
        Card(
            CardHeader(H4("Dashboard")),
            CardBody(create_dashboard_stats_section(user.id)),
            cls=(CardT.default, "mb-6")
        ),
        cls="bg-muted border-r border-border p-4 overflow-y-auto max-w-xs md:block hidden md:relative absolute top-0 left-0 h-full z-40",
        id="sidebar",
    )


def create_default_content():
    """Create default content for the main area"""
    return Div(
        H1("Welcome to Report Generator"),
        P("Transform unstructured frontline inputs into structured maintenance reports using AI."),
        P("Select an option from the sidebar to get started, or create a new report."),
        Div(
            Button(
                "Create New Report",
                hx_get="/content/workspace",
                hx_target="#main-content",
                cls=(ButtonT.primary, "mr-4"),
            ),
            Button(
                "View Dashboard", hx_get="/content/dashboard", hx_target="#main-content"
            ),
            cls="mt-8"
        ),
        cls="text-center p-8",
    )

login_redir = RedirectResponse("/login", status_code=303)
def user_auth_before(req, session):
    auth = req.scope["auth"] = session.get("auth", None)
    print(session)
    if not auth:
        return login_redir

bware = Beforeware(
    user_auth_before,
    skip=[r"/login", r"/send_login", r"/register", r"/", r"/register-user", r"/static"],
)

hdrs = Theme.blue.headers()
hdrs.append(Script(src="https://unpkg.com/hyperscript.org@0.9.14"))
hdrs.append(Style(css))

app = FastHTML(
    before=bware,
    hdrs=hdrs,
    pico=False,
    secret_key="your-secret-key-change-in-production",
)
rt = app.route

# Serve uploaded files
@rt("/uploads/{file_type}/{filename}")
def serve_file(file_type: str, filename: str):
    file_path = upload_dir / file_type / filename
    if file_path.exists():
        return FileResponse(file_path)
    return "Not found", 404

@rt
def index(session):
    auth = session.get("auth", None)
    if not auth:
        return Titled("Maintenance Report Generator",
            Container(Section(
                H1("Welcome to the Maintenance Report Generator"),
                P(
                    "Transform unstructured frontline inputs into structured maintenance reports using AI."
                ),
                Div(
                    A("Login", href="/login", role="button", cls=ButtonT.primary),
                    A("Register", href="/register", role="button", cls="ml-4"),
                    cls="mt-8",
                ),
        )))

    user = users[auth]
    return Title("Maintenance Report Generator"), Container(
        # Mobile sidebar tab - positioned as a tab on the left edge
        Button(
            UkIcon("panel-left", height=18, width=18),
            id="mobile-menu-toggle", 
            cls="fixed top-20 left-0 z-50 md:hidden p-3 rounded-r-lg bg-primary text-primary-foreground shadow-lg hover:bg-primary/90 border-l-0",
            style="writing-mode: vertical-lr; text-orientation: mixed;",
            _="on click toggle .hidden on #sidebar then toggle .hidden on #mobile-overlay"
        ),
        NavBar(
            DivRAligned(
                Span(f"Welcome, {user.username}", cls="mr-4 hidden sm:inline"),
                Button("Logout", href="/logout", cls=ButtonT.ghost),
            ),
            brand=H3("Maintenance Report Generator")
        ),
        Div(
            create_sidebar(user),
            Div(
                create_default_content(),
                id="main-content",
                cls="p-4 overflow-y-auto flex-1 md:ml-0",
            ),
            # Mobile overlay to close sidebar when clicking outside
            Div(
                cls="fixed inset-0 bg-black/50 z-30 md:hidden hidden",
                id="mobile-overlay",
                _="on click add .hidden to #sidebar then add .hidden to me"
            ),
            cls="flex min-h-screen relative"
        )
    )

@rt
def login():
    return Titled(
        "Login - Maintenance Report Generator",
        Section(
            H1("Login"),
            Form(action="/send_login",method="post")(
                Div(
                    Label("Username"), Input(name="username", required=True, placeholder="Enter your username"),
                ),
                Div(
                    Label("Password"), Input(name="password", type="password", required=True, placeholder="Enter your password"),
                ),
                Button("Login", type="submit", cls=ButtonT.primary),
                cls="max-w-md mx-auto space-y-4",
            ),
            Div(id="login-result"),
            P(A("Don't have an account? Register here", href="/register"), cls="text-center mt-8"),
        ),
    )

@rt
def send_login(username: str, password: str, session):
    try:
        user = users(where=f"username = '{username}' AND active = 1")[0]
        print(f"User found: {user.username}")
        if verify_password(password, user.password_hash):
            session["auth"] = user.id
            return RedirectResponse("/", status_code=303)
        else:
            return Div(
                "Invalid username or password", cls=TextT.error
            )
    except (IndexError, Exception):
        return Div(
            "Invalid username or password", cls=TextT.error
        )

@rt
def register():
    return Titled(
        "Register - Report Generator",
        Container(
            Section(
                H1("Register"),
                Form(hx_post="/register-user", hx_target="#register-result")(
                    Div(
                        Label("Username"),
                        Input(
                            name="username",
                            required=True,
                            placeholder="Choose a username",
                        ),
                    ),
                    Div(
                        Label("Email"),
                        Input(
                            name="email",
                            type="email",
                            required=True,
                            placeholder="Enter your email",
                        ),
                    ),
                    Div(
                        Label("Password"),
                        Input(
                            name="password",
                            type="password",
                            required=True,
                            placeholder="Choose a password",
                        ),
                    ),
                    Button("Register", type="submit", cls=ButtonT.primary),
                    cls="max-w-md mx-auto space-y-4",
                ),
                Div(id="register-result"),
                P(
                    A("Already have an account? Login here", href="/login"),
                    cls="text-center mt-8",
                ),
            )
        ),
    )


@rt("/register-user")
def post(username: str, email: str, password: str, session):
    try:
        # Check if username already exists
        existing_users = users(where=f"username = '{username}' OR email = '{email}'")

        if existing_users:
            return Div(
                "Username or email already exists",
                cls=TextT.error,
            )

        # Create new user
        user_id = users.insert(
            User(
                username=username,
                email=email,
                password_hash=hash_password(password),
                created_at=get_current_timestamp(),
                active=True,
            )
        )

        # Log them in
        session["auth"] = user_id
        return Div(
            P(
                "Registration successful! Redirecting...",
                cls=TextT.success,
            ),
            Script("setTimeout(() => window.location.href = '/', 500)"),
        )

    except Exception as e:
        return Div(
            f"Registration failed: {str(e)}", cls=TextT.error
        )


@rt("/upload")
async def upload_file(request, session):
    """Handle file uploads via drag-and-drop or file input"""
    auth = session.get("auth")
    form = await request.form()
    files = form.getlist("files")
    workspace_id = form.get("workspace_id", generate_uuid())
    user = users[auth]
    print(f"Upload called with workspace_id: {workspace_id}, files: {len(files) if files else 0}")
    print(f"Form keys: {list(form.keys())}")
    if files:
        print(f"First file type: {type(files[0])}")
        if hasattr(files[0], 'filename'):
            print(f"First file: filename={files[0].filename}, content_type={files[0].content_type}")
        else:
            print(f"First file value: {files[0]}")

    # Create workspace if it doesn't exist
    try:
        workspace = workspaces[workspace_id]
    except:
        workspace = workspaces.insert(
            Workspace(
                id=workspace_id,
                user_id=user.id,
                name=f"Workspace {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                created_at=get_current_timestamp(),
                updated_at=get_current_timestamp(),
                status="draft",
            )
        )

    uploaded_items = []
    for file in files:
        print(f"Processing file: {file.filename}, content_type: {file.content_type}")
        if file.filename:
            file_ext = Path(file.filename).suffix
            unique_filename = f"{generate_uuid()}{file_ext}"

            # Handle webm recordings and other audio types
            if file.content_type.startswith("audio/") or file.filename.endswith(('.webm', '.m4a')):
                file_type = "audio"
                storage_path = upload_dir / "audio" / unique_filename
            elif file.content_type.startswith("image/"):
                file_type = "image"
                storage_path = upload_dir / "images" / unique_filename
            else:
                file_type = "text"
                storage_path = upload_dir / "text" / unique_filename

            content = await file.read()
            async with aiofiles.open(storage_path, "wb") as f:
                await f.write(content)

            item_id = generate_uuid()
            
            # Process text files immediately during upload
            transcription = ""
            extracted_data = ""
            processed = False
            
            if file_type == "text":
                try:
                    # Read text content immediately
                    async with aiofiles.open(storage_path, "r") as f:
                        text_content = await f.read()
                    transcription = text_content
                    extracted_data = json.dumps(
                        await extract_entities_from_text(text_content)
                    )
                    processed = True
                except Exception as e:
                    transcription = f"Error reading file: {str(e)}"
                    processed = False
            
            input_items.insert(
                InputItem(
                    id=item_id,
                    user_id=user.id,
                    filename=unique_filename,
                    original_filename=file.filename,
                    file_path=str(storage_path),
                    file_type=file_type,
                    mime_type=file.content_type,
                    file_size=len(content),
                    uploaded_at=get_current_timestamp(),
                    processed=processed,
                    transcription=transcription,
                    extracted_data=extracted_data,
                )
            )
            
            current_item_ids = json.loads(workspace.input_item_ids or "[]")
            current_item_ids.append(item_id)
            workspaces.update({"input_item_ids": json.dumps(current_item_ids)}, workspace_id)

            uploaded_items.append(
                {
                    "id": item_id,
                    "filename": file.filename,
                    "type": file_type,
                    "size": len(content),
                }
            )

    recent_uploads_update = create_recent_uploads_section(user.id, swap_oob=True)
    
    # Get all current workspace items to rebuild the ingested-items div
    updated_workspace = workspaces[workspace_id]
    all_item_ids = json.loads(updated_workspace.input_item_ids or "[]")
    all_items = []
    if all_item_ids:
        item_ids_str = "', '".join(all_item_ids)
        all_items = input_items(where=f"id IN ('{item_ids_str}')")
    
    # Rebuild the entire ingested-items div with all items using unified fragment
    items_content = []
    for workspace_item in all_items:
        items_content.append(build_input_item_fragment(workspace_item, workspace_id))
    
    # Create the updated ingested-items div
    updated_ingested_items = Div(
        *items_content if items_content else [P("No items added yet.", cls=(TextPresets.muted_sm, "italic"))],
        id="ingested-items",
        _="on htmx:afterSwap if .input-item-article in me then remove @disabled from #generate-btn else add @disabled to #generate-btn",
        hx_swap_oob="true"
    )
    
    workspace_input = Input(type="hidden", id="current-workspace-id", value=workspace_id, hx_swap_oob="true")
    
    return updated_ingested_items, recent_uploads_update, workspace_input


@rt("/workspace/{workspace_id}/items")
def get_workspace_items(workspace_id: str, session):
    """Get all items for a workspace"""
    auth = session.get("auth")
    user = users[auth]
    workspace = workspaces[workspace_id]
    item_ids = json.loads(workspace.input_item_ids or "[]")
    
    if not item_ids:
        items = []
    else:
        item_ids_str = "', '".join(item_ids)
        items = input_items(where=f"id IN ('{item_ids_str}')")

    items_html = ""
    for item in items:
        items_html += f"""
        <div class="input-item" data-item-id="{item.id}">
            <div>
                <strong>{item.original_filename}</strong>
                <div class="item-meta">
                    {item.file_type.title()} • {(item.file_size / 1024):.1f} KB
                </div>
            </div>
            <div class="input-item-meta">
                {datetime.fromisoformat(item.uploaded_at).strftime('%H:%M:%S')}
            </div>
        </div>
        """

    return (
        items_html
        if items_html
        else '<p class="italic-muted">No items added yet.</p>'
    )


@rt("/process-items")
async def process_items(workspace_id: str, session):
    """Process workspace items with AI (transcription and entity extraction)"""
    auth = session.get("auth")
    user = users[auth]
    workspace = workspaces[workspace_id]
    item_ids = json.loads(workspace.input_item_ids or "[]")
    
    if not item_ids:
        items = []
    else:
        item_ids_str = "', '".join(item_ids)
        items = input_items(where=f"id IN ('{item_ids_str}')")

    if not items:
        return {"error": "No items found"}

    processed_count = 0
    for item in items:
        if not item.processed:
            transcription = ""
            extracted_data = ""

            # Process audio files (text files are processed during upload)
            if item.file_type == "audio":
                transcription = await transcribe_audio(item.file_path)
                if transcription and not transcription.startswith("Error"):
                    extracted_data = json.dumps(
                        await extract_entities_from_text(transcription)
                    )

            # Update item in database
            input_items.update(
                {
                    "transcription": transcription,
                    "extracted_data": extracted_data,
                    "processed": True,
                },
                item.id,
            )
            processed_count += 1

    return {"success": True, "processed": processed_count}


@rt("/generate-report")
async def generate_report(workspace_id: str, session):
    """Generate a maintenance report from workspace items"""
    auth = session.get("auth")
    user = users[auth]
    workspace = workspaces[workspace_id]
    item_ids = json.loads(workspace.input_item_ids or "[]")
    
    if not item_ids:
        items = []
    else:
        item_ids_str = "', '".join(item_ids)
        items = input_items(where=f"id IN ('{item_ids_str}')")

    if not items:
        return Div(
            P("No items found in workspace to generate report from."),
            cls="text-red-600 p-4",
        )

    await process_items(workspace_id, session)

    workspace = workspaces[workspace_id]
    item_ids = json.loads(workspace.input_item_ids or "[]")
    
    if not item_ids:
        items = []
    else:
        item_ids_str = "', '".join(item_ids)
        items = input_items(where=f"id IN ('{item_ids_str}')")

    items_data = []
    for item in items:
        items_data.append(
            {
                "filename": item.original_filename,
                "type": item.file_type,
                "transcription": item.transcription,
                "extracted_data": item.extracted_data,
            }
        )

    report_data = await generate_maintenance_report(items_data)

    if "error" in report_data:
        return Div(
            H3("Report Generation Failed"),
            P(f"Error: {report_data['error']}"),
            cls="p-8 border border-red-500 rounded-lg mt-8 bg-red-50",
        )

    report_id = generate_uuid()
    maintenance_reports.insert(
        MaintenanceReport(
            id=report_id,
            workspace_id=workspace_id,
            user_id=user.id,
            title=report_data.get("title", "Generated Maintenance Report"),
            description=report_data.get("description", ""),
            equipment_id=report_data.get("equipment_id", ""),
            part_numbers=json.dumps(report_data.get("part_numbers", [])),
            defect_codes=json.dumps(report_data.get("defect_codes", [])),
            corrective_action=report_data.get("corrective_action", ""),
            parts_used=json.dumps(report_data.get("parts_used", [])),
            next_service_date=report_data.get("next_service_date", ""),
            priority=report_data.get("priority", "medium"),
            status="open",
            created_at=get_current_timestamp(),
            updated_at=get_current_timestamp(),
            finalized=False,
        )
    )

    return Div(
        H3("Generated Maintenance Report"),
        Div(
            H4(report_data.get("title", "Maintenance Report")),
            P(Strong("Description: "), report_data.get("description", "N/A")),
            P(Strong("Equipment ID: "), report_data.get("equipment_id", "N/A")),
            P(
                Strong("Priority: "),
                Span(
                    report_data.get("priority", "medium").title(),
                ),
            ),
            P(Strong("Part Numbers: "), ", ".join(report_data.get("part_numbers", []))),
            P(Strong("Defect Codes: "), ", ".join(report_data.get("defect_codes", []))),
            P(
                Strong("Corrective Action: "),
                report_data.get("corrective_action", "N/A"),
            ),
            P(Strong("Parts Used: "), ", ".join(report_data.get("parts_used", []))),
            P(
                Strong("Next Service Date: "),
                report_data.get("next_service_date", "N/A"),
            ),
            id="report-section",
        ),
        Div(
            Button(
                "Edit Report",
                hx_get=f"/content/edit-report/{report_id}",
                hx_target="#main-content",
                cls=ButtonT.primary,
            ),
            cls="mt-4",
        ),
        cls="mt-8 p-4 bg-muted rounded-lg",
    )

@rt("/content/workspace")
@rt("/content/workspace/{workspace_id}")
def content_workspace(session, workspace_id: str = None):
    """Return workspace content fragment - creates new or loads existing workspace"""
    auth = session.get("auth")
    user = users[auth]

    if workspace_id is None:
        # Create a new workspace
        workspace_id = generate_uuid()
        workspace_name = f"Workspace {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        workspaces.insert(
            Workspace(
                id=workspace_id,
                user_id=user.id,
                name=workspace_name,
                created_at=get_current_timestamp(),
                updated_at=get_current_timestamp(),
                status="draft",
                input_item_ids="[]"
            )
        )
    else:
        # Load existing workspace
        try:
            workspace = workspaces[workspace_id]
            if workspace.user_id != user.id:
                return Alert("Unauthorized access to workspace", cls=AlertT.error)
            workspace_name = workspace.name
        except KeyError:
            return Alert("Workspace not found", cls=AlertT.error)

    # Get workspace items if any
    workspace = workspaces[workspace_id]
    item_ids = json.loads(workspace.input_item_ids or "[]")
    items = []
    if item_ids:
        item_ids_str = "', '".join(item_ids)
        items = input_items(where=f"id IN ('{item_ids_str}')")

    # Create items display using unified fragment
    items_content = []
    for item in items:
        items_content.append(build_input_item_fragment(item, workspace_id))

    return Container(
        # Workspace Header Card
        Card(
            CardHeader(
                DivFullySpaced(
                    H3("Workspace Settings"),
                    Button("Delete Workspace",
                        hx_delete=f"/delete-workspace/{workspace.id}/?source=workspace",
                        hx_target="#main-content",
                        hx_confirm="Are you sure you want to delete this workspace?",
                        cls=ButtonT.destructive)
                )
            ),
            CardBody(
                LabelInput(
                    "Workspace Name",
                    type="text",
                    name="name",
                    value=workspace_name,
                    hx_put=f"/update-workspace/{workspace_id}",
                    hx_target="this",
                    hx_swap="none",
                    hx_trigger="keyup changed delay:500ms",
                    id="workspace-name-input"
                )
            ),
            cls=CardT.default
        ),
        # Input Canvas Section
        Section(
            H2("Input Canvas"),
            Subtitle("Add content to your workspace through recording or file upload"),
            cls=SectionT.default
        ),
        
        # Audio Recording Card
        Card(
            CardHeader(
                DivLAligned(UkIcon("mic", height=20, width=20), H4("Audio Recording"))
            ),
            CardBody(
                DivLAligned(
                    Button("Start Recording", 
                        id="start-recording-btn",
                        cls=ButtonT.primary,
                        _="on click call startRecording()"),
                    Button("Stop Recording", 
                        id="stop-recording-btn",
                        disabled=True,
                        cls=ButtonT.destructive,
                        _="on click call stopRecording()"),
                    Span("", id="recording-status", cls="text-green-600 font-medium ml-4"),
                    cls="space-x-3 mb-4"
                ),
                Audio(id="audio-playback", controls=True, cls="w-full hidden")
            ),
            cls=CardT.default
        ),
        
        # File Upload Card
        Card(
            CardHeader(
                DivLAligned(UkIcon("upload", height=20, width=20), H4("File Upload"))
            ),
            CardBody(
                Form(
                    hx_encoding="multipart/form-data",
                    hx_post="/upload",
                    hx_target="#ingested-items",
                    hx_swap="afterbegin",
                    _="on htmx:xhr:progress(loaded, total) set #upload-progress.value to (loaded/total)*100"
                )(
                    UploadZone(
                        DivVStacked(
                            UkIcon("file-plus", height=32, width=32, cls="mx-auto text-muted-foreground mb-4"),
                            P("Drag and drop files here", cls=TextT.medium),
                            P("Supports: Audio (.wav, .mp3), Text (.txt), Images (.png, .jpg)", cls=TextPresets.muted_sm),
                            P("Or click to select files", cls=TextPresets.muted_sm + " mt-2"),
                            cls="text-center py-8"
                        ),
                        Input(
                            type="file",
                            name="files",
                            multiple=True,
                            accept=".wav,.mp3,.txt,.png,.jpg,.jpeg",
                            _="on change trigger submit on closest <form/>"
                        )
                    ),
                    Progress(id="upload-progress", value="0", max="100", cls="w-full mt-4 hidden", 
                            _="on htmx:beforeRequest show me then on htmx:afterRequest hide me")
                )
            ),
            cls=CardT.default
        ),
            # Recording JavaScript
            Script(f"""
            window.mediaRecorder = window.mediaRecorder || null;
            window.audioChunks = window.audioChunks || [];
            window.discarding = window.discarding || false;            window.audioElement = document.getElementById('audio-playback');
            window.startBtn = document.getElementById('start-recording-btn');
            window.stopBtn = document.getElementById('stop-recording-btn');
            window.status = document.getElementById('recording-status');
            window.workspaceId = '{workspace_id}';

            async function startRecording() {{
                try {{
                    const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                    
                    // Use WebM since it's well supported and works with Whisper
                    let mimeType = 'audio/webm';
                    let fileExtension = 'webm';
                    
                    // Store the workspace ID at the time of starting the recording
                    window.recordingWorkspaceId = window.workspaceId;
                    
                    window.mediaRecorder = new MediaRecorder(stream, {{ mimeType: mimeType }});
                    window.audioChunks = [];

                    window.mediaRecorder.ondataavailable = (e) => {{
                        if (e.data.size > 0) window.audioChunks.push(e.data);
                    }};

                    window.mediaRecorder.onstop = () => {{
                        if (window.discarding) {{
                            // Discard recording
                            stream.getTracks().forEach(track => track.stop());
                            window.status.textContent = '';
                            window.mediaRecorder = null;
                            window.audioChunks = [];
                            window.discarding = false;
                            return;
                        }}

                        const audioBlob = new Blob(window.audioChunks, {{ type: mimeType }});
                        const audioUrl = URL.createObjectURL(audioBlob);
                        window.audioElement.src = audioUrl;
                        window.audioElement.style.display = 'block';
                        
                        // Load metadata to get duration
                        window.audioElement.addEventListener('loadedmetadata', function() {{
                            console.log('Audio duration:', window.audioElement.duration);
                        }}, {{ once: true }});
                        window.audioElement.load();

                        // Upload via existing route
                        const formData = new FormData();
                        formData.append('files', audioBlob, `recording-${{Date.now()}}.` + fileExtension);
                        formData.append('workspace_id', window.recordingWorkspaceId);

                        fetch('/upload', {{
                            method: 'POST',
                            body: formData
                        }})
                        .then(response => response.text())
                        .then(html => {{
                            // Process out-of-band swaps manually
                            const parser = new DOMParser();
                            const doc = parser.parseFromString(html, 'text/html');
                            doc.querySelectorAll('[hx-swap-oob], [data-hx-swap-oob]').forEach(el => {{
                                const oobValue = el.getAttribute('hx-swap-oob') || el.getAttribute('data-hx-swap-oob');
                                // Assuming default OOB behavior: replace element with matching ID
                                const targetId = (oobValue === 'true' || !oobValue.includes(':')) ? el.id : oobValue.split(':')[1];
                                const target = document.getElementById(targetId);
                                if (target) {{
                                    target.outerHTML = el.outerHTML;
                                    const newTarget = document.getElementById(targetId);
                                    if (newTarget) htmx.process(newTarget);
                                }}
                            }});
                        }})
                        .catch(error => console.error('Upload error:', error));

                        // Stop stream and cleanup
                        stream.getTracks().forEach(track => track.stop());
                        window.status.textContent = '';
                        
                        // Reset for next recording
                        window.mediaRecorder = null;
                        window.audioChunks = [];
                    }};

                    window.mediaRecorder.start();
                    window.startBtn.disabled = true;
                    window.stopBtn.disabled = false;
                    window.status.textContent = ' Recording...';
                }} catch (err) {{
                    console.error('Error accessing microphone:', err);
                    alert('Microphone access denied or unavailable.');
                }}
            }}

            function stopRecording() {{
                if (window.mediaRecorder && window.mediaRecorder.state !== 'inactive') {{
                    window.mediaRecorder.stop();
                    window.startBtn.disabled = false;
                    window.stopBtn.disabled = true;
                }}
            }}

            // Restore UI state if already recording (e.g., after navigation)
            if (window.mediaRecorder && window.mediaRecorder.state === 'recording') {{
                window.startBtn.disabled = true;
                window.stopBtn.disabled = false;
                window.status.textContent = ' Recording...';
            }}

            // Handle navigation away during recording
            document.addEventListener('htmx:beforeSwap', (evt) => {{
                if (window.mediaRecorder && window.mediaRecorder.state === 'recording' && evt.detail.target.contains(window.startBtn)) {{
                    window.discarding = true;
                    window.mediaRecorder.stop();
                    window.startBtn.disabled = false;
                    window.stopBtn.disabled = true;
                    window.status.textContent = '';
                }}
            }});
        """),
        
        # Ingested Items Card
        Card(
            CardHeader(
                DivFullySpaced(
                    DivLAligned(UkIcon("file-text", height=20, width=20), H4("Workspace Items")),
                    Button(
                        UkIcon("plus", height=16, width=16, cls="mr-2"),
                        "Add Existing Item",
                        hx_get=f"/modal/add-input/{workspace_id}",
                        hx_target="#modal-container",
                        cls=ButtonT.secondary
                    )
                )
            ),
            CardBody(
                Div(
                    *items_content if items_content else [
                        Center(
                            DivVStacked(
                                UkIcon("inbox", height=48, width=48, cls="mx-auto text-muted-foreground mb-4"),
                                P("No items added yet", cls=TextT.medium),
                                P("Upload files or add existing items to get started", cls=TextPresets.muted_sm),
                                cls="text-center py-8"
                            )
                        )
                    ],
                    id="ingested-items",
                    _="on htmx:afterSwap if .input-item-article in me then remove @disabled from #generate-btn else add @disabled to #generate-btn"
                )
            ),
            cls=CardT.default
        ),
        
        # Generate Report Card
        Card(
            CardHeader(
                DivLAligned(UkIcon("file-output", height=20, width=20), H4("Generate Report"))
            ),
            CardBody(
                DivVStacked(
                    P("Create a maintenance report from your workspace items", cls=TextPresets.muted_sm + " mb-4"),
                    Button(
                        UkIcon("zap", height=16, width=16, cls="mr-2"),
                        "Generate Report",
                        hx_post="/content/generate-report",
                        hx_target="#main-content",
                        cls=(ButtonT.primary, "w-full"),
                        id="generate-btn",
                        _="on htmx:configRequest(detail) if #current-workspace-id then set detail.parameters.workspace_id to #current-workspace-id.value end",
                        disabled=False if items_content else True
                    )
                )
            ),
            cls=CardT.default
        ),
        Div(id="report-section"),
        Input(type="hidden", id="current-workspace-id", value=workspace_id),
        Div(id="modal-container"),
    )


@rt("/modal/add-input/{workspace_id}")
def modal_add_input(workspace_id: str, session):
    """Return modal for adding existing input items to workspace"""
    auth = session.get("auth")
    user = users[auth]
    
    # Get workspace and its current items
    workspace = workspaces[workspace_id]
    if workspace.user_id != user.id:
        return Alert("Unauthorized", cls=AlertT.error)
    
    current_item_ids = json.loads(workspace.input_item_ids or "[]")
    
    # Get all user input items not already in this workspace
    all_user_items = input_items(where=f"user_id = {user.id}")
    available_items = [item for item in all_user_items if item.id not in current_item_ids]
    
    modal_items = []
    for item in available_items:
        modal_items.append(
            Card(
                CardBody(
                    Div(
                        Strong(item.original_filename, cls=TextT.medium),
                        P(f"{item.file_type.title()} • {(item.file_size / 1024):.1f} KB • {datetime.fromisoformat(item.uploaded_at).strftime('%m/%d %H:%M')}",
                          cls=TextPresets.muted_sm)
                    )
                ),
                hx_post=f"/add-item-to-workspace/{workspace_id}/{item.id}",
                hx_target=f"#modal-item-{item.id}",
                hx_swap="outerHTML",
                cls=CardT.hover + " cursor-pointer mb-4",
                id=f"modal-item-{item.id}"
            )
        )
    
    return Modal(
        *modal_items if modal_items else [
            P("No additional input items available.", 
              cls=(TextPresets.muted_sm, "italic text-center p-8"))
        ],
        header=H3("Add Existing Input Items"),
        footer=ModalCloseButton(
            "Close",
            hx_get="/modal/close",
            hx_target="#modal-container", 
            hx_swap="innerHTML",
            htmx=True,
            cls=ButtonT.secondary
        ),
        body_cls="max-h-96 overflow-y-auto",
        open=True
    )


@rt("/modal/close")
def modal_close():
    """Close modal by returning empty content"""
    return ""


@rt("/modal/edit-transcription/{item_id}")
def modal_edit_transcription(item_id: str, session):
    """Return modal for editing transcription or text content"""
    auth = session.get("auth")
    user = users[auth]
    
    try:
        # Verify item ownership
        item = input_items[item_id]
        if item.user_id != user.id:
            return Alert("Unauthorized", cls=AlertT.error)
        
        if item.file_type not in ["audio", "text"]:
            return Alert("Not an audio or text file", cls=AlertT.error)
        
        # Dynamic labels based on file type
        title = "Edit Transcription" if item.file_type == "audio" else "Edit Text Content"
        label_text = "Transcription" if item.file_type == "audio" else "Content"
        placeholder_text = "Transcription will appear here..." if item.file_type == "audio" else "Text content will appear here..."
        
        return Modal(
            FormLabel(f"{label_text} for: {item.original_filename}"),
            TextArea(
                item.transcription or "",
                name="transcription",
                hx_put=f"/update-transcription/{item_id}",
                hx_target="this",
                hx_swap="none",
                hx_trigger="keyup changed delay:500ms",
                placeholder=placeholder_text
            ),
            header=H3(title),
            footer=ModalCloseButton(
                "Close",
                hx_get="/modal/close",
                hx_target="#modal-container",
                hx_swap="innerHTML",
                htmx=True,
                cls=ButtonT.secondary
            ),
            dialog_cls="max-w-4xl", 
            open=True
        )
        
    except Exception as e:
        return Alert(f"Error: {str(e)}", cls=AlertT.error)


@rt("/update-transcription/{item_id}", methods=["PUT"])
def update_transcription(item_id: str, session, transcription: str):
    """Update transcription or text content for an input item"""
    auth = session.get("auth")
    user = users[auth]
    
    try:
        # Verify item ownership
        item = input_items[item_id]
        if item.user_id != user.id:
            return Alert("Unauthorized", cls=AlertT.error)
        
        # Update the transcription
        input_items.update({"transcription": transcription}, item_id)
        
        # Create out-of-band update with proper workspace context
        updated_item = input_items[item_id]
        
        # Find which workspace this item belongs to for the current user
        workspace_id = None
        user_workspaces = workspaces(where=f"user_id = {user.id}")
        for workspace in user_workspaces:
            item_ids = json.loads(workspace.input_item_ids or "[]")
            if item_id in item_ids:
                workspace_id = workspace.id
                break
        
        # Create fragment with correct workspace context to match existing DOM structure  
        article = build_input_item_fragment(updated_item, workspace_id)
        
        # Set OOB swap attribute properly - recreate article with hx_swap_oob in constructor
        updated_article = Article(
            *article.children,
            id=article.attrs.get("id"),
            cls=article.attrs.get("cls"),
            hx_swap_oob="true"
        )
        
        print(updated_article, updated_article.attrs)
        
        return updated_article
        
    except Exception as e:
        return Alert(f"Error updating transcription: {str(e)}", cls=AlertT.error)


@rt("/update-extracted-field/{item_id}/equipment_ids", methods=["PUT"])
def update_equipment_ids(item_id: str, session, equipment_ids: str = ""):
    """Update equipment_ids field in extracted data"""
    return _update_extracted_field_helper(item_id, "equipment_ids", equipment_ids, session)

@rt("/update-extracted-field/{item_id}/part_numbers", methods=["PUT"])
def update_part_numbers(item_id: str, session, part_numbers: str = ""):
    """Update part_numbers field in extracted data"""
    return _update_extracted_field_helper(item_id, "part_numbers", part_numbers, session)

@rt("/update-extracted-field/{item_id}/defect_codes", methods=["PUT"])
def update_defect_codes(item_id: str, session, defect_codes: str = ""):
    """Update defect_codes field in extracted data"""
    return _update_extracted_field_helper(item_id, "defect_codes", defect_codes, session)

@rt("/update-extracted-field/{item_id}/priority", methods=["PUT"])
def update_priority(item_id: str, session, priority: str = ""):
    """Update priority field in extracted data"""
    return _update_extracted_field_helper(item_id, "priority", priority, session)

@rt("/update-extracted-field/{item_id}/description", methods=["PUT"])
def update_description(item_id: str, session, description: str = ""):
    """Update description field in extracted data"""
    return _update_extracted_field_helper(item_id, "description", description, session)

def _update_extracted_field_helper(item_id: str, field: str, value: str, session):
    """Helper function to update a specific field in the extracted data"""
    auth = session.get("auth")
    user = users[auth]
    
    try:
        # Verify item ownership
        item = input_items[item_id]
        if item.user_id != user.id:
            return Alert("Unauthorized", cls=AlertT.error)
        
        # Parse current extracted data
        if item.extracted_data:
            import json
            try:
                data = json.loads(item.extracted_data)
            except:
                data = {}
        else:
            data = {}
        
        # Update the specific field
        if field in ["equipment_ids", "part_numbers", "defect_codes"]:
            # Handle comma-separated lists
            if value.strip():
                data[field] = [item.strip() for item in value.split(",") if item.strip()]
            else:
                data[field] = []
        else:
            # Handle simple string fields
            data[field] = value
        
        # Save updated data back to database
        updated_data = json.dumps(data)
        input_items.update({"extracted_data": updated_data}, item_id)
        
        return "Updated"
        
    except Exception as e:
        return Alert(f"Error updating field: {str(e)}", cls=AlertT.error)


@rt("/update-extracted-data/{item_id}", methods=["PUT"])
def update_extracted_data(item_id: str, extracted_data: str, session):
    """Update entire extracted data for an input item"""
    auth = session.get("auth")
    user = users[auth]
    
    try:
        # Verify item ownership
        item = input_items[item_id]
        if item.user_id != user.id:
            return Alert("Unauthorized", cls=AlertT.error)
        
        # Update extracted data
        input_items.update({"extracted_data": extracted_data}, item_id)
        
        return "Updated"
        
    except Exception as e:
        return Alert(f"Error updating extracted data: {str(e)}", cls=AlertT.error)


@rt("/modal/detect-entity/{item_id}")
def modal_detect_entity(item_id: str, session):
    """Return modal for entity detection input"""
    auth = session.get("auth")
    user = users[auth]
    
    try:
        # Verify item ownership
        item = input_items[item_id]
        if item.user_id != user.id:
            return Alert("Unauthorized", cls=AlertT.error)
        
        if item.file_type != "image":
            return Alert("Not an image file", cls=AlertT.error)
        
        return Modal(
            FormLabel(f"Image: {item.original_filename}"),
            FormLabel("Entity to detect:", cls="mt-4"),
            Input(
                type="text",
                name="entity_type",
                placeholder="e.g., person, car, face, door, window...",
            ),
            header=H3("Detect Entity in Image"),
            footer=Div(
                Button(
                    "Detect Entity",
                    hx_post=f"/detect-entity/{item_id}",
                    hx_target="#modal-container",
                    hx_swap="innerHTML",
                    hx_include="closest div",
                    cls=ButtonT.primary
                ),
                ModalCloseButton(
                    "Cancel",
                    hx_get="/modal/close",
                    hx_target="#modal-container",
                    hx_swap="innerHTML",
                    htmx=True,
                    cls=ButtonT.secondary
                ),
                cls="flex gap-2 justify-end"
            ),
            open=True
        )
        
    except Exception as e:
        return Alert(f"Error: {str(e)}", cls=AlertT.error)


@rt("/detect-entity/{item_id}", methods=["POST"])
async def detect_entity_in_image(item_id: str, session, entity_type: str):
    """Detect entities in an image using Moondream API"""
    auth = session.get("auth")
    user = users[auth]
    
    try:
        # Verify item ownership
        item = input_items[item_id]
        if item.user_id != user.id:
            return Alert("Unauthorized", cls=AlertT.error)
        
        if item.file_type != "image":
            return Alert("Not an image file", cls=AlertT.error)
        
        if not entity_type or not entity_type.strip():
            return Alert("Please specify an entity type to detect", cls=AlertT.error)
        
        # Perform entity detection
        from ai_services import detect_entities_in_image
        result = await detect_entities_in_image(item.file_path, entity_type.strip())
        
        if "error" in result:
            return Div(
                H3("Entity Detection Failed"),
                P(result["error"]),
                Button(
                    "Try Again",
                    hx_get=f"/modal/detect-entity/{item_id}",
                    hx_target="#modal-container",
                    hx_swap="innerHTML",
                ),
            )
        
        # Show results
        if result["count"] == 0:
            return Div(
                H3("No Entities Found"),
                P(result["message"]),
                Button(
                    "Try Different Entity",
                    hx_get=f"/modal/detect-entity/{item_id}",
                    hx_target="#modal-container", 
                    hx_swap="innerHTML",
                ),
                Button(
                    "Close",
                    hx_get="/modal/close",
                    hx_target="#modal-container",
                    hx_swap="innerHTML",
                ),
            )
        else:
            # Show results within modal structure
            return Div(
                # Modal backdrop
                Div(
                    # Modal content
                    Div(
                        Div(
                            H3("Entities Detected!"),
                            Button(
                                "×",
                                hx_get="/modal/close",
                                hx_target="#modal-container",
                                hx_swap="innerHTML",
                            ),
                        ),
                        Div(
                            P(f"{result['message']} - Preview with bounding boxes:"),
                            
                            # Image preview with bounding boxes
                            Div(
                                Img(
                                    src=f"uploads/images/{Path(result['preview_path']).name}",
                                    alt="Preview with detected entities",
                                    cls="max-w-full max-h-72 border-2 border-border rounded-lg mb-4"
                                ),
                            ),
                            
                            # Detection details
                            Div(
                                Strong("Detection Details:"),
                                Ul(
                                    *[Li(f"{result['entity_type'].title()} {det['index']}: Bounding box at ({det['pixel_coords']['x_min']}, {det['pixel_coords']['y_min']}) to ({det['pixel_coords']['x_max']}, {det['pixel_coords']['y_max']})") 
                                      for det in result["detections"]],
                                ),
                            ),
                            
                            P("Do you want to keep these bounding boxes on your image?"),
                            
                            # Accept/Reject buttons
                            Div(
                                Button(
                                    "✓ Accept",
                                    hx_post=f"/accept-entity-detection/{item_id}",
                                    hx_target="#modal-container",
                                    hx_swap="innerHTML",
                                    hx_vals=f'{{"preview_path": "{result["preview_path"]}", "original_path": "{result["original_path"]}"}}',
                                ),
                                Button(
                                    "✗ Reject", 
                                    hx_post=f"/reject-entity-detection/{item_id}",
                                    hx_target="#modal-container",
                                    hx_swap="innerHTML",
                                    hx_vals=f'{{"preview_path": "{result["preview_path"]}"}}',
                                ),
                                Button(
                                    "Detect Different Entity",
                                    hx_get=f"/modal/detect-entity/{item_id}",
                                    hx_target="#modal-container",
                                    hx_swap="innerHTML",
                                ),
                            ),
                        ),
                    ),
                    _="on click if event.target == me then trigger click on the first button in #modal-container end"
                ),
                id="modal-detect-entity-results"
            )
        
    except Exception as e:
        return Alert(f"Error detecting entities: {str(e)}", cls=AlertT.error)


@rt("/accept-entity-detection/{item_id}", methods=["POST"])
async def accept_entity_detection(item_id: str, session, preview_path: str, original_path: str):
    """Accept entity detection by overwriting original image with preview"""
    auth = session.get("auth")
    user = users[auth]
    
    try:
        # Verify item ownership
        item = input_items[item_id]
        if item.user_id != user.id:
            return Alert("Unauthorized", cls=AlertT.error)
        
        # Copy preview image to original location
        import shutil
        shutil.copy2(preview_path, original_path)
        
        # Clean up preview file
        import os
        if os.path.exists(preview_path):
            os.remove(preview_path)
        
        return Div(
            H3("✓ Entity Detection Applied!"),
            P("The bounding boxes have been permanently applied to your image."),
            Button(
                "Close",
                hx_get="/modal/close",
                hx_target="#modal-container",
                hx_swap="innerHTML",
            ),
        )
        
    except Exception as e:
        return Alert(f"Error applying detection: {str(e)}", cls=AlertT.error)


@rt("/reject-entity-detection/{item_id}", methods=["POST"])
async def reject_entity_detection(item_id: str, session, preview_path: str):
    """Reject entity detection by discarding preview and keeping original"""
    auth = session.get("auth")
    user = users[auth]
    
    try:
        # Verify item ownership
        item = input_items[item_id]
        if item.user_id != user.id:
            return Alert("Unauthorized", cls=AlertT.error)
        
        # Clean up preview file
        import os
        if os.path.exists(preview_path):
            os.remove(preview_path)
        
        return Div(
            H3("✗ Entity Detection Rejected"),
            P("The preview has been discarded. Your original image remains unchanged."),
            Button(
                "Try Different Entity",
                hx_get=f"/modal/detect-entity/{item_id}",
                hx_target="#modal-container",
                hx_swap="innerHTML",
            ),
            Button(
                "Close",
                hx_get="/modal/close",
                hx_target="#modal-container",
                hx_swap="innerHTML",
            ),
        )
        
    except Exception as e:
        return Alert(f"Error rejecting detection: {str(e)}", cls=AlertT.error)


@rt("/transcribe-audio/{item_id}", methods=["POST"])
async def transcribe_audio_item(item_id: str, session, request):
    """Transcribe an audio input item"""
    auth = session.get("auth")
    user = users[auth]
    
    try:
        # Verify item ownership
        item = input_items[item_id]
        if item.user_id != user.id:
            return Alert("Unauthorized", cls=AlertT.error)
        
        if item.file_type != "audio":
            return Div("Not an audio file")
        
        # Transcribe the audio
        transcription = await transcribe_audio(item.file_path)
        
        # Update the item with transcription
        input_items.update({
            "transcription": transcription,
            "processed": True
        }, item_id)
        
        # Get updated item
        updated_item = input_items[item_id]
        
        # Detect context from the referrer or HX-Target header
        hx_target = request.headers.get("HX-Target", "")
        referrer = request.headers.get("Referer", "")
        
        # Individual input view context
        if "view-input" in referrer or "closest div" in hx_target:
            return Div(
                H3("Transcription"),
                Textarea(
                    updated_item.transcription,
                    hx_put=f"/update-transcription/{updated_item.id}",
                    hx_target="this",
                    hx_swap="none",
                    hx_trigger="keyup changed delay:500ms",
                    name="transcription",
                    placeholder="Transcription will appear here..."
                ),
            )
        
        # All inputs view context (closest article)
        elif "closest article" in hx_target or "content/inputs" in referrer:
            content_sections = []
            
            # File info section
            content_sections.append(P(Strong("File: "), updated_item.original_filename))
            content_sections.append(P(Strong("Type: "), updated_item.file_type.title()))
            content_sections.append(P(Strong("Size: "), f"{(updated_item.file_size / 1024):.1f} KB"))
            
            # Add transcription content for audio files
            if updated_item.transcription:
                # Show shorter preview of transcription (clickable to edit)
                preview = updated_item.transcription[:80] + "..." if len(updated_item.transcription) > 80 else updated_item.transcription
                content_sections.append(
                    P(
                        Strong("Transcription: "),
                        Span(
                            f'"{preview}"',
                            hx_get=f"/modal/edit-transcription/{updated_item.id}",
                            hx_target="#modal-container",
                            title="Click to edit transcription"
                        )
                    )
                )
            
            return Article(
                Header(
                    H3(updated_item.original_filename),
                    Div(
                        A(
                            "View",
                            hx_get=f"/content/view-input/{updated_item.id}",
                            hx_target="#main-content",
                        ),
                        Span(datetime.fromisoformat(updated_item.uploaded_at).strftime('%Y-%m-%d %H:%M'))
                    ),
                ),
                *content_sections,
            )
        
        # Workspace view context (default) - use unified fragment
        else:
            # Extract workspace_id from request context if available
            workspace_id = request.headers.get("Referer", "").split("/")[-1] if "workspace" in request.headers.get("Referer", "") else None
            return build_input_item_fragment(updated_item, workspace_id)
        
    except Exception as e:
        return Alert(f"Error transcribing audio: {str(e)}", cls=AlertT.error)


@rt("/add-item-to-workspace/{workspace_id}/{item_id}", methods=["POST"])
def add_item_to_workspace(workspace_id: str, item_id: str, session):
    """Add an existing input item to a workspace"""
    auth = session.get("auth")
    user = users[auth]
    
    try:
        # Verify workspace ownership
        workspace = workspaces[workspace_id]
        if workspace.user_id != user.id:
            return Alert("Unauthorized", cls=AlertT.error)
        
        # Verify item ownership
        item = input_items[item_id]
        if item.user_id != user.id:
            return Alert("Unauthorized", cls=AlertT.error)
        
        # Add item to workspace
        current_item_ids = json.loads(workspace.input_item_ids or "[]")
        if item_id not in current_item_ids:
            current_item_ids.append(item_id)
            workspaces.update({
                "input_item_ids": json.dumps(current_item_ids),
                "updated_at": get_current_timestamp()
            }, workspace_id)
        
        # Get all current workspace items to rebuild the ingested-items div
        updated_workspace = workspaces[workspace_id]
        all_item_ids = json.loads(updated_workspace.input_item_ids or "[]")
        all_items = []
        if all_item_ids:
            item_ids_str = "', '".join(all_item_ids)
            all_items = input_items(where=f"id IN ('{item_ids_str}')")
        
        # Rebuild the entire ingested-items div with all items using unified fragment
        items_content = []
        for workspace_item in all_items:
            items_content.append(build_input_item_fragment(workspace_item, workspace_id))
        
        # Create the updated ingested-items div
        updated_ingested_items = Div(
            *items_content if items_content else [P("No items added yet.")],
            id="ingested-items",
            _="on htmx:afterSwap if .input-item-article in me then remove @disabled from #generate-btn else add @disabled to #generate-btn",
            hx_swap_oob="true"
        )
        
        # Update sidebar sections
        recent_workspaces_update = create_recent_workspaces_section(user.id, swap_oob=True)
        
        # Check if there are any remaining items in the modal
        updated_current_item_ids = json.loads(workspaces[workspace_id].input_item_ids or "[]")
        remaining_items = [i for i in input_items(where=f"user_id = {user.id}") if i.id not in updated_current_item_ids]
        
        # If no items remain, show the "no items" message
        if not remaining_items:
            no_items_message = Div(
                P("No additional input items available."),
                id="modal-no-items",
                hx_swap_oob="innerHTML:.modal-items-container"
            )
            return Div(), updated_ingested_items, recent_workspaces_update, no_items_message
        else:
            # Remove this item from modal (empty div to replace it)
            return Div(), updated_ingested_items, recent_workspaces_update
        
    except Exception as e:
        return Alert(f"Error: {str(e)}", cls=AlertT.error)


@rt("/content/reports")
def content_reports(session):
    """Return reports content fragment"""
    auth = session.get("auth")
    user = users[auth]

    user_reports = maintenance_reports(where=f"user_id == '{user.id}'")

    reports_content = []
    if user_reports:
        for report in user_reports:
            # Status label styling
            status_label_class = {
                'open': 'bg-amber-100 text-amber-800',
                'in_progress': 'bg-blue-100 text-blue-800', 
                'completed': 'bg-green-100 text-green-800',
                'closed': 'bg-gray-100 text-gray-800'
            }.get(report.status, 'bg-gray-100 text-gray-800')
            
            # Priority label styling
            priority_label_class = {
                'low': 'bg-green-100 text-green-800',
                'medium': 'bg-yellow-100 text-yellow-800',
                'high': 'bg-orange-100 text-orange-800',
                'critical': 'bg-red-100 text-red-800'
            }.get(report.priority, 'bg-gray-100 text-gray-800')

            reports_content.append(
                Card(
                    CardHeader(
                        DivFullySpaced(
                            Button(
                                report.title,
                                hx_get=f"/content/view-report/{report.id}",
                                hx_target="#main-content",
                                cls=(ButtonT.ghost, "text-left p-0 h-auto font-medium hover:text-primary text-lg")
                            ),
                            DivLAligned(
                                Label(
                                    report.status.replace("_", " ").title(),
                                    cls=status_label_class + " text-xs px-2 py-1 rounded-full"
                                ),
                                Label(
                                    report.priority.title(),
                                    cls=priority_label_class + " text-xs px-2 py-1 rounded-full ml-2"
                                )
                            )
                        )
                    ),
                    CardBody(
                        DivVStacked(
                            P(
                                report.description[:120] + "..." if len(report.description) > 120 else report.description,
                                cls=TextPresets.muted_sm
                            ),
                            DivFullySpaced(
                                Small(f"Equipment: {report.equipment_id}", cls=TextPresets.muted_sm),
                                Small(
                                    datetime.fromisoformat(report.created_at).strftime('%m/%d/%y %H:%M'),
                                    cls=TextPresets.muted_sm
                                )
                            ),
                            cls="space-y-3"
                        )
                    ),
                    cls=(CardT.hover, "cursor-pointer"),
                    hx_get=f"/content/view-report/{report.id}",
                    hx_target="#main-content"
                )
            )
    else:
        reports_content = [
            Card(
                CardBody(
                    Center(
                        DivVStacked(
                            UkIcon("file-text", height=48, width=48, cls="mx-auto text-muted-foreground mb-4"),
                            P("No reports available yet.", cls=TextPresets.muted_sm + " text-center"),
                            Button(
                                "Create Your First Report",
                                hx_get="/content/workspace",
                                hx_target="#main-content",
                                cls=ButtonT.primary
                            ),
                            cls="text-center py-8"
                        )
                    )
                ),
                cls=CardT.default
            )
        ]

    return Container(
        Section(
            H1("Maintenance Reports"),
            Subtitle(f"You have {len(user_reports)} saved reports"),
            cls=SectionT.default
        ),
        Section(
            DivVStacked(
                *reports_content,
                cls="space-y-4"
            ),
            cls=SectionT.default
        ),
        cls=ContainerT.lg
    )


@rt("/content/dashboard")
def content_dashboard(session):
    """Return dashboard content fragment"""
    auth = session.get("auth")
    user = users[auth]

    user_reports = maintenance_reports(where=f"user_id = {user.id}")
    total_reports = len(user_reports)

    status_counts = {"open": 0, "in_progress": 0, "completed": 0, "closed": 0}
    priority_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}

    for report in user_reports:
        status_counts[report.status] = status_counts.get(report.status, 0) + 1
        priority_counts[report.priority] = priority_counts.get(report.priority, 0) + 1

    recent_reports = sorted(user_reports, key=lambda r: r.created_at, reverse=True)[:5]

    return Container(
        Section(
            H1("Dashboard"),
            Subtitle("Overview of your maintenance reporting activity"),
            cls=SectionT.default
        ),
        
        # Stats Cards Row
        Section(
            Grid(
                # Total Reports Card
                Card(
                    CardHeader(
                        H5("Total Reports"),
                        cls="p-0"
                    ),
                    CardBody(
                        Div(
                            H2(str(total_reports), cls="text-3xl font-bold"),
                            P("Reports Created", cls=TextPresets.muted_sm)
                        ),
                        cls="p-0"
                    ),
                    cls=CardT.default
                ),
                
                # Status Breakdown Card
                Card(
                    CardHeader(
                        H5("By Status"),
                        cls="p-0"
                    ),
                    CardBody(
                        DivVStacked(
                            DivFullySpaced(
                                Span("Open", cls=TextPresets.muted_sm),
                                Strong(str(status_counts['open']))
                            ),
                            DivFullySpaced(
                                Span("In Progress", cls=TextPresets.muted_sm),
                                Strong(str(status_counts['in_progress']))
                            ),
                            DivFullySpaced(
                                Span("Completed", cls=TextPresets.muted_sm),
                                Strong(str(status_counts['completed']))
                            ),
                            cls="space-y-2"
                        ),
                        cls="p-0"
                    ),
                    cls=CardT.default
                ),
                
                # Priority Breakdown Card
                Card(
                    CardHeader(
                        H5("By Priority"),
                        cls="p-0"
                    ),
                    CardBody(
                        DivVStacked(
                            DivFullySpaced(
                                Span("Critical", cls=TextPresets.muted_sm),
                                Strong(str(priority_counts['critical']))
                            ),
                            DivFullySpaced(
                                Span("High", cls=TextPresets.muted_sm),
                                Strong(str(priority_counts['high']))
                            ),
                            DivFullySpaced(
                                Span("Medium", cls=TextPresets.muted_sm),
                                Strong(str(priority_counts['medium']))
                            ),
                            DivFullySpaced(
                                Span("Low", cls=TextPresets.muted_sm),
                                Strong(str(priority_counts['low']))
                            ),
                            cls="space-y-2"
                        ),
                        cls="p-0"
                    ),
                    cls=CardT.default
                ),
                
                cols=3
            ),
            cls=SectionT.default
        ),
        
        # Recent Reports Section (if reports exist)
        *(
            [
                Section(
                    Card(
                        CardHeader(
                            DivFullySpaced(
                                DivLAligned(
                                    UkIcon("clock", height=20, width=20, cls="text-muted-foreground"),
                                    H4("Recent Reports")
                                ),
                                Button(
                                    "View All",
                                    hx_get="/content/reports",
                                    hx_target="#main-content",
                                    cls=ButtonT.ghost
                                )
                            )
                        ),
                        CardBody(
                            DivVStacked(
                                *(
                                    [
                                        Card(
                                            CardBody(
                                                DivVStacked(
                                                    Button(
                                                        report.title,
                                                        hx_get=f"/content/view-report/{report.id}",
                                                        hx_target="#main-content",
                                                        cls=(ButtonT.ghost, "text-left p-0 h-auto font-medium hover:text-primary")
                                                    ),
                                                    P(
                                                        report.description[:60] + "..." if len(report.description) > 60 else report.description,
                                                        cls=TextPresets.muted_sm
                                                    ),
                                                    DivLAligned(
                                                        Label(report.priority.title(), cls={
                                                            'critical': 'bg-red-100 text-red-800',
                                                            'high': 'bg-orange-100 text-orange-800',
                                                            'medium': 'bg-yellow-100 text-yellow-800',
                                                            'low': 'bg-green-100 text-green-800'
                                                        }.get(report.priority, LabelT.secondary)),
                                                        Small(
                                                            datetime.fromisoformat(report.created_at).strftime('%m/%d/%y'),
                                                            cls=TextPresets.muted_sm
                                                        ),
                                                        cls="space-x-2 mt-2"
                                                    )
                                                )
                                            ),
                                            cls=(CardT.hover, "cursor-pointer"),
                                            hx_get=f"/content/view-report/{report.id}",
                                            hx_target="#main-content"
                                        )
                                        for report in recent_reports
                                    ]
                                    if recent_reports
                                    else [
                                        Center(
                                            P("No reports created yet", cls=TextPresets.muted_sm + " py-8")
                                        )
                                    ]
                                ),
                                cls="space-y-3"
                            )
                        ),
                        cls=CardT.default
                    ),
                    cls=SectionT.default
                )
            ]
            if total_reports > 0
            else []
        ),
        
        # Get Started Section (if no reports)
        *(
            [
                Section(
                    Card(
                        CardBody(
                            Center(
                                DivVStacked(
                                    UkIcon("rocket", height=48, width=48, cls="mx-auto text-primary mb-4"),
                                    H3("Get Started"),
                                    P(
                                        "Create your first maintenance report by uploading audio recordings, text files, or images from the field.",
                                        cls=TextPresets.muted_sm + " text-center max-w-md"
                                    ),
                                    Button(
                                        UkIcon("plus-circle", height=16, width=16, cls="mr-2"),
                                        "Start New Report",
                                        hx_get="/content/workspace",
                                        hx_target="#main-content",
                                        cls=ButtonT.primary
                                    ),
                                    cls="text-center py-8"
                                )
                            )
                        ),
                        cls=CardT.default
                    ),
                    cls=SectionT.default
                )
            ]
            if total_reports == 0
            else []
        ),
        
        cls=ContainerT.lg
    )


@rt("/content/workspaces")
def content_workspaces(session):
    """Return all workspaces content fragment"""
    auth = session.get("auth")
    user = users[auth]
    
    user_workspaces = workspaces(where=f"user_id = {user.id}")
    
    workspaces_content = []
    if user_workspaces:
        for workspace in user_workspaces:
            item_count = len(json.loads(workspace.input_item_ids or "[]"))
            
            # Status styling
            status_styles = {
                "draft": (LabelT.secondary, "Draft"),
                "processing": ("bg-orange-100 text-orange-800", "Processing"), 
                "completed": ("bg-green-100 text-green-800", "Completed")
            }
            status_style, status_text = status_styles.get(workspace.status, (LabelT.secondary, workspace.status.title()))
            
            workspaces_content.append(
                DivLAligned(
                    Card(
                        CardHeader(
                            DivLAligned(
                                UkIcon("folder", height=20, width=20, cls="mr-3 text-muted-foreground"),
                                DivVStacked(
                                    H4(workspace.name, cls=TextT.medium),
                                    DivLAligned(
                                        Label(status_text, cls=status_style if isinstance(status_style, str) else status_style),
                                        Small(f"{item_count} item{'s' if item_count != 1 else ''}", cls=TextPresets.muted_sm),
                                        cls="space-x-2 mt-1"
                                    )
                                )
                            )
                        ),
                        CardBody(
                            DivLAligned(
                                DivLAligned(
                                    UkIcon("calendar", height=14, width=14, cls="mr-1 text-muted-foreground"),
                                    Small(f"Created {datetime.fromisoformat(workspace.created_at).strftime('%m/%d/%y')}", cls=TextPresets.muted_sm)
                                ),
                                DivLAligned(
                                    UkIcon("clock", height=14, width=14, cls="mr-1 text-muted-foreground"),
                                    Small(f"Updated {datetime.fromisoformat(workspace.updated_at).strftime('%m/%d/%y')}", cls=TextPresets.muted_sm)
                                ),
                                cls="space-x-4"
                            )
                        ),
                        hx_get=f"/content/workspace/{workspace.id}",
                        hx_target="#main-content",
                        cls=(CardT.hover, "cursor-pointer flex-1"),
                        title=f"Open {workspace.name}"
                    ),
                    Button(
                        UkIcon("trash-2", height=20, width=20),
                        hx_delete=f"/delete-workspace/{workspace.id}",
                        hx_target="closest div",
                        hx_swap="outerHTML",
                        hx_confirm="Are you sure you want to delete this workspace?",
                        cls=(ButtonT.destructive, "ml-4 p-3"),
                        title="Delete workspace",
                        _="on htmx:afterRequest if detail.successful then wait 10ms then set #workspaces-count's textContent to 'You have ' + document.querySelectorAll('#main-content .card').length + ' workspaces.' end"
                    ),
                    cls="mb-4 items-start"
                )
            )
    
    return Container(
        Section(
            H1("All Workspaces"),
            Subtitle(f"You have {len(user_workspaces)} workspace{'s' if len(user_workspaces) != 1 else ''}", id="workspaces-count"),
            cls=SectionT.default
        ),
        
        Section(
            DivRAligned(
                Button(
                    UkIcon("plus-circle", height=16, width=16, cls="mr-2"),
                    "Create New Workspace",
                    hx_get="/content/workspace",
                    hx_target="#main-content",
                    cls=ButtonT.primary
                )
            ),
            cls="mb-6"
        ),
        
        Section(
            *workspaces_content if workspaces_content else [
                Card(
                    CardBody(
                        Center(
                            DivVStacked(
                                UkIcon("folder-plus", height=48, width=48, cls="mx-auto text-muted-foreground mb-4"),
                                H4("No workspaces found"),
                                P("Create your first workspace to get started!", cls=TextPresets.muted_sm),
                                Button(
                                    UkIcon("plus-circle", height=16, width=16, cls="mr-2"),
                                    "Create Your First Workspace",
                                    hx_get="/content/workspace",
                                    hx_target="#main-content",
                                    cls=ButtonT.primary
                                ),
                                cls="text-center py-8"
                            )
                        )
                    ),
                    cls=CardT.default
                )
            ],
            cls=SectionT.default
        ),
        cls=ContainerT.lg
    )


@rt("/content/inputs")
def content_inputs(session):
    """Return all inputs content fragment"""
    auth = session.get("auth")
    user = users[auth]
    
    user_inputs = input_items(where=f"user_id = {user.id}")
    
    inputs_content = []
    if user_inputs:
        for input_item in user_inputs:
            inputs_content.append(build_input_item_fragment(input_item))
    else:
        inputs_content = [P("No input items available yet.")]
    
    return Div(
        H1("Input Items"),
        P(f"You have {len(user_inputs)} uploaded items.", id="inputs-count"),
        Div(*inputs_content, id="inputs-list"),
        Div(id="modal-container")
    )


@rt("/content/view-input/{input_id}")
def content_view_input(input_id: str, session):
    """Return view input content fragment"""
    auth = session.get("auth")
    user = users[auth]
    try:
        input_item = input_items[input_id]
        
        # Build transcription section based on file type and transcription status
        transcription_section = None
        if input_item.file_type == "audio":
            if input_item.transcription:
                # Show editable transcription input box
                transcription_section = Card(
                    CardHeader(H4("Transcription")),
                    CardBody(
                        TextArea(
                            input_item.transcription,
                            hx_put=f"/update-transcription/{input_item.id}",
                            hx_target="this",
                            hx_swap="none",
                            hx_trigger="keyup changed delay:500ms",
                            name="transcription",
                            placeholder="Transcription will appear here..."
                        )
                    ),
                    cls=CardT.default
                )
            else:
                # Show transcribe button
                transcription_section = Card(
                    CardHeader(H4("Transcription")),
                    CardBody(
                        P("This audio file has not been transcribed yet.", cls=TextPresets.muted_sm),
                        Button(
                            "Transcribe Audio",
                            hx_post=f"/transcribe-audio/{input_item.id}",
                            hx_target="closest div",
                            hx_swap="outerHTML",
                            cls=ButtonT.primary
                        )
                    ),
                    cls=CardT.default
                )
        elif input_item.transcription:
            # Non-audio files that somehow have transcription (legacy data)
            transcription_section = Card(
                CardHeader(H4("Transcription")),
                CardBody(P(input_item.transcription)),
                cls=CardT.default
            )
        
        # Image preview section for image files
        image_section = None
        if input_item.file_type == "image":
            image_section = Card(
                CardHeader(H4("Image Preview")), 
                CardBody(
                    Center(
                        Img(
                            src=f"uploads/images/{Path(input_item.file_path).name}",
                            alt=f"Preview of {input_item.original_filename}",
                            cls="max-w-full max-h-96 rounded-lg object-contain shadow-sm"
                        )
                    )
                ),
                cls=CardT.default
            )
        
        # Extracted data section
        extracted_section = None
        if input_item.extracted_data:
            # Parse JSON data to create form fields
            try:
                if input_item.extracted_data.startswith('{') or input_item.extracted_data.startswith('['):
                    import json
                    data = json.loads(input_item.extracted_data)
                    
                    form_fields = []
                    
                    # Equipment IDs field
                    equipment_ids = data.get("equipment_ids", [])
                    equipment_value = ", ".join(equipment_ids) if isinstance(equipment_ids, list) else str(equipment_ids)
                    form_fields.append(
                        LabelInput(
                            "Equipment IDs",
                            value=equipment_value,
                            placeholder="Enter equipment IDs separated by commas",
                            hx_put=f"/update-extracted-field/{input_item.id}/equipment_ids",
                            hx_target="this",
                            hx_swap="none",
                            hx_trigger="keyup changed delay:500ms",
                            name="equipment_ids",
                            id=f"equipment_ids_{input_item.id}"
                        )
                    )
                    
                    # Part Numbers field
                    part_numbers = data.get("part_numbers", [])
                    part_value = ", ".join(part_numbers) if isinstance(part_numbers, list) else str(part_numbers)
                    form_fields.append(
                        LabelInput(
                            "Part Numbers",
                            value=part_value,
                            placeholder="Enter part numbers separated by commas",
                            hx_put=f"/update-extracted-field/{input_item.id}/part_numbers",
                            hx_target="this",
                            hx_swap="none",
                            hx_trigger="keyup changed delay:500ms",
                            name="part_numbers",
                            id=f"part_numbers_{input_item.id}"
                        )
                    )
                    
                    # Defect Codes field
                    defect_codes = data.get("defect_codes", [])
                    defect_value = ", ".join(defect_codes) if isinstance(defect_codes, list) else str(defect_codes)
                    form_fields.append(
                        LabelInput(
                            "Defect Codes",
                            value=defect_value,
                            placeholder="Enter defect codes separated by commas",
                            hx_put=f"/update-extracted-field/{input_item.id}/defect_codes",
                            hx_target="this",
                            hx_swap="none",
                            hx_trigger="keyup changed delay:500ms",
                            name="defect_codes",
                            id=f"defect_codes_{input_item.id}"
                        )
                    )
                    
                    # Priority field
                    priority_options = ["", "Low", "Medium", "High", "Critical"]
                    current_priority = data.get("priority", "")
                    selected_idx = priority_options.index(current_priority) if current_priority in priority_options else 0
                    form_fields.append(
                        LabelSelect(
                            *Options(*priority_options, selected_idx=selected_idx),
                            label="Priority",
                            hx_put=f"/update-extracted-field/{input_item.id}/priority",
                            hx_target="this",
                            hx_swap="none",
                            hx_trigger="change delay:500ms",
                            name="priority",
                            id=f"priority_{input_item.id}"
                        )
                    )
                    
                    # Description field
                    description = data.get("description", "")
                    form_fields.append(
                        Div(
                            FormLabel("Description", fr=f"description_{input_item.id}"),
                            TextArea(
                                description,
                                placeholder="Enter maintenance description",
                                hx_put=f"/update-extracted-field/{input_item.id}/description",
                                hx_target="this",
                                hx_swap="none",
                                hx_trigger="keyup changed delay:500ms",
                                name="description",
                                id=f"description_{input_item.id}",
                                rows=3
                            )
                        )
                    )
                    
                    extracted_section = Card(
                        CardHeader(
                            H4("Extracted Data"),
                            Small("Edit the extracted maintenance information", cls=TextPresets.muted_sm)
                        ),
                        CardBody(
                            Form(*form_fields, cls="space-y-4")
                        ),
                        cls=CardT.default
                    )
                else:
                    # Non-JSON data - show as textarea
                    extracted_section = Card(
                        CardHeader(H4("Extracted Data")),
                        CardBody(
                            TextArea(
                                input_item.extracted_data,
                                hx_put=f"/update-extracted-data/{input_item.id}",
                                hx_target="this",
                                hx_swap="none",
                                hx_trigger="keyup changed delay:500ms",
                                name="extracted_data",
                                placeholder="Extracted data will appear here...",
                                rows=6
                            )
                        ),
                        cls=CardT.default
                    )
            except:
                # Fallback for invalid JSON
                extracted_section = Card(
                    CardHeader(H4("Extracted Data")),
                    CardBody(
                        TextArea(
                            input_item.extracted_data,
                            hx_put=f"/update-extracted-data/{input_item.id}",
                            hx_target="this",
                            hx_swap="none",
                            hx_trigger="keyup changed delay:500ms",
                            name="extracted_data",
                            placeholder="Extracted data will appear here...",
                            rows=6
                        )
                    ),
                    cls=CardT.default
                )
        
        return Container(
            Section(
                H1("Input Item Details"),
                Subtitle(f"Viewing details for {input_item.original_filename}"),
                cls=SectionT.default
            ),
            Section(
                Card(
                    CardHeader(
                        H3(input_item.original_filename),
                        Small(datetime.fromisoformat(input_item.uploaded_at).strftime('%Y-%m-%d %H:%M:%S'), cls=TextPresets.muted_sm)
                    ),
                    CardBody(
                        Grid(
                            Div(
                                Strong("File Type", cls=TextT.medium),
                                P(input_item.file_type.title(), cls=TextPresets.muted_sm)
                            ),
                            Div(
                                Strong("File Size", cls=TextT.medium), 
                                P(f"{(input_item.file_size / 1024):.1f} KB", cls=TextPresets.muted_sm)
                            ),
                            Div(
                                Strong("Status", cls=TextT.medium),
                                P("Processed" if input_item.processed else "Pending", 
                                  cls=f"{TextPresets.muted_sm} {'text-green-600' if input_item.processed else 'text-orange-600'}")
                            ),
                            cols=3, cls="gap-6"
                        )
                    ),
                    cls=CardT.default
                ),
                cls=SectionT.default
            ),
            *([Section(image_section, cls=SectionT.default)] if image_section else []),
            *([Section(transcription_section, cls=SectionT.default)] if transcription_section else []),
            *([Section(extracted_section, cls=SectionT.default)] if extracted_section else []),
            cls=ContainerT.lg,
            id=f"input-item-view-{input_id}"
        )
    except:
        return Container(
            Section(
                Alert("Input item not found", cls=AlertT.error),
                cls=SectionT.default
            ),
            cls=ContainerT.lg
        )


@rt("/content/view-report/{report_id}")
def content_view_report(report_id: str, session):
    """Return view report content fragment"""
    auth = session.get("auth")
    user = users[auth]
    try:
        report = maintenance_reports[report_id]

        return Container(
            Section(
                H1("Maintenance Report"),
                cls=SectionT.default
            ),
            Card(
                CardBody(
                    Div(
                        H2(report.title),
                        P(Strong("Description: "), report.description),
                        P(Strong("Equipment ID: "), report.equipment_id),
                        P(
                            Strong("Priority: "),
                            Span(
                                report.priority.title(),
                            ),
                        ),
                        P(
                            Strong("Part Numbers: "),
                            ", ".join(json.loads(report.part_numbers or "[]")),
                        ),
                        P(
                            Strong("Defect Codes: "),
                            ", ".join(json.loads(report.defect_codes or "[]")),
                        ),
                        P(Strong("Corrective Action: "), report.corrective_action),
                        P(
                            Strong("Parts Used: "),
                            ", ".join(json.loads(report.parts_used or "[]")),
                        ),
                        P(
                            Strong("Next Service Date: "),
                            (
                                report.next_service_date.split("T")[0]
                                if report.next_service_date
                                else "N/A"
                            ),
                        ),
                        P(Strong("Status: "), report.status.title()),
                        Button(
                            "Edit Report",
                            hx_get=f"/content/edit-report/{report_id}",
                            hx_target="#main-content",
                            cls=ButtonT.primary,
                        ),
                        cls="space-y-3",
                        style="text-align: left;"
                    )
                ),
                cls=CardT.default
            ),
            cls=ContainerT.lg
        )
    except:
        return Div("Report not found")


@rt("/content/edit-report/{report_id}")
def content_edit_report(report_id: str, session):
    """Return edit report content fragment"""
    auth = session.get("auth")
    user = users[auth]
    try:
        report = maintenance_reports[report_id]

        return Container(
            Section(
                H1("Edit Maintenance Report"),
                cls=SectionT.default
            ),
            Card(
                CardBody(
                    Form(
                        hx_post=f"/update-report-content/{report_id}", hx_target="#main-content"
                    )(
                        Div(
                            Label("Title", cls="font-medium text-sm text-gray-500 mb-1"),
                            Input(name="title", value=report.title, required=True),
                            cls="space-y-2"
                        ),
                        Div(
                            Label("Description", cls="font-medium text-sm text-gray-500 mb-1"),
                            Textarea(
                                name="description",
                                rows=4,
                                placeholder="Detailed problem description",
                                cls="w-full"
                            )(report.description),
                            cls="space-y-2"
                        ),
                        Div(
                            Label("Equipment ID", cls="font-medium text-sm text-gray-500 mb-1"),
                            Input(name="equipment_id", value=report.equipment_id, cls="w-full"),
                            cls="space-y-2"
                        ),
                        Div(
                            Label("Priority", cls="font-medium text-sm text-gray-500 mb-1"),
                            Select(
                                Option("Low", value="low", selected="low" == report.priority),
                                Option("Medium", value="medium", selected="medium" == report.priority),
                                Option("High", value="high", selected="high" == report.priority),
                                Option("Critical", value="critical", selected="critical" == report.priority),
                                name="priority", cls="w-full"
                            ),
                            cls="space-y-2"
                        ),
                        Div(
                            Label("Part Numbers (comma-separated)", cls="font-medium text-sm text-gray-500 mb-1"),
                            Input(
                                name="part_numbers",
                                value=", ".join(json.loads(report.part_numbers) if report.part_numbers else []),
                                cls="w-full"
                            ),
                            cls="space-y-2"
                        ),
                        Div(
                            Label("Defect Codes (comma-separated)", cls="font-medium text-sm text-gray-500 mb-1"),
                            Input(
                                name="defect_codes",
                                value=", ".join(json.loads(report.defect_codes) if report.defect_codes else []),
                                cls="w-full"
                            ),
                            cls="space-y-2"
                        ),
                        Div(
                            Label("Corrective Action", cls="font-medium text-sm text-gray-500 mb-1"),
                            Textarea(
                                name="corrective_action",
                                rows=4,
                                placeholder="Recommended actions",
                                cls="w-full"
                            )(report.corrective_action),
                            cls="space-y-2"
                        ),
                        Div(
                            Label("Parts Used (comma-separated)", cls="font-medium text-sm text-gray-500 mb-1"),
                            Input(
                                name="parts_used",
                                value=", ".join(json.loads(report.parts_used) if report.parts_used else []),
                                cls="w-full"
                            ),
                            cls="space-y-2"
                        ),
                        Div(
                            Label("Next Service Date", cls="font-medium text-sm text-gray-500 mb-1"),
                            Input(
                                name="next_service_date",
                                type="date",
                                value=(
                                    report.next_service_date.split("T")[0]
                                    if report.next_service_date
                                    else ""
                                ),
                                cls="w-full"
                            ),
                            cls="space-y-2"
                        ),
                        Div(
                            Button("Save Changes", type="submit", cls=ButtonT.primary),
                            Button(
                                "Cancel",
                                hx_get=f"/content/view-report/{report_id}",
                                hx_target="#main-content",
                                cls=ButtonT.secondary
                            ),
                            cls="space-x-3 pt-4"
                        ),
                    )
                ),
                cls=CardT.default
            ),
            cls=ContainerT.lg
        )
    except:
        return Div("Report not found")

@rt("/content/generate-report")
async def content_generate_report(workspace_id: str, session):
    """Generate a maintenance report from workspace items and return content fragment"""
    auth = session.get("auth")
    user = users[auth]
    workspace = workspaces[workspace_id]
    item_ids = json.loads(workspace.input_item_ids or "[]")
    
    if not item_ids:
        items = []
    else:
        item_ids_str = "', '".join(item_ids)
        items = input_items(where=f"id IN ('{item_ids_str}')")

    if not items:
        return Div(
            H1("Report Generation Failed"),
            P("No items found in workspace to generate report from."),
            Button(
                "Back to Workspace",
                hx_get="/content/workspace",
                hx_target="#main-content",
                cls=ButtonT.primary,
            ),
        )

    await process_items(workspace_id, session)

    workspace = workspaces[workspace_id]
    item_ids = json.loads(workspace.input_item_ids or "[]")
    
    if not item_ids:
        items = []
    else:
        item_ids_str = "', '".join(item_ids)
        items = input_items(where=f"id IN ('{item_ids_str}')")

    items_data = []
    for item in items:
        items_data.append(
            {
                "filename": item.original_filename,
                "type": item.file_type,
                "transcription": item.transcription,
                "extracted_data": item.extracted_data,
            }
        )

    report_data = await generate_maintenance_report(items_data)

    if "error" in report_data:
        return Div(
            H1("Report Generation Failed"),
            P(f"Error: {report_data['error']}"),
            Button(
                "Back to Workspace",
                hx_get="/content/workspace",
                hx_target="#main-content",
                cls=ButtonT.primary,
            ),
        )

    report_id = generate_uuid()
    maintenance_reports.insert(
        MaintenanceReport(
            id=report_id,
            workspace_id=workspace_id,
            user_id=user.id,
            title=report_data.get("title", "Generated Maintenance Report"),
            description=report_data.get("description", ""),
            equipment_id=report_data.get("equipment_id", ""),
            part_numbers=json.dumps(report_data.get("part_numbers", [])),
            defect_codes=json.dumps(report_data.get("defect_codes", [])),
            corrective_action=report_data.get("corrective_action", ""),
            parts_used=json.dumps(report_data.get("parts_used", [])),
            next_service_date=report_data.get("next_service_date", ""),
            priority=report_data.get("priority", "medium"),
            status="open",
            created_at=get_current_timestamp(),
            updated_at=get_current_timestamp(),
            finalized=False,
        )
    )

    main_content = Div(
        H1("Generated Maintenance Report"),
        Div(
            H2(report_data.get("title", "Maintenance Report")),
            P(Strong("Description: "), report_data.get("description", "N/A")),
            P(Strong("Equipment ID: "), report_data.get("equipment_id", "N/A")),
            P(
                Strong("Priority: "),
                Span(
                    report_data.get("priority", "medium").title(),
                ),
            ),
            P(Strong("Part Numbers: "), ", ".join(report_data.get("part_numbers", []))),
            P(Strong("Defect Codes: "), ", ".join(report_data.get("defect_codes", []))),
            P(
                Strong("Corrective Action: "),
                report_data.get("corrective_action", "N/A"),
            ),
            P(Strong("Parts Used: "), ", ".join(report_data.get("parts_used", []))),
            P(
                Strong("Next Service Date: "),
                report_data.get("next_service_date", "N/A"),
            ),
            cls="report-section",
        ),
        Div(
            Button(
                "Edit Report",
                hx_get=f"/content/edit-report/{report_id}",
                hx_target="#main-content",
                cls=ButtonT.primary,
            ),
        ),
    )

    recent_reports_update = create_recent_reports_section(user.id, swap_oob=True)
    dashboard_stats_update = create_dashboard_stats_section(user.id, swap_oob=True)

    return main_content, recent_reports_update, dashboard_stats_update


@rt("/update-report-content/{report_id}")
async def update_report_content(report_id:str, session, request):
    auth = session.get("auth")
    user = users[auth]
    
    # Parse form data
    form_data = await request.form()
    title = form_data.get("title", "")
    description = form_data.get("description", "")
    equipment_id = form_data.get("equipment_id", "")
    priority = form_data.get("priority", "")
    part_numbers = form_data.get("part_numbers", "")
    defect_codes = form_data.get("defect_codes", "")
    corrective_action = form_data.get("corrective_action", "")
    parts_used = form_data.get("parts_used", "")
    next_service_date = form_data.get("next_service_date", "")
    
    # Debug: print the received priority value
    print(f"DEBUG: Received priority value: '{priority}' (type: {type(priority)})")
    
    try:
        part_numbers_list = [p.strip() for p in part_numbers.split(",") if p.strip()]
        defect_codes_list = [d.strip() for d in defect_codes.split(",") if d.strip()]
        parts_used_list = [p.strip() for p in parts_used.split(",") if p.strip()]

        maintenance_reports.update(
            {
                "title": title,
                "description": description,
                "equipment_id": equipment_id,
                "priority": priority,
                "part_numbers": json.dumps(part_numbers_list),
                "defect_codes": json.dumps(defect_codes_list),
                "corrective_action": corrective_action,
                "parts_used": json.dumps(parts_used_list),
                "next_service_date": (
                    next_service_date + "T00:00:00" if next_service_date else ""
                ),
                "updated_at": get_current_timestamp(),
            },
            report_id,
        )

        main_content = content_view_report(report_id, session)
        recent_reports_update = create_recent_reports_section(user.id, swap_oob=True)
        dashboard_stats_update = create_dashboard_stats_section(user.id, swap_oob=True)

        return main_content, recent_reports_update, dashboard_stats_update

    except Exception as e:
        return Div(f"Error updating report: {str(e)}")

@rt("/remove-from-workspace/{workspace_id}/{input_id}", methods=["DELETE"])
def remove_from_workspace(workspace_id: str, input_id: str, session):
    """Remove an input item from a workspace without deleting the item"""
    auth = session.get("auth")
    user = users[auth]
    
    try:
        workspace = workspaces[workspace_id]
        if workspace.user_id != user.id: return Div("Unauthorized")
        
        # Remove item from workspace
        item_ids = json.loads(workspace.input_item_ids or "[]")
        if input_id in item_ids:
            item_ids.remove(input_id)
            workspaces.update({"input_item_ids": json.dumps(item_ids)}, workspace_id)
        
        # Rebuild the entire ingested-items div with remaining items
        updated_workspace = workspaces[workspace_id]
        all_item_ids = json.loads(updated_workspace.input_item_ids or "[]")
        all_items = []
        if all_item_ids:
            item_ids_str = "', '".join(all_item_ids)
            all_items = input_items(where=f"id IN ('{item_ids_str}')")
        
        # Create the updated ingested-items div
        items_content = []
        for workspace_item in all_items:
            items_content.append(build_input_item_fragment(workspace_item, workspace_id))
        
        updated_ingested_items = Div(
            *items_content if items_content else [P("No items added yet.", cls=(TextPresets.muted_sm, "italic"))],
            id="ingested-items",
            _="on htmx:afterSwap if .input-item-article in me then remove @disabled from #generate-btn else add @disabled to #generate-btn",
            hx_swap_oob="true"
        )
        
        return updated_ingested_items
        
    except Exception as e: 
        return Div(f"Error removing item from workspace: {str(e)}")

@rt("/delete-input/{input_id}", methods=["DELETE"])
def delete_input(input_id: str, session):
    auth = session.get("auth")
    user = users[auth]
    
    try:
        input_item = input_items[input_id]
        if input_item.user_id != user.id: return Div("Unauthorized")
        
        try:
            import os
            if os.path.exists(input_item.file_path):
                os.remove(input_item.file_path)
        except Exception as e: print(f"Failed to delete file {input_item.file_path}: {e}")
        
        user_workspaces = workspaces(where=f"user_id = {user.id}")
        for workspace in user_workspaces:
            item_ids = json.loads(workspace.input_item_ids or "[]")
            if input_id in item_ids:
                item_ids.remove(input_id)
                workspaces.update({"input_item_ids": json.dumps(item_ids)}, workspace.id)
        
        input_items.delete(input_id)
        return create_recent_uploads_section(user.id, swap_oob=True)
    except Exception as e: return Div(f"Error deleting input: {str(e)}")


@rt("/update-workspace/{workspace_id}", methods=["PUT"])
def update_workspace(workspace_id: str, session, updates: dict):
    auth = session.get("auth")
    user = users[auth]
    
    try:
        workspace = workspaces[workspace_id]
        if workspace.user_id != user.id:
            return Alert("Unauthorized", cls=AlertT.error)
        
        # Always update the timestamp
        updates["updated_at"] = get_current_timestamp()
        
        # Update the workspace
        workspaces.update(updates, workspace_id)
        
        # Return updated sidebar sections
        recent_workspaces_update = create_recent_workspaces_section(user.id, swap_oob=True)
        return recent_workspaces_update
        
    except Exception as e:
        return Div(f"Error updating workspace: {str(e)}")


@rt("/delete-workspace/{workspace_id}", methods=["DELETE"])
def delete_workspace(workspace_id: str, session, source: str = None):
    auth = session.get("auth")
    user = users[auth]
    
    try:
        workspace = workspaces[workspace_id]
        if workspace.user_id != user.id:
            return Alert("Unauthorized", cls=AlertT.error)
        
        
        # Delete the workspace
        workspaces.delete(workspace_id)
        
        # Return updated sidebar sections
        recent_workspaces_update = create_recent_workspaces_section(user.id, swap_oob=True)
        if source and source == "workspace":
            main_content = content_workspaces(session)
            return main_content, recent_workspaces_update
        return recent_workspaces_update
        
    except Exception as e:
        return Div(f"Error deleting workspace: {str(e)}")

@rt("/logout")
def logout(session):
    session.clear()
    return RedirectResponse("/", status_code=303)

serve()