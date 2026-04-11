"use client";

import { useLanguage } from "@/contexts/LanguageContext";
import { t, tx } from "@/lib/translations";

export default function HowItWorksSection() {
  const { lang } = useLanguage();

  const steps = [
    {
      step: "01",
      title: tx(t.howItWorks.step1Title, lang),
      description: tx(t.howItWorks.step1Desc, lang),
      code: 'base_url="http://localhost:8000/api/v1/proxy"',
      aside: tx(t.howItWorks.step1Aside, lang),
    },
    {
      step: "02",
      title: tx(t.howItWorks.step2Title, lang),
      description: tx(t.howItWorks.step2Desc, lang),
      aside: tx(t.howItWorks.step2Aside, lang),
    },
    {
      step: "03",
      title: tx(t.howItWorks.step3Title, lang),
      description: tx(t.howItWorks.step3Desc, lang),
      aside: tx(t.howItWorks.step3Aside, lang),
    },
  ];

  return (
    <section id="how-it-works" className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <p className="text-guardian-600 text-sm font-semibold uppercase tracking-widest mb-3">{tx(t.howItWorks.label, lang)}</p>
          <h2 className="section-heading">{tx(t.howItWorks.heading, lang)}</h2>
          <p className="section-subheading">{tx(t.howItWorks.sub, lang)}</p>
        </div>

        <div className="relative">
          <div className="hidden md:block absolute top-[60px] left-[16.66%] right-[16.66%] h-px bg-gradient-to-r from-guardian-200 via-guardian-400 to-guardian-200" />
          <div className="grid md:grid-cols-3 gap-8">
            {steps.map((step) => (
              <div key={step.step} className="relative flex flex-col items-center text-center">
                <div className="relative z-10 w-14 h-14 rounded-full bg-guardian-600 text-white flex items-center justify-center text-sm font-bold mb-6 shadow-lg shadow-guardian-200/50 font-mono tracking-tight">
                  {step.step}
                </div>
                <div className="card w-full text-left">
                  <h3 className="text-base font-bold text-gray-900 mb-2 leading-snug">{step.title}</h3>
                  <p className="text-sm text-gray-600 leading-relaxed">{step.description}</p>
                  {step.code && (
                    <code className="mt-4 block text-xs bg-gray-950 text-green-400 rounded-lg px-3 py-2.5 font-mono overflow-x-auto">
                      {step.code}
                    </code>
                  )}
                  <p className="mt-3 text-xs text-guardian-500 font-medium">{step.aside}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
