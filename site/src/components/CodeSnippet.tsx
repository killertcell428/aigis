import { codeToHtml } from "shiki";

interface CodeSnippetProps {
  code: string;
  lang: string;
  theme?: string;
}

export default async function CodeSnippet({
  code,
  lang,
  theme = "github-dark",
}: CodeSnippetProps) {
  const html = await codeToHtml(code, {
    lang,
    theme,
  });

  return (
    <div
      className="rounded-xl overflow-hidden text-sm font-mono [&_pre]:p-5 [&_pre]:overflow-x-auto"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
