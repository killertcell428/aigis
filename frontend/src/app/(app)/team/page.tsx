"use client";

import { useEffect, useState } from "react";
import { billingApi, teamApi, TeamMember, UsageStats } from "@/lib/api";
import LangToggle from "@/components/LangToggle";
import { getLang, saveLang } from "@/lib/lang";

export default function TeamPage() {
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [showInvite, setShowInvite] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteName, setInviteName] = useState("");
  const [inviteRole, setInviteRole] = useState("reviewer");
  const [invitePassword, setInvitePassword] = useState("");
  const [error, setError] = useState("");
  const [lang, setLang] = useState<"en" | "ja">("ja");

  useEffect(() => {
    setLang(getLang());
  }, []);

  function changeLang(l: "en" | "ja") {
    saveLang(l);
    setLang(l);
    window.dispatchEvent(new Event("aig-lang-change"));
  }

  const load = () => {
    setLoading(true);
    Promise.all([teamApi.list().catch(() => []), billingApi.getUsage()])
      .then(([m, u]) => {
        setMembers(Array.isArray(m) ? m : []);
        setUsage(u);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleInvite = async () => {
    if (!inviteEmail || !inviteName || !invitePassword) return;
    setError("");
    try {
      await teamApi.invite(inviteEmail, inviteName, inviteRole, invitePassword);
      setShowInvite(false);
      setInviteEmail("");
      setInviteName("");
      setInvitePassword("");
      load();
    } catch (err: any) {
      setError(err.message || "Failed to invite member");
    }
  };

  const atLimit =
    usage?.team_limit !== null &&
    usage?.team_limit !== undefined &&
    usage?.team_size !== undefined &&
    usage.team_size >= usage.team_limit;

  const t = {
    en: {
      title: "Team Management",
      invite: "Invite Member",
      name: "Full Name",
      email: "Email",
      password: "Temp Password",
      role: "Role",
      send: "Send Invite",
      cancel: "Cancel",
      seats: "seats used",
      atLimit: "Team limit reached. Upgrade to add more members.",
      nameCol: "Name",
      emailCol: "Email",
      roleCol: "Role",
      statusCol: "Status",
      active: "Active",
      inactive: "Inactive",
      noMembers: "No team members yet",
      loading: "Loading...",
      upgrade: "Upgrade",
    },
    ja: {
      title: "チーム管理",
      invite: "メンバー招待",
      name: "氏名",
      email: "メールアドレス",
      password: "仮パスワード",
      role: "ロール",
      send: "招待する",
      cancel: "キャンセル",
      seats: "席使用中",
      atLimit: "チーム上限に達しました。アップグレードしてメンバーを追加してください。",
      nameCol: "名前",
      emailCol: "メールアドレス",
      roleCol: "ロール",
      statusCol: "ステータス",
      active: "有効",
      inactive: "無効",
      noMembers: "チームメンバーはまだいません",
      loading: "読み込み中...",
      upgrade: "アップグレード",
    },
  }[lang];

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl text-gd-text-primary" style={{ fontWeight: 580 }}>{t.title}</h1>
        <div className="flex items-center gap-2">
          <LangToggle lang={lang} onChange={changeLang} />
          <button
            onClick={() => setShowInvite(true)}
            disabled={atLimit}
            className="px-4 py-2 bg-gd-accent text-white text-sm rounded-lg hover:bg-gd-accent-hover shadow-gd-inset disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            style={{ fontWeight: 480 }}
          >
            {t.invite}
          </button>
        </div>
      </div>

      {/* Seats indicator */}
      {usage && (
        <div className="text-sm text-gd-text-muted">
          <span className="text-gd-text-secondary" style={{ fontWeight: 540 }}>{usage.team_size}</span>
          {" / "}
          {usage.team_limit ?? "Unlimited"} {t.seats}
        </div>
      )}

      {atLimit && (
        <div className="bg-gd-warn-bg border border-gd-subtle rounded-lg px-4 py-3 text-sm text-gd-warn">
          {t.atLimit}{" "}
          <a href="/billing" className="underline" style={{ fontWeight: 480 }}>
            {t.upgrade}
          </a>
        </div>
      )}

      {/* Invite form */}
      {showInvite && (
        <div className="bg-gd-surface border border-gd-subtle rounded-xl p-6 shadow-gd-card space-y-4">
          {error && (
            <div className="bg-gd-danger-bg border border-gd-subtle rounded-lg px-4 py-2 text-sm text-gd-danger">
              {error}
            </div>
          )}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gd-text-muted mb-1">{t.name}</label>
              <input
                className="w-full px-3 py-2 bg-gd-input border border-gd-standard rounded-lg text-sm text-gd-text-primary placeholder-gd-text-dim focus:outline-none focus:border-gd-accent focus:shadow-gd-focus"
                value={inviteName}
                onChange={(e) => setInviteName(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs text-gd-text-muted mb-1">{t.email}</label>
              <input
                type="email"
                className="w-full px-3 py-2 bg-gd-input border border-gd-standard rounded-lg text-sm text-gd-text-primary placeholder-gd-text-dim focus:outline-none focus:border-gd-accent focus:shadow-gd-focus"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs text-gd-text-muted mb-1">{t.password}</label>
              <input
                type="password"
                className="w-full px-3 py-2 bg-gd-input border border-gd-standard rounded-lg text-sm text-gd-text-primary placeholder-gd-text-dim focus:outline-none focus:border-gd-accent focus:shadow-gd-focus"
                value={invitePassword}
                onChange={(e) => setInvitePassword(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs text-gd-text-muted mb-1">{t.role}</label>
              <select
                className="w-full px-3 py-2 bg-gd-input border border-gd-standard rounded-lg text-sm text-gd-text-primary focus:outline-none focus:border-gd-accent focus:shadow-gd-focus"
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
              >
                <option value="reviewer">Reviewer</option>
                <option value="admin">Admin</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleInvite}
              className="px-4 py-2 bg-gd-accent text-white text-sm rounded-lg hover:bg-gd-accent-hover shadow-gd-inset"
              style={{ fontWeight: 480 }}
            >
              {t.send}
            </button>
            <button
              onClick={() => setShowInvite(false)}
              className="px-4 py-2 text-gd-text-secondary text-sm rounded-lg hover:bg-gd-elevated"
            >
              {t.cancel}
            </button>
          </div>
        </div>
      )}

      {/* Members table */}
      <div className="bg-gd-surface border border-gd-subtle rounded-xl shadow-gd-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gd-subtle bg-gd-elevated">
              <th className="text-left px-4 py-3 text-gd-text-secondary" style={{ fontWeight: 480 }}>{t.nameCol}</th>
              <th className="text-left px-4 py-3 text-gd-text-secondary" style={{ fontWeight: 480 }}>{t.emailCol}</th>
              <th className="text-left px-4 py-3 text-gd-text-secondary" style={{ fontWeight: 480 }}>{t.roleCol}</th>
              <th className="text-left px-4 py-3 text-gd-text-secondary" style={{ fontWeight: 480 }}>{t.statusCol}</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-gd-text-muted">
                  {t.loading}
                </td>
              </tr>
            ) : members.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-gd-text-muted">
                  {t.noMembers}
                </td>
              </tr>
            ) : (
              members.map((m) => (
                <tr key={m.id} className="border-b border-[rgba(255,255,255,0.04)] hover:bg-gd-elevated">
                  <td className="px-4 py-3 text-gd-text-primary" style={{ fontWeight: 480 }}>{m.full_name}</td>
                  <td className="px-4 py-3 text-gd-text-secondary">{m.email}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-xs ${
                        m.role === "admin"
                          ? "bg-purple-900/30 text-purple-400"
                          : "bg-gd-elevated text-gd-text-secondary"
                      }`}
                      style={{ fontWeight: 480 }}
                    >
                      {m.role}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-xs ${
                        m.is_active
                          ? "bg-gd-safe-bg text-gd-safe"
                          : "bg-gd-danger-bg text-gd-danger"
                      }`}
                      style={{ fontWeight: 480 }}
                    >
                      {m.is_active ? t.active : t.inactive}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
