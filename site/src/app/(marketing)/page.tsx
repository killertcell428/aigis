import HeroSection from "@/components/HeroSection";
import WaitlistSection from "@/components/WaitlistSection";
import SocialProofBar from "@/components/SocialProofBar";
import HowItWorksSection from "@/components/HowItWorksSection";
import SocialProofSection from "@/components/SocialProofSection";
import FeaturesSection from "@/components/FeaturesSection";
import RiskScoringSection from "@/components/RiskScoringSection";
import CodeIntegrationSection from "@/components/CodeIntegrationSection";
import PricingSection from "@/components/PricingSection";
import FAQSection from "@/components/FAQSection";
import FooterCTASection from "@/components/FooterCTASection";

export default function LandingPage() {
  return (
    <>
      <HeroSection />
      <WaitlistSection lang="en" />
      <SocialProofBar />
      <HowItWorksSection />
      <SocialProofSection />
      <FeaturesSection />
      <RiskScoringSection />
      <CodeIntegrationSection />
      {/* Dashboard Preview */}
      <section className="py-20 bg-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-guardian-600 text-sm font-semibold uppercase tracking-widest mb-3">Dashboard</p>
          <h2 className="text-3xl md:text-4xl font-extrabold text-gray-900 tracking-tight mb-4">
            See every threat in real time
          </h2>
          <p className="text-gray-500 text-lg max-w-2xl mx-auto mb-10">
            Monitor risk scores, blocked attacks, and team activity from a single dashboard.
            No more guessing what your AI agents are doing.
          </p>
          <div className="relative rounded-2xl border border-gray-200 bg-gray-950 shadow-2xl overflow-hidden">
            {/* Mock dashboard UI */}
            <div className="p-6 md:p-8">
              <div className="flex items-center gap-2 mb-6">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <div className="w-3 h-3 rounded-full bg-green-500" />
                <span className="ml-3 text-gray-500 text-xs font-mono">dashboard.ai-guardian.dev</span>
              </div>
              <div className="grid grid-cols-4 gap-4 mb-6">
                {[
                  { label: "Total Requests", value: "24,891", color: "text-white" },
                  { label: "Blocked", value: "147", color: "text-red-400" },
                  { label: "High Risk", value: "23", color: "text-yellow-400" },
                  { label: "Detection Rate", value: "100%", color: "text-green-400" },
                ].map((stat) => (
                  <div key={stat.label} className="bg-gray-900/80 rounded-xl p-4 text-left">
                    <div className="text-gray-500 text-xs mb-1">{stat.label}</div>
                    <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
                  </div>
                ))}
              </div>
              {/* Mock chart area */}
              <div className="bg-gray-900/60 rounded-xl p-6 h-48 flex items-end gap-1">
                {[40, 35, 55, 45, 60, 50, 70, 65, 80, 75, 90, 85, 70, 95, 60, 75, 80, 70, 85, 90, 75, 80, 85, 70].map((h, i) => (
                  <div
                    key={i}
                    className="flex-1 bg-guardian-500/70 rounded-t-sm hover:bg-guardian-400 transition-colors"
                    style={{ height: `${h}%` }}
                  />
                ))}
              </div>
              <div className="flex justify-between text-gray-600 text-xs mt-2 px-1">
                <span>7 days ago</span>
                <span>Today</span>
              </div>
            </div>
          </div>
          <p className="mt-6 text-gray-400 text-sm">
            Available on Pro and Business plans · 14-day free trial
          </p>
        </div>
      </section>

      <PricingSection />
      <FAQSection />
      <FooterCTASection />
    </>
  );
}
