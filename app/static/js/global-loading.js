(() => {
  const loader = document.querySelector("[data-page-loading]");
  if (!loader) {
    return;
  }

  let timer = null;

  const showLoader = () => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => {
      loader.hidden = false;
      document.body.classList.add("loading-active");
    }, 180);
  };

  const hideLoader = () => {
    window.clearTimeout(timer);
    loader.hidden = true;
    document.body.classList.remove("loading-active");
  };

  document.addEventListener("submit", (event) => {
    window.setTimeout(() => {
      if (!event.defaultPrevented) {
        const submitter = event.submitter;
        if (submitter && !submitter.disabled) {
          submitter.disabled = true;
        }
        showLoader();
      }
    }, 0);
  });

  document.addEventListener("click", (event) => {
    const link = event.target.closest("a[href]");
    if (!link || event.defaultPrevented) {
      return;
    }
    if (link.target || link.hasAttribute("download") || link.dataset.noLoading === "true") {
      return;
    }

    const url = new URL(link.href, window.location.href);
    if (url.origin !== window.location.origin || url.href === window.location.href || url.hash) {
      return;
    }

    showLoader();
  });

  window.addEventListener("pageshow", hideLoader);
  window.addEventListener("pagehide", hideLoader);
})();
