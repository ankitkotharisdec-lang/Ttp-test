(() => {
    const root = document.querySelector('[data-reading-tools]');
    if (!root) return;

    const signedIn = root.dataset.signedIn === '1';
    const bookmarkToggle = root.querySelector('[data-bookmark-toggle]');
    const selectionButton = root.querySelector('[data-highlight-selection]');
    const status = root.querySelector('[data-reading-status]');
    const lessonID = root.dataset.lessonId;
    const storageKey = 'step2success:annotations:' + root.dataset.course;
    const blocks = new Map(Array.from(document.querySelectorAll('[data-annotation-block]'),
        block => [block.dataset.annotationBlock, block]));
    const maxQuote = 3000;
    const maxSelections = 16;
    const nativeHighlights = window.Highlight && window.CSS?.highlights;
    let state = { saved: false, highlights: [] };
    let selection = [];
    let loaded = false;
    let pending = false;
    let bookmarkRequest = 0;

    function announce(message) {
        status.textContent = message;
        status.hidden = !message;
    }

    function readLocal() {
        const data = JSON.parse(localStorage.getItem(storageKey) || '{}');
        return { bookmarks: data.bookmarks || [], highlights: data.highlights || {} };
    }

    function lessonLocal(data) {
        return {
            saved: data.bookmarks.some(bookmark => bookmark.id === lessonID),
            highlights: data.highlights[lessonID] || [],
        };
    }

    async function request(url, data) {
        const options = { credentials: 'same-origin' };
        if (data) {
            options.method = 'POST';
            options.headers = { 'Content-Type': 'application/json', 'X-CSRFToken': root.dataset.csrf };
            options.body = JSON.stringify(data);
        }
        const response = await fetch(url, options);
        if (response.status === 401) {
            throw new Error('Your session expired. Reload the page and sign in again.');
        }
        if (!response.ok) throw new Error('Could not load or save your reading tools. Please try again.');
        return response.json();
    }

    function count(selector, amount) {
        root.querySelector(selector).textContent = amount ? '(' + amount + ')' : '';
    }

    function renderBookmarks(bookmarks) {
        const list = root.querySelector('[data-saved-bookmarks]');
        list.replaceChildren();
        for (const bookmark of bookmarks) {
            if (!/^\/lessons\/[a-f0-9-]{36}\/$/i.test(bookmark.url)) continue;
            const item = document.createElement('li');
            const link = document.createElement('a');
            const chapter = document.createElement('small');
            link.href = bookmark.url;
            link.textContent = bookmark.title;
            chapter.textContent = bookmark.chapter;
            link.append(chapter);
            item.append(link);
            list.append(item);
        }
        root.querySelector('[data-no-bookmarks]').hidden = !!list.childElementCount;
        count('[data-bookmark-count]', list.childElementCount);
    }

    async function refreshBookmarks() {
        const version = ++bookmarkRequest;
        const data = signedIn ? await request(root.dataset.bookmarksUrl) : readLocal();
        if (version === bookmarkRequest) renderBookmarks(data.bookmarks);
    }

    if (!lessonID) {
        refreshBookmarks().catch(error => announce(error.message));
        return;
    }

    const floating = document.createElement('button');
    floating.type = 'button';
    floating.className = 'reading-highlight-action';
    floating.textContent = 'Highlight selection';
    floating.hidden = true;
    floating.tabIndex = -1;
    document.body.append(floating);

    function textRange(block, start, end) {
        const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT);
        let node, offset = 0, hasStart = false;
        const range = document.createRange();
        while ((node = walker.nextNode())) {
            const next = offset + node.length;
            if (!hasStart && start < next) {
                range.setStart(node, start - offset);
                hasStart = true;
            }
            if (hasStart && end <= next) {
                range.setEnd(node, end - offset);
                return range;
            }
            offset = next;
        }
        return null;
    }

    function locate(highlight) {
        const block = blocks.get(highlight.block);
        if (!block) return null;
        const text = block.textContent;
        let start = highlight.start;
        if (text.slice(start, highlight.end) !== highlight.quote) {
            start = text.indexOf(highlight.quote);
            if (start < 0 || start !== text.lastIndexOf(highlight.quote)) return null;
        }
        return {
            block,
            start,
            end: start + highlight.quote.length,
            range: textRange(block, start, start + highlight.quote.length),
        };
    }

    function paintFallback(locations) {
        // Paint by text node so an inline code tag or a paragraph stays structurally intact.
        const rangesByNode = new Map();
        for (const { block, start, end } of locations) {
            const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT);
            let node, offset = 0;
            while ((node = walker.nextNode()) && offset < end) {
                const next = offset + node.length;
                if (start < next) {
                    const ranges = rangesByNode.get(node) || [];
                    ranges.push([Math.max(0, start - offset), Math.min(node.length, end - offset)]);
                    rangesByNode.set(node, ranges);
                }
                offset = next;
            }
        }
        for (const [node, ranges] of rangesByNode) {
            const fragment = document.createDocumentFragment();
            const text = node.textContent;
            const merged = [];
            ranges.sort((a, b) => a[0] - b[0]);
            for (const range of ranges) {
                const previous = merged[merged.length - 1];
                if (previous && range[0] <= previous[1]) previous[1] = Math.max(previous[1], range[1]);
                else merged.push(range);
            }
            let offset = 0;
            for (const [start, end] of merged) {
                fragment.append(text.slice(offset, start));
                const mark = document.createElement('mark');
                mark.className = 'saved-passage';
                mark.textContent = text.slice(start, end);
                fragment.append(mark);
                offset = end;
            }
            fragment.append(text.slice(offset));
            node.replaceWith(fragment);
        }
    }

    function renderHighlights() {
        const list = root.querySelector('[data-saved-highlights]');
        list.replaceChildren();
        if (!nativeHighlights) {
            for (const block of blocks.values()) {
                const marks = block.querySelectorAll('mark.saved-passage');
                marks.forEach(mark => mark.replaceWith(...mark.childNodes));
                if (marks.length) block.normalize();
            }
        }
        const locations = [];
        for (const highlight of state.highlights) {
            const location = locate(highlight);
            const item = document.createElement('li');
            const jump = document.createElement('button');
            const remove = document.createElement('button');
            jump.type = remove.type = 'button';
            jump.dataset.jumpHighlight = '';
            jump.textContent = highlight.quote;
            jump.disabled = !location?.range;
            if (location?.range) {
                locations.push(location);
                jump.addEventListener('click', () => {
                    const current = locate(highlight);
                    if (!current?.range) return;
                    list.closest('details').open = false;
                    const position = current.range.getBoundingClientRect();
                    window.scrollBy({ top: position.top - Math.max(100, window.innerHeight / 3) });
                });
            } else {
                const note = document.createElement('small');
                note.textContent = 'Passage moved or changed.';
                jump.append(note);
            }
            remove.dataset.removeHighlight = highlight.id;
            remove.textContent = 'Remove';
            remove.setAttribute('aria-label', 'Remove highlight “' + highlight.quote.slice(0, 60) + '”');
            item.append(jump, remove);
            list.append(item);
        }
        if (nativeHighlights) {
            CSS.highlights.set('saved-passage', new Highlight(...locations.map(location => location.range)));
        } else {
            paintFallback(locations);
        }
        root.querySelector('[data-no-highlights]').hidden = !!state.highlights.length;
        count('[data-highlight-count]', state.highlights.length);
    }

    function applyLocal(action) {
        const data = readLocal();
        const local = lessonLocal(data);
        if (action.action === 'bookmark') {
            data.bookmarks = data.bookmarks.filter(bookmark => bookmark.id !== lessonID);
            if (action.saved) data.bookmarks.unshift({
                id: lessonID,
                title: root.dataset.lessonTitle,
                chapter: root.dataset.chapterTitle,
                url: root.dataset.lessonUrl,
            });
        } else if (action.action === 'highlight') {
            for (const part of action.selections) {
                const existing = local.highlights.some(item =>
                    item.block === part.block && item.start === part.start &&
                    item.end === part.end && item.quote === part.quote);
                if (!existing) {
                    const id = Array.from(crypto.getRandomValues(new Uint32Array(4))).join('-');
                    local.highlights.unshift({ ...part, id });
                }
            }
            data.highlights[lessonID] = local.highlights;
        } else {
            data.highlights[lessonID] = local.highlights.filter(item => item.id !== action.id);
        }
        localStorage.setItem(storageKey, JSON.stringify(data));
        return lessonLocal(data);
    }

    async function save(action, message) {
        if (!loaded || pending) return;
        pending = true;
        updateControls();
        try {
            state = signedIn ? await request(root.dataset.annotationUrl, action) : applyLocal(action);
            if (action.action === 'highlight') {
                window.getSelection()?.removeAllRanges();
                selection = [];
                floating.hidden = true;
            }
            renderHighlights();
            announce(message);
            if (action.action === 'bookmark') await refreshBookmarks();
        } catch (error) {
            announce(error.message);
        } finally {
            pending = false;
            updateControls();
        }
    }

    function updateControls() {
        bookmarkToggle.disabled = !loaded || pending;
        bookmarkToggle.textContent = state.saved ? 'Bookmarked' : 'Bookmark lesson';
        bookmarkToggle.setAttribute('aria-pressed', state.saved);
        bookmarkToggle.title = state.saved ? 'Remove bookmark' : 'Save this lesson for later';
        selectionButton.disabled = floating.disabled = !loaded || pending || !selection.length;
        root.querySelectorAll('[data-remove-highlight]').forEach(button => {
            button.disabled = pending;
        });
    }

    function selectionOffset(block, node, offset, fallback) {
        if (!block.contains(node)) return fallback;
        const prefix = document.createRange();
        prefix.selectNodeContents(block);
        prefix.setEnd(node, offset);
        return prefix.toString().length;
    }

    function updateSelection() {
        const selected = window.getSelection();
        selection = [];
        floating.hidden = true;
        if (!loaded || !selected?.rangeCount || selected.isCollapsed) {
            updateControls();
            return;
        }
        const range = selected.getRangeAt(0);
        for (const [key, block] of blocks) {
            if (!range.intersectsNode(block)) continue;
            const text = block.textContent;
            let start = selectionOffset(block, range.startContainer, range.startOffset, 0);
            const end = selectionOffset(block, range.endContainer, range.endOffset, text.length);
            const raw = text.slice(start, end);
            const quote = raw.trim();
            if (!quote) continue;
            start += raw.length - raw.trimStart().length;
            selection.push({ block: key, start, end: start + quote.length, quote });
        }

        if (selection.length) {
            const box = range.getBoundingClientRect();
            if (box.bottom >= 0 && box.top < window.innerHeight && !pending) {
                floating.hidden = false;
                const left = Math.max(8, Math.min(box.left, window.innerWidth - floating.offsetWidth - 8));
                const above = box.top - floating.offsetHeight - 8;
                const below = Math.min(window.innerHeight - floating.offsetHeight - 8, box.bottom + 8);
                floating.style.left = left + 'px';
                floating.style.top = (above >= 8 ? above : below) + 'px';
            }
        }
        updateControls();
    }

    function saveSelection() {
        if (!selection.length) return;
        if (selection.length > maxSelections || selection.some(part => part.quote.length > maxQuote)) {
            announce('Select a shorter passage to highlight.');
            return;
        }
        save({ action: 'highlight', selections: selection }, 'Highlight saved.');
    }

    for (const button of [selectionButton, floating]) {
        button.addEventListener('pointerdown', event => event.preventDefault());
        button.addEventListener('click', saveSelection);
    }
    bookmarkToggle.addEventListener('click', () => {
        save({ action: 'bookmark', saved: !state.saved }, state.saved ? 'Bookmark removed.' : 'Lesson bookmarked.');
    });
    root.querySelector('[data-saved-highlights]').addEventListener('click', event => {
        const id = event.target.closest('[data-remove-highlight]')?.dataset.removeHighlight;
        if (id) save({ action: 'remove', id }, 'Highlight removed.');
    });
    document.addEventListener('selectionchange', updateSelection);
    window.addEventListener('resize', updateSelection);
    window.addEventListener('scroll', () => {
        if (selection.length) updateSelection();
    }, { passive: true });

    const initial = signedIn ? request(root.dataset.annotationUrl) : Promise.resolve().then(() => lessonLocal(readLocal()));
    initial.then(data => {
        state = data;
        loaded = true;
        updateControls();
        renderHighlights();
    }).catch(error => announce(error.message));
    refreshBookmarks().catch(error => announce(error.message));
})();
