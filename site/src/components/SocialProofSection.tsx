"use client";

import { useLanguage } from "@/contexts/LanguageContext";
import { t, tx } from "@/lib/translations";

export default function SocialProofSection() {
  const { lang } = useLanguage();

  const testimonials = [
    { quote: tx(t.testimonials.q1, lang), name: "Marcus T.", role: tx(t.testimonials.r1, lang), company: tx(t.testimonials.c1, lang), initials: "MT" },
    { quote: tx(t.testimonials.q2, lang), name: "Yuki N.", role: tx(t.testimonials.r2, lang), company: tx(t.testimonials.c2, lang), initials: "YN" },
    { quote: tx(t.testimonials.q3, lang), name: "Priya K.", role: tx(t.testimonials.r3, lang), company: tx(t.testimonials.c3, lang), initials: "PK" },
  ];

  return (
    <section className="py-20 bg-white border-t border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <p className="text-center text-guardian-600 text-sm font-semibold uppercase tracking-widest mb-10">
          {tx(t.testimonials.label, lang)}
        </p>
        <div className="grid md:grid-cols-3 gap-6">
          {testimonials.map((t) => (
            <div key={t.initials} className="bg-gray-50 rounded-2xl p-6 border border-gray-100">
              <p className="text-sm text-gray-700 leading-relaxed mb-5">&ldquo;{t.quote}&rdquo;</p>
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-guardian-100 text-guardian-700 flex items-center justify-center text-xs font-bold flex-shrink-0">
                  {t.initials}
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-900">{t.name}</p>
                  <p className="text-xs text-gray-500">{t.role} · {t.company}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
