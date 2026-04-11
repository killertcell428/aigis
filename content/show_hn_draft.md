# Show HN: Aigis — Open-source LLM security library

## 投稿タイミング
**月〜水曜 EST 9:00-10:00（日本時間 夜22:00-23:00）** に投稿すること
→ HNのトラフィックが最も高い時間帯。朝一番のページに乗れれば数百upvote狙える。

---

## タイトル（コピペ用）
```
Show HN: Aigis – Open-source LLM security library with remediation hints (Python, zero deps)
```

## URL（コピペ用）
```
https://github.com/killertcell428/aigis
```

## 本文（コピペ用）
```
I built an open-source Python library that scans LLM prompts and
responses for security threats.

The key difference from existing tools (LLM Guard, Rebuff, etc.):
it doesn't just block — it explains WHY something was flagged and
HOW to fix it.

  from aigis import Guard
  guard = Guard()
  result = guard.check_input("Ignore previous instructions and...")
  # result.risk_score = 94, result.reasons = ["prompt_injection"],
  # result.remediation = "..."

What it detects (64 patterns):
- Prompt injection & jailbreaks ("ignore previous instructions", DAN, roleplay abuse)
- SQL injection in LLM pipelines (UNION SELECT, blind injection)
- PII & credential leaks (API keys, credit cards, My Number / マイナンバー)
- Indirect prompt injection in RAG documents
- Multi-turn attack sequences

Other features:
- OWASP LLM Top 10 + CWE classification on every detection
- Auto-sanitize: sanitize("Call me at 090-1234-5678") → "Call me at [PHONE_REDACTED]"
- FastAPI middleware, LangChain callback, OpenAI proxy — 3-line integration
- Zero required dependencies (pure Python stdlib)

Try the Gandalf Challenge — an interactive game where you try to
trick the AI into revealing a secret password. Each level uses
harder defenses: https://aigis-mauve.vercel.app/challenge

pip install aigis  (v0.6.1, latest)

Would love feedback on detection patterns and any bypasses you find!
```

---

## 投稿手順
1. https://news.ycombinator.com/submit を開く
2. タイトルをコピペ
3. URLをコピペ
4. 「submit」→ 本文は**コメント欄の最初の返信**として投稿する（HNのルール）
5. 投稿後すぐに本文コメントを追加する

## 投稿後のアクション
- [ ] 投稿後30分以内に本文コメントを追加
- [ ] コメントが来たら**1時間以内に返信**（初動のエンゲージメントがランキングに影響）
- [ ] Reddit r/Python, r/netsec にクロスポスト（翌日）
- [ ] URLを `content/weekly_x_drafts/` にメモしてTwitterでシェア
