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
