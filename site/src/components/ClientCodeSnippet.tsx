"use client";

import { useEffect, useState } from "react";
import { codeToHtml } from "shiki";

interface ClientCodeSnippetProps {
  code: string;
  lang: string;
  theme?: string;
}

export default function ClientCodeSnippet({
  code,
  lang,
  theme = "github-dark",
}: ClientCodeSnippetProps) {
  const [html, setHtml] = useState<string>("");

  useEffect(() => {
    codeToHtml(code, { lang, theme }).then(setHtml);
  }, [code, lang, theme]);

  if (!html) {
    return (
      <div className="rounded-xl overflow-hidden text-sm font-mono bg-gray-950 text-gray-100">
        <pre className="p-5 overflow-x-auto"><code>{code}</code></pre>
      </div>
    );
  }

  return (
    <div
      className="rounded-xl overflow-hidden text-sm font-mono [&_pre]:p-5 [&_pre]:overflow-x-auto"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
