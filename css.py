css = """
/* Warm light palette shared by MonsterUI/FrankenUI and its DaisyUI components. */
html.frontline-theme {
    color-scheme: light;
    --background: 36 44% 94%;
    --foreground: 28 26% 22%;
    --card: 38 63% 98%;
    --card-foreground: 28 26% 22%;
    --popover: 38 63% 98%;
    --popover-foreground: 28 26% 22%;
    --primary: 28 34% 36%;
    --primary-foreground: 38 60% 97%;
    --secondary: 35 38% 84%;
    --secondary-foreground: 27 27% 25%;
    --muted: 35 31% 89%;
    --muted-foreground: 28 17% 39%;
    --accent: 32 40% 86%;
    --accent-foreground: 28 32% 25%;
    --border: 33 25% 76%;
    --input: 33 25% 76%;
    --ring: 28 34% 42%;
    --destructive: 10 51% 40%;
    --destructive-foreground: 38 60% 97%;
    --chart-1: 28 34% 36%;
    --chart-2: 35 38% 60%;
    --chart-3: 23 29% 48%;
    --chart-4: 40 30% 72%;
    --chart-5: 18 22% 39%;
}

body {
    background: hsl(var(--background));
    color: hsl(var(--foreground));
    min-height: 100vh;
}

html.frontline-theme [hidden] { display: none !important; }

.uk-card {
    background: hsl(var(--card));
    border-color: hsl(var(--border));
    box-shadow: 0 2px 8px hsl(28 26% 22% / 0.035);
}

#main-content > .uk-container > .uk-card { margin-bottom: 1rem; }

#sidebar {
    background: hsl(35 34% 88%);
    border-color: hsl(var(--border));
}

.uk-navbar-container, .monster-navbar {
    background: hsl(var(--secondary));
    border-color: hsl(var(--border));
}

.status-active {
    background: hsl(var(--accent));
    color: hsl(var(--accent-foreground));
}

input, textarea, select, progress { accent-color: hsl(var(--primary)); }

.js-upload {
    background: hsl(var(--card));
    border-color: hsl(var(--border));
    border-radius: 0.75rem;
    transition: background-color 0.15s, border-color 0.15s;
}

.js-upload:hover { background: hsl(var(--accent) / 0.45); }

/* Drag and drop styling for file upload */
.dragover {
    border-color: hsl(var(--primary)) !important;
    background-color: hsl(var(--primary) / 0.1) !important;
}

/* Audio playback initially hidden */
.audio-playback {
    display: none;
}

/* Upload progress initially hidden */
.upload-progress {
    display: none;
}

/* HTMX indicators */
.htmx-indicator {
    opacity: 0;
    transition: opacity 0.3s ease-in-out;
}

.htmx-request .htmx-indicator {
    opacity: 1;
}

/* Content preview hover effect for transcription editing */
.content-preview {
    cursor: pointer;
    font-style: italic;
    padding: 0.25rem;
    border-radius: 0.25rem;
    transition: background-color 0.2s;
}

.content-preview:hover {
    background-color: hsl(var(--muted));
}

/* Image modal specific styling */
.img-modal {
    max-width: 100%;
    max-height: 300px;
    border: 2px solid hsl(var(--border));
    border-radius: 0.5rem;
}

/* Mobile sidebar transitions */
#sidebar {
    transition: transform 0.3s ease-in-out;
}

@media (max-width: 768px) {
    #sidebar:not(.hidden) {
        transform: translateX(0);
    }
    
    #sidebar.hidden {
        transform: translateX(-100%);
    }
}
"""

css += """
.demo-intro { max-width: 46rem; margin: clamp(2rem, 8vh, 6rem) auto; }
.demo-intro h1 { font-size: clamp(2rem, 4vw, 3.25rem); line-height: 1.12; }
.source-text { white-space: pre-wrap; overflow-wrap: anywhere; font-family: inherit; line-height: 1.65; max-width: 100%; }
.source-panel { border: 1px solid #d9caba; border-radius: .5rem; margin: 1rem 0; padding: 1rem; }
.source-panel summary { cursor: pointer; font-weight: 600; margin-bottom: .5rem; }
.source-citation { color: #765438; text-decoration: underline; font-weight: 600; padding: 0 .15rem; }
#app-messages:not(:empty) { background: #f2e5d3; border: 1px solid #d9caba; padding: .8rem 1rem; margin-bottom: 1rem; border-radius: .5rem; }
"""
