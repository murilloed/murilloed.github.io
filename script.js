const switcher = document.querySelector(".lang-toggle");
const year = document.querySelector("#year");
let language = localStorage.getItem("language") || "en";

function applyLanguage(nextLanguage) {
  language = nextLanguage;
  document.documentElement.lang = language === "pt" ? "pt-BR" : "en";

  document.querySelectorAll("[data-en][data-pt]").forEach((element) => {
    element.textContent = element.dataset[language];
  });

  switcher.setAttribute(
    "aria-label",
    language === "en" ? "Mudar para português" : "Switch to English",
  );
  localStorage.setItem("language", language);
}

switcher.addEventListener("click", () => {
  applyLanguage(language === "en" ? "pt" : "en");
});

year.textContent = new Date().getFullYear();
applyLanguage(language);

// Keep navigation state aligned with direct links and in-page navigation.
const navigationLinks = document.querySelectorAll('.topbar nav a[href^="#"]');
function updateNavigation() {
  const hash = window.location.hash || "#home";
  navigationLinks.forEach((link) => {
    const active = link.getAttribute("href") === hash;
    link.classList.toggle("active", active);
    if (active) link.setAttribute("aria-current", "location");
    else link.removeAttribute("aria-current");
  });
}
window.addEventListener("hashchange", updateNavigation);
updateNavigation();
