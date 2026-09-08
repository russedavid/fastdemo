(() => {
    // FastHTML's htmx4 adapter uses '-' for event/attribute modifiers.
    const eventName = name => name.replaceAll(':', htmx.config.metaCharacter || ':');
    const onHtmx = (name, handler) => document.addEventListener(eventName(name), handler);

    function syncWorkspaceControls() {
        const button = document.getElementById('generate-btn');
        const items = document.getElementById('ingested-items');
        if (button && items) button.disabled = !items.querySelector('.input-item-article');

        const count = document.getElementById('workspaces-count');
        if (count) {
            const total = document.querySelectorAll('#main-content [data-workspace-card]').length;
            count.textContent = `You have ${total} workspace${total === 1 ? '' : 's'}`;
        }
    }

    function initialize(root) {
        // Hyperscript's built-in htmx hook targets the older htmx:load event.
        if (window._hyperscript) window._hyperscript.processNode(root);
        syncWorkspaceControls();
    }

    htmx.onLoad(initialize);
    document.addEventListener('DOMContentLoaded', () => initialize(document.body));
    onHtmx('htmx:after:swap', syncWorkspaceControls);

    function setUploadBusy(event, busy) {
        const source = event.detail.ctx?.sourceElement || event.target;
        const form = source instanceof Element ? source.closest('#file-upload-form') : null;
        if (!form) return;
        const progress = form.querySelector('#upload-progress');
        if (progress) progress.hidden = !busy;
        form.setAttribute('aria-busy', String(busy));
    }
    onHtmx('htmx:before:request', event => setUploadBusy(event, true));
    onHtmx('htmx:finally:request', event => setUploadBusy(event, false));
    onHtmx('htmx:response:error', event => {
        const message = document.getElementById('app-messages');
        if (message) {
            const status = event.detail.ctx?.response?.status;
            message.textContent = status === 413
                ? 'Upload too large. Use files up to 4 MB, at most two at a time.'
                : 'This request could not be completed. Your saved workspace is still available.';
            message.setAttribute('role', 'alert');
        }
    });
    document.addEventListener('change', event => {
        if (event.target.id !== 'workspace-files') return;
        const files = [...(event.target.files || [])];
        if (files.length <= 2 && files.every(file => file.size <= 4 * 1024 * 1024)) return;
        event.stopImmediatePropagation();
        event.target.value = '';
        const message = document.getElementById('app-messages');
        if (message) message.textContent = 'Choose at most two files, up to 4 MB each.';
    }, true);

    onHtmx('htmx:before:swap', event => {
        const replacesRecorder = (event.detail.tasks || []).some(
            task => task.target instanceof Element && task.target.contains(window.startBtn)
        );
        if (window.mediaRecorder?.state === 'recording' && replacesRecorder) {
            window.discarding = true;
            window.mediaRecorder.stop();
            if (window.startBtn) window.startBtn.disabled = false;
            if (window.stopBtn) window.stopBtn.disabled = true;
            if (window.recordingStatusElement) window.recordingStatusElement.textContent = '';
        }
    });

    const uploadZone = event => event.target instanceof Element
        ? event.target.closest('[data-upload-zone]') : null;
    document.addEventListener('dragover', event => {
        const zone = uploadZone(event);
        if (!zone) return;
        event.preventDefault();
        zone.classList.add('dragover');
    });
    document.addEventListener('dragleave', event => {
        const zone = uploadZone(event);
        if (zone && !zone.contains(event.relatedTarget)) zone.classList.remove('dragover');
    });
    document.addEventListener('drop', event => {
        const zone = uploadZone(event);
        if (!zone) return;
        event.preventDefault();
        zone.classList.remove('dragover');
        const input = zone.querySelector('input[type="file"]');
        if (input && event.dataTransfer?.files.length) {
            input.files = event.dataTransfer.files;
            input.dispatchEvent(new Event('change', {bubbles: true}));
        }
    });
})();
