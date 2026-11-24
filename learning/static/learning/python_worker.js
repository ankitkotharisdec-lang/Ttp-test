const PYODIDE_URL = 'https://cdn.jsdelivr.net/pyodide/v0.27.7/full/';
const OUTPUT_LIMIT = 16000;

function limitedStream() {
    const buffer = new Uint8Array(OUTPUT_LIMIT);
    let length = 0;
    let truncated = false;
    return {
        write(bytes) {
            const remaining = OUTPUT_LIMIT - length;
            const accepted = bytes.subarray(0, remaining);
            buffer.set(accepted, length);
            length += accepted.length;
            truncated ||= bytes.length > accepted.length;
            return bytes.length;
        },
        text: () => new TextDecoder().decode(buffer.subarray(0, length)),
        wasTruncated: () => truncated,
    };
}

self.addEventListener('message', async ({ data: code }) => {
    let python;
    try {
        importScripts(`${PYODIDE_URL}pyodide.js`);
        python = await loadPyodide({ indexURL: PYODIDE_URL });
    } catch {
        self.postMessage({ type: 'unavailable' });
        return;
    }

    const stdout = limitedStream();
    const stderr = limitedStream();
    let error = '';
    try {
        await python.loadPackagesFromImports(code);
        self.postMessage({ type: 'ready' });
        python.setStdout({ write: stdout.write });
        python.setStderr({ write: stderr.write });
        python.setStdin({ stdin: () => undefined });
        const value = await python.runPythonAsync(code, { filename: 'practice.py' });
        if (value instanceof python.ffi.PyProxy) value.destroy();
    } catch (exception) {
        error = String(exception).slice(0, OUTPUT_LIMIT);
        if (error.startsWith('PythonError:')) {
            const userFrame = error.indexOf('  File "practice.py"');
            if (userFrame >= 0) error = `Traceback (most recent call last):\n${error.slice(userFrame)}`;
        }
    }
    self.postMessage({
        type: 'result',
        stdout: stdout.text(),
        stderr: stderr.text(),
        truncated: stdout.wasTruncated() || stderr.wasTruncated(),
        error,
    });
}, { once: true });
