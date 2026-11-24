(() => {
    const LOAD_DEADLINE = 45000;
    const RUN_DEADLINE = 8000;
    const workerSources = new Map();
    let activeRun = false;

    function getWorkerSource(url) {
        if (!workerSources.has(url)) {
            const request = fetch(url, { credentials: 'same-origin' }).then(response => {
                if (!response.ok) throw new Error('Worker source unavailable');
                return response.text();
            }).catch(error => {
                workerSources.delete(url);
                throw error;
            });
            workerSources.set(url, request);
        }
        return workerSources.get(url);
    }

    function normalizeOutput(value) {
        return value.replace(/\r\n/g, '\n').replace(/\n$/, '');
    }

    document.querySelectorAll('.python-practice').forEach(practice => {
        const editor = practice.querySelector('.practice-code');
        const output = practice.querySelector('.practice-output');
        const status = practice.querySelector('.practice-status');
        const runButton = practice.querySelector('.practice-run');
        const checkButton = practice.querySelector('.practice-check');
        const resetButton = practice.querySelector('.practice-reset');
        const stopButton = practice.querySelector('.practice-stop');
        const expected = practice.querySelector('.practice-expected');
        const starter = editor.value;
        const emptyOutput = output.textContent;

        function setStatus(message, kind = '') {
            status.textContent = message;
            status.dataset.kind = kind;
        }

        function execute(check, trigger) {
            if (activeRun) {
                setStatus('Stop the current run before starting another.');
                return;
            }
            if (!editor.value.trim()) {
                setStatus('Enter some Python code first.');
                editor.focus();
                return;
            }
            if (editor.value.length > editor.maxLength) {
                setStatus('Practice code is limited to 16,000 characters.', 'error');
                return;
            }

            const frame = document.createElement('iframe');
            const channel = new MessageChannel();
            const code = editor.value;
            let finished = false;
            let started = false;
            const timeoutMessage = 'Python could not start. Check your connection and try again.';
            let deadline = setTimeout(() => {
                output.textContent = 'Python runtime unavailable.';
                close(timeoutMessage, 'error');
            }, LOAD_DEADLINE);

            function close(message, kind) {
                if (finished) return;
                finished = true;
                clearTimeout(deadline);
                channel.port1.close();
                channel.port2.close();
                frame.remove();
                activeRun = false;
                runButton.disabled = resetButton.disabled = false;
                if (checkButton) checkButton.disabled = false;
                editor.readOnly = false;
                if (document.activeElement === stopButton) trigger.focus();
                stopButton.hidden = true;
                stopButton.onclick = null;
                setStatus(message, kind);
            }

            activeRun = true;
            runButton.disabled = resetButton.disabled = true;
            if (checkButton) checkButton.disabled = true;
            editor.readOnly = true;
            stopButton.hidden = false;
            stopButton.onclick = () => {
                output.textContent = 'Execution stopped.';
                close('Run stopped.');
            };
            if (trigger !== editor) stopButton.focus();
            output.textContent = 'Starting Python…';
            setStatus('Loading Python…');

            channel.port1.onmessage = ({ data }) => {
                if (data?.type === 'ready' && !started) {
                    started = true;
                    clearTimeout(deadline);
                    deadline = setTimeout(() => {
                        output.textContent = 'Execution stopped.';
                        close(`Code ran for more than ${RUN_DEADLINE / 1000} seconds. Check your loop conditions.`, 'error');
                    }, RUN_DEADLINE);
                    output.textContent = 'Waiting for output…';
                    setStatus('Running your code…');
                    return;
                }
                if (data?.type === 'unavailable') {
                    output.textContent = 'Python runtime unavailable.';
                    close(timeoutMessage, 'error');
                    return;
                }
                if (data?.type !== 'result') return;

                output.textContent = [data.stdout, data.stderr, data.error].filter(Boolean).join('\n') || 'No output. Use print() to show a value.';
                if (data.truncated) output.textContent += '\n\n[Output limit reached]';

                if (data.error) {
                    close('Python reported an error. See the output panel.', 'error');
                } else if (data.truncated) {
                    close('Output was shortened. Try printing fewer values.', 'error');
                } else if (!check) {
                    close('Run finished.', 'success');
                } else {
                    expected.hidden = false;
                    if (normalizeOutput(data.stdout) === normalizeOutput(practice.dataset.expected) && !data.stderr) {
                        close('Correct! Your output matches.', 'success');
                    } else {
                        close('Try again. Compare your result with the expected output.', 'error');
                    }
                }
            };

            frame.hidden = true;
            frame.title = 'Isolated Python runtime';
            frame.setAttribute('sandbox', 'allow-scripts');
            frame.referrerPolicy = 'no-referrer';
            frame.src = practice.dataset.sandbox;
            frame.addEventListener('load', async () => {
                try {
                    const source = await getWorkerSource(practice.dataset.worker);
                    if (!finished) {
                        frame.contentWindow.postMessage({ type: 'python-run', source, code }, '*', [channel.port2]);
                    }
                } catch {
                    output.textContent = 'Python runtime unavailable.';
                    close(timeoutMessage, 'error');
                }
            }, { once: true });
            document.body.append(frame);
        }

        runButton.addEventListener('click', () => execute(false, runButton));
        checkButton?.addEventListener('click', () => execute(true, checkButton));
        resetButton.addEventListener('click', () => {
            editor.value = starter;
            output.textContent = emptyOutput;
            if (expected) {
                expected.hidden = true;
                expected.open = false;
            }
            setStatus('Starter code restored.');
            editor.focus();
        });
        editor.addEventListener('keydown', event => {
            if (event.key !== 'Enter' || editor.readOnly || event.isComposing) return;
            if (event.ctrlKey || event.metaKey) {
                event.preventDefault();
                execute(false, editor);
                return;
            }
            const currentLine = editor.value.slice(0, editor.selectionStart).split('\n').pop();
            const indent = currentLine.match(/^\s*/)[0];
            const nextLine = `\n${indent}${currentLine.trimEnd().endsWith(':') ? '    ' : ''}`;
            const lengthAfterEdit = editor.value.length - (editor.selectionEnd - editor.selectionStart) + nextLine.length;
            if (lengthAfterEdit <= editor.maxLength) {
                event.preventDefault();
                editor.setRangeText(nextLine, editor.selectionStart, editor.selectionEnd, 'end');
            }
        });
    });
})();
