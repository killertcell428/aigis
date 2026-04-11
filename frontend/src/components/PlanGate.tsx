"use client";

import { ReactNode, useEffect, useState } from "react";
import { getLang } from "@/lib/lang";

const PLAN_ORDER = ["free", "pro", "business", "enterprise"];

interface Props {
  requiredPlan: string;
  currentPlan: string;
  children: ReactNode;
}

export default function PlanGate({ requiredPlan, currentPlan, children }: Props) {
  const [lang, setLang] = useState<"en" | "ja">("ja");
  useEffect(() => { setLang(getLang()); }, []);

  const currentIdx = PLAN_ORDER.indexOf(currentPlan);
  const requiredIdx = PLAN_ORDER.indexOf(requiredPlan);

  if (currentIdx >= requiredIdx) {
    return <>{children}</>;
  }

  const planLabel = requiredPlan.charAt(0).toUpperCase() + requiredPlan.slice(1);
  const currentLabel = currentPlan.charAt(0).toUpperCase() + currentPlan.slice(1);
  const ja = lang === "ja";

  return (
    <div className="bg-gd-surface border-2 border-dashed border-gd-standard rounded-xl p-8 text-center">
      <p className="text-lg text-gd-text-primary" style={{ fontWeight: 560 }}>
        {ja ? `${planLabel} プラン以上が必要です` : `${planLabel} Plan Required`}
      </p>
      <p className="text-sm text-gd-text-secondary mt-2">
        {ja
          ? `この機能には ${planLabel} プラン以上が必要です。現在のプランは ${currentLabel} です。`
          : `This feature requires the ${planLabel} plan or higher. You are currently on the ${currentLabel} plan.`}
      </p>
      <a
        href="/billing"
        className="inline-block mt-4 px-5 py-2.5 bg-gd-accent text-white rounded-lg text-sm shadow-gd-inset hover:bg-gd-accent-hover transition-colors"
        style={{ fontWeight: 520 }}
      >
        {ja ? "プランをアップグレード" : "Upgrade Plan"}
      </a>
    </div>
  );
}
