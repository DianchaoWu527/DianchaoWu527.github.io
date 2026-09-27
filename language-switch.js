// Static links work without JavaScript; preserve the current query and section when switching.
(() => {
    const links = document.querySelectorAll(".language-switch a");
    const update = () => {
        for (const link of links) {
            const destination = new URL(link.getAttribute("href"), document.baseURI);
            destination.search = window.location.search;
            destination.hash = window.location.hash;
            link.href = destination.href;
        }
    };
    update();
    window.addEventListener("hashchange", update);
})();
