export type Lang = "en" | "ja";

export function getLang(): Lang {
  if (typeof window === "undefined") return "ja";
  return (localStorage.getItem("aig_lang") as Lang) || "ja";
}

export function saveLang(lang: Lang) {
  localStorage.setItem("aig_lang", lang);
}
