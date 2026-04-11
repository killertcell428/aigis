"use client";

import Link from "next/link";
import { useLanguage } from "@/contexts/LanguageContext";
import { t, tx } from "@/lib/translations";

export default function DocsLayout({
  children,
  toc,
}: {
  children: React.ReactNode;
  toc?: { id: string; label: string; level?: number }[];
}) {
  const { lang } = useLanguage();

  const NAV = [
    {
      category: tx(t.docsLayout.gettingStarted, lang),
      items: [
        { label: tx(t.docsLayout.overview, lang), href: "/docs" },
        { label: tx(t.docsLayout.quickstart, lang), href: "/docs/quickstart" },
      ],
    },
    {
      category: tx(t.docsLayout.conceptsCategory, lang),
      items: [
        { label: tx(t.docsLayout.coreConcepts, lang), href: "/docs/concepts" },
      ],
    },
    {
      category: tx(t.docsLayout.reference, lang),
      items: [
        { label: tx(t.docsLayout.apiReference, lang), href: "/docs/api-reference" },
      ],
    },
    {
      category: tx(t.docsLayout.integrationsCategory, lang),
      items: [
        { label: tx(t.docsLayout.python, lang), href: "/docs/integrations/python" },
        { label: tx(t.docsLayout.nodejs, lang), href: "/docs/integrations/nodejs" },
      ],
    },
    {
      category: tx(t.docsLayout.complianceCategory, lang),
      items: [
        { label: tx(t.docsLayout.japanGovernance, lang), href: "/docs/compliance/japan" },
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Docs header */}
      <div className="border-b border-gray-200 bg-white sticky top-16 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center gap-2 text-sm text-gray-500">
          <Link href="/" className="hover:text-guardian-600 transition-colors">Aigis</Link>
          <span>/</span>
          <Link href="/docs" className="hover:text-guardian-600 transition-colors font-medium text-gray-700">
            {tx(t.docsLayout.breadcrumbDocs, lang)}
          </Link>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex gap-8 py-10">
        {/* Left sidebar */}
        <aside className="hidden md:block w-56 flex-shrink-0 self-start sticky top-32">
          <nav className="space-y-6">
            {NAV.map((section) => (
              <div key={section.category}>
                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">
                  {section.category}
                </h4>
                <ul className="space-y-1">
                  {section.items.map((item) => (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        className="block text-sm text-gray-600 hover:text-guardian-600 py-1 transition-colors rounded px-2 hover:bg-guardian-50"
                      >
                        {item.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </nav>
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0 prose prose-gray prose-sm max-w-none prose-headings:font-bold prose-a:text-guardian-600 prose-code:text-guardian-700 prose-code:bg-guardian-50 prose-code:px-1 prose-code:rounded prose-pre:bg-gray-950 prose-pre:text-gray-100">
          {children}
        </main>

        {/* Right TOC */}
        {toc && toc.length > 0 && (
          <aside className="hidden lg:block w-48 flex-shrink-0 self-start sticky top-32">
            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">
              {tx(t.docsLayout.onThisPage, lang)}
            </h4>
            <nav className="space-y-1">
              {toc.map((item) => (
                <a
                  key={item.id}
                  href={`#${item.id}`}
                  className={`block text-xs text-gray-500 hover:text-guardian-600 py-0.5 transition-colors ${item.level === 3 ? "pl-3" : ""}`}
                >
                  {item.label}
                </a>
              ))}
            </nav>
          </aside>
        )}
      </div>
    </div>
  );
}
