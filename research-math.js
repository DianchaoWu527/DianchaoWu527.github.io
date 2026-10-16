/* KaTeX is deferred before this script on both research pages. */
(() => {
    const content = document.querySelector('.research-content');
    if (!content || typeof window.renderMathInElement !== 'function') return;

    window.renderMathInElement(content, {
        delimiters: [
            { left: '\\[', right: '\\]', display: true },
            { left: '\\(', right: '\\)', display: false }
        ],
        throwOnError: false,
        trust: false
    });
})();
