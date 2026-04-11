"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useLanguage } from "@/contexts/LanguageContext";
import { t, tx } from "@/lib/translations";

const NAV_ITEMS = [
  { href: "/challenge", labelEn: "Challenge", labelJa: "チャレンジ" },
  { href: "/pricing", labelEn: "Pricing", labelJa: "料金" },
  { href: "/docs", labelEn: "Docs", labelJa: "ドキュメント" },
];

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { lang, setLang } = useLanguage();
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 bg-white/90 backdrop-blur border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 font-bold text-xl text-guardian-700">
          <ShieldIcon />
          Aigis
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-gray-600">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`hover:text-guardian-600 transition-colors ${
                  isActive ? "font-semibold text-guardian-600" : ""
                }`}
              >
                {lang === "ja" ? item.labelJa : item.labelEn}
              </Link>
            );
          })}
          <a href="https://zenn.dev/sharu389no" target="_blank" rel="noopener noreferrer" className="hover:text-guardian-600 transition-colors">{lang === "ja" ? "ブログ" : "Blog"}</a>
          <a
            href="https://github.com/killertcell428/aigis"
            target="_blank"
            rel="noreferrer"
            className="hover:text-guardian-600 transition-colors flex items-center gap-1"
          >
            <GitHubIcon />
            {tx(t.nav.github, lang)}
          </a>
        </nav>

        {/* CTA + Lang toggle */}
        <div className="hidden md:flex items-center gap-3">
          {/* Language toggle */}
          <div className="flex items-center rounded-full border border-gray-200 overflow-hidden text-xs font-semibold">
            <button
              onClick={() => setLang("en")}
              className={`px-3 py-1.5 transition-colors ${lang === "en" ? "bg-guardian-600 text-white" : "text-gray-500 hover:bg-gray-50"}`}
            >
              EN
            </button>
            <button
              onClick={() => setLang("ja")}
              className={`px-3 py-1.5 transition-colors ${lang === "ja" ? "bg-guardian-600 text-white" : "text-gray-500 hover:bg-gray-50"}`}
            >
              日本語
            </button>
          </div>

          <Link href="/docs/quickstart" className="text-sm font-semibold text-gray-700 hover:text-guardian-600 transition-colors">
            {tx(t.nav.signIn, lang)}
          </Link>
          <Link href="/#waitlist" className="btn-primary text-sm">
            {tx(t.nav.startTrial, lang)}
          </Link>
        </div>

        {/* Mobile burger */}
        <button
          className="md:hidden p-2 rounded-md text-gray-600 hover:bg-gray-100"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          {mobileOpen ? <XIcon /> : <MenuIcon />}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-gray-200 bg-white px-4 py-4 space-y-3">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`block text-sm py-2 ${
                  isActive ? "font-bold text-guardian-600" : "font-medium text-gray-700"
                }`}
                onClick={() => setMobileOpen(false)}
              >
                {lang === "ja" ? item.labelJa : item.labelEn}
              </Link>
            );
          })}
          <a href="https://zenn.dev/sharu389no" target="_blank" rel="noopener noreferrer" className="block text-sm font-medium text-gray-700 py-2">{lang === "ja" ? "ブログ" : "Blog"}</a>
          <a href="https://github.com/killertcell428/aigis" target="_blank" rel="noreferrer" className="block text-sm font-medium text-gray-700 py-2">GitHub</a>
          {/* Mobile lang toggle */}
          <div className="flex items-center gap-2 py-2">
            <span className="text-xs text-gray-500">{lang === "ja" ? "言語：" : "Language:"}</span>
            <button
              onClick={() => setLang("en")}
              className={`text-xs px-2 py-1 rounded border ${lang === "en" ? "bg-guardian-600 text-white border-guardian-600" : "border-gray-300 text-gray-600"}`}
            >EN</button>
            <button
              onClick={() => setLang("ja")}
              className={`text-xs px-2 py-1 rounded border ${lang === "ja" ? "bg-guardian-600 text-white border-guardian-600" : "border-gray-300 text-gray-600"}`}
            >日本語</button>
          </div>
          <Link href="/#waitlist" className="btn-primary w-full text-center mt-2" onClick={() => setMobileOpen(false)}>{tx(t.nav.startTrial, lang)}</Link>
        </div>
      )}
    </header>
  );
}

function ShieldIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-guardian-600">
      <path
        d="M12 2L3 6v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V6l-9-4z"
        fill="currentColor"
        fillOpacity="0.15"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function GitHubIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
    </svg>
  );
}

function MenuIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  );
}

function XIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}
