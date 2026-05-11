/**
 * Waitlist API — stores beta signup emails.
 * Uses a simple JSON file on Vercel's /tmp for demo;
 * replace with Supabase/database for production.
 */

import { NextRequest, NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";

const WAITLIST_FILE = path.join("/tmp", "waitlist.json");

interface WaitlistEntry {
  email: string;
  lang: string;
  timestamp: string;
}

function sanitizeForLog(value: string): string {
  return value.replace(/[\r\n\t\x00-\x1f\x7f]/g, "_").slice(0, 200);
}

async function readWaitlist(): Promise<WaitlistEntry[]> {
  try {
    const data = await fs.readFile(WAITLIST_FILE, "utf-8");
    return JSON.parse(data) as WaitlistEntry[];
  } catch {
    return [];
  }
}

async function writeWaitlist(entries: WaitlistEntry[]): Promise<void> {
  await fs.writeFile(WAITLIST_FILE, JSON.stringify(entries, null, 2));
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { email: rawEmail, lang: rawLang } = body as { email?: string; lang?: string };

    if (
      typeof rawEmail !== "string" ||
      rawEmail.length > 254 ||
      !/^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(rawEmail)
    ) {
      return NextResponse.json(
        { error: "Valid email required" },
        { status: 400 }
      );
    }

    const email = rawEmail.toLowerCase();
    const lang = typeof rawLang === "string" && /^[a-z]{2}(-[A-Z]{2})?$/.test(rawLang) ? rawLang : "en";

    const entries = await readWaitlist();

    if (entries.some((e) => e.email === email)) {
      return NextResponse.json({ status: "already_registered" });
    }

    entries.push({
      email,
      lang,
      timestamp: new Date().toISOString(),
    });

    await writeWaitlist(entries);

    console.log(`[Waitlist] New signup: ${sanitizeForLog(email)} (${sanitizeForLog(lang)})`);

    return NextResponse.json({ status: "ok" });
  } catch {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function GET() {
  // Simple admin endpoint — in production, add auth
  const entries = await readWaitlist();
  return NextResponse.json({ count: entries.length, entries });
}
