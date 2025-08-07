css = '''
/* Essential custom styles that cannot be replaced with MonsterUI */

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
'''