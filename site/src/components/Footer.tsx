"use client";

import Link from "next/link";
import { useLanguage } from "@/contexts/LanguageContext";
import { t, tx } from "@/lib/translations";

export default function Footer() {
  const { lang } = useLanguage();

  const links = {
    [tx(t.footer.product, lang)]: [
      { label: tx(t.footer.features, lang), href: "/#features" },
      { label: tx(t.footer.pricing, lang), href: "/pricing" },
      { label: tx(t.footer.howItWorks, lang), href: "/#how-it-works" },
      { label: tx(t.footer.riskScoring, lang), href: "/#risk-scoring" },
    ],
    [tx(t.footer.docs, lang)]: [
      { label: tx(t.footer.overview, lang), href: "/docs" },
      { label: tx(t.footer.quickstart, lang), href: "/docs/quickstart" },
      { label: tx(t.footer.concepts, lang), href: "/docs/concepts" },
      { label: tx(t.footer.apiRef, lang), href: "/docs/api-reference" },
    ],
    [tx(t.footer.integrations, lang)]: [
      { label: tx(t.footer.python, lang), href: "/docs/integrations/python" },
      { label: tx(t.footer.nodejs, lang), href: "/docs/integrations/nodejs" },
      { label: tx(t.footer.openai, lang), href: "/docs/integrations/python" },
      { label: tx(t.footer.langchain, lang), href: "/docs/integrations/python" },
    ],
    [tx(t.footer.company, lang)]: [
      { label: tx(t.footer.github, lang), href: "https://github.com" },
      { label: tx(t.footer.privacy, lang), href: "#" },
      { label: tx(t.footer.terms, lang), href: "#" },
      { label: tx(t.footer.security, lang), href: "#" },
    ],
  };

  return (
    <footer className="bg-gray-950 text-gray-400">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
          <div className="col-span-2 md:col-span-1">
            <Link href="/" className="flex items-center gap-2 font-bold text-lg text-white mb-3">
              <ShieldIcon />
              Aigis
            </Link>
            <p className="text-sm leading-relaxed">{tx(t.footer.tagline, lang)}</p>
            <div className="flex gap-3 mt-4">
              <Badge>SOC2 Ready</Badge>
              <Badge>GDPR</Badge>
            </div>
          </div>

          {Object.entries(links).map(([category, catLinks]) => (
            <div key={category}>
              <h4 className="text-sm font-semibold text-white mb-3">{category}</h4>
              <ul className="space-y-2">
                {catLinks.map((link) => (
                  <li key={link.label}>
                    <Link href={link.href} className="text-sm hover:text-white transition-colors">{link.label}</Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-gray-500">
          <p>{tx(t.footer.copyright, lang)}</p>
          <p>{tx(t.footer.builtFor, lang)}</p>
        </div>
      </div>
    </footer>
  );
}

function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span className="text-xs px-2 py-0.5 rounded-full border border-gray-700 text-gray-400">{children}</span>
  );
}

function ShieldIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
      <path d="M12 2L3 6v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V6l-9-4z" fill="white" fillOpacity="0.15" stroke="white" strokeWidth="1.5" strokeLinejoin="round" />
      <path d="M9 12l2 2 4-4" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
