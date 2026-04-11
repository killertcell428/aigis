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
    const { email, lang } = body as { email?: string; lang?: string };

    if (!email || email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return NextResponse.json(
        { error: "Valid email required" },
        { status: 400 }
      );
    }

    const entries = await readWaitlist();

    // Deduplicate
    if (entries.some((e) => e.email.toLowerCase() === email.toLowerCase())) {
      return NextResponse.json({ status: "already_registered" });
    }

    entries.push({
      email: email.toLowerCase(),
      lang: lang ?? "en",
      timestamp: new Date().toISOString(),
    });

    await writeWaitlist(entries);

    console.log(`[Waitlist] New signup: ${email} (${lang ?? "en"})`);

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
