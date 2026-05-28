const sidebarToggles = document.querySelectorAll("[data-sidebar-toggle]");
const sidebarClosers = document.querySelectorAll("[data-sidebar-close]");

function setSidebarState(open) {
  document.body.classList.toggle("sidebar-open", open);
}

sidebarToggles.forEach((button) => {
  button.addEventListener("click", () => setSidebarState(true));
});

sidebarClosers.forEach((button) => {
  button.addEventListener("click", () => setSidebarState(false));
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    setSidebarState(false);
  }
});

document.querySelectorAll(".sidebar .nav-list a").forEach((link) => {
  link.addEventListener("click", () => setSidebarState(false));
});
