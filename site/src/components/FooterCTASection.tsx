"use client";

import Link from "next/link";
import { useLanguage } from "@/contexts/LanguageContext";
import { t, tx } from "@/lib/translations";

export default function FooterCTASection() {
  const { lang } = useLanguage();

  return (
    <section className="py-24 bg-gradient-to-r from-guardian-800 to-guardian-950 text-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <p className="text-guardian-400 text-sm font-medium uppercase tracking-widest mb-4">{tx(t.footerCta.label, lang)}</p>
        <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-4">{tx(t.footerCta.heading, lang)}</h2>
        <p className="text-guardian-200 text-lg max-w-xl mx-auto mb-10">{tx(t.footerCta.sub, lang)}</p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link href="/#waitlist" className="bg-white text-guardian-700 hover:bg-guardian-50 transition-colors font-semibold px-8 py-3 rounded-lg text-base">
            {tx(t.footerCta.cta1, lang)}
          </Link>
          <Link href="/docs" className="btn-outline-white px-8 py-3 text-base">
            {tx(t.footerCta.cta2, lang)}
          </Link>
        </div>
        <p className="text-guardian-500 text-xs mt-10 max-w-sm mx-auto">
          {tx(t.footerCta.contactPrefix, lang)}{" "}
          <a href="mailto:ueda.bioinfo.base01@gmail.com" className="text-guardian-400 hover:text-guardian-200 underline transition-colors">
            ueda.bioinfo.base01@gmail.com
          </a>
          {tx(t.footerCta.contactSuffix, lang)}
        </p>
      </div>
    </section>
  );
}
