"use client";

import { useState } from "react";
import { useLanguage } from "@/contexts/LanguageContext";
import { t, tx } from "@/lib/translations";

export default function FAQSection() {
  const [open, setOpen] = useState<number | null>(null);
  const { lang } = useLanguage();

  const faqs = [
    { q: tx(t.faq.q1, lang), a: tx(t.faq.a1, lang) },
    { q: tx(t.faq.q2, lang), a: tx(t.faq.a2, lang) },
    { q: tx(t.faq.q3, lang), a: tx(t.faq.a3, lang) },
    { q: tx(t.faq.q4, lang), a: tx(t.faq.a4, lang) },
    { q: tx(t.faq.q5, lang), a: tx(t.faq.a5, lang) },
    { q: tx(t.faq.q6, lang), a: tx(t.faq.a6, lang) },
  ];

  return (
    <section id="faq" className="py-24 bg-white">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <p className="text-guardian-600 text-sm font-semibold uppercase tracking-widest mb-3">{tx(t.faq.label, lang)}</p>
          <h2 className="section-heading">{tx(t.faq.heading, lang)}</h2>
        </div>

        <div className="divide-y divide-gray-100">
          {faqs.map((faq, i) => (
            <div key={i}>
              <button
                className="w-full text-left py-5 flex items-start justify-between gap-4"
                onClick={() => setOpen(open === i ? null : i)}
              >
                <span className="font-semibold text-gray-900 text-sm leading-relaxed">{faq.q}</span>
                <span className={`text-guardian-500 flex-shrink-0 text-lg transition-transform duration-200 ${open === i ? "rotate-45" : ""}`}>+</span>
              </button>
              {open === i && (
                <div className="pb-5 text-sm text-gray-600 leading-relaxed">{faq.a}</div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-12 p-5 bg-guardian-50 rounded-xl border border-guardian-100">
          <p className="text-sm text-guardian-800 font-medium">{tx(t.faq.contactLabel, lang)}</p>
          <p className="text-sm text-guardian-600 mt-1">
            {tx(t.faq.contactSub, lang)}{" "}
            <a href="mailto:ueda.bioinfo.base01@gmail.com" className="underline underline-offset-2 hover:text-guardian-800 transition-colors">
              ueda.bioinfo.base01@gmail.com
            </a>
            {tx(t.faq.contactSuffix, lang)}
          </p>
        </div>
      </div>
    </section>
  );
}
