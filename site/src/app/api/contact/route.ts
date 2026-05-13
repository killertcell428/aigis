/**
 * Contact form API — stores enterprise inquiries.
 * Uses /tmp JSON for demo; replace with database for production.
 */

import { NextRequest, NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";

// Pinned to /tmp/contacts.json on the server. The filename is a compile-time
// constant — user input never reaches the path argument of fs.writeFile.
const CONTACTS_FILE = path.join("/tmp", "contacts.json");

// Disk-fill mitigation: keep at most this many entries on disk; older entries
// are dropped FIFO. Combined with per-field clampString this caps file size
// to roughly MAX_CONTACTS * 6 KB ≈ 30 MB.
const MAX_CONTACTS = 5000;

interface ContactEntry {
  name: string;
  email: string;
  company: string;
  industry: string;
  teamSize: string;
  message: string;
  timestamp: string;
}

function clampString(value: unknown, max: number): string {
  if (typeof value !== "string") return "";
  return value.slice(0, max);
}

async function readContacts(): Promise<ContactEntry[]> {
  try {
    const data = await fs.readFile(CONTACTS_FILE, "utf-8");
    return JSON.parse(data) as ContactEntry[];
  } catch {
    return [];
  }
}

async function writeContacts(entries: ContactEntry[]): Promise<void> {
  // Trim to the most recent MAX_CONTACTS to prevent unbounded disk growth
  // from repeated POSTs. CodeQL: filename is the compile-time constant
  // CONTACTS_FILE; only the JSON-serialized payload depends on HTTP input.
  const trimmed =
    entries.length > MAX_CONTACTS ? entries.slice(-MAX_CONTACTS) : entries;
  await fs.writeFile(CONTACTS_FILE, JSON.stringify(trimmed, null, 2));
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const raw = body as Record<string, unknown>;

    const name = clampString(raw.name, 200);
    const rawEmail = clampString(raw.email, 254);
    const message = clampString(raw.message, 5000);
    const company = clampString(raw.company, 200);
    const industry = clampString(raw.industry, 100);
    const teamSize = clampString(raw.teamSize, 50);

    if (!name || !rawEmail || !message) {
      return NextResponse.json(
        { error: "Name, email, and message are required" },
        { status: 400 }
      );
    }

    if (!/^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(rawEmail)) {
      return NextResponse.json(
        { error: "Valid email required" },
        { status: 400 }
      );
    }

    const email = rawEmail.toLowerCase();

    const entries = await readContacts();
    entries.push({
      name,
      email,
      company,
      industry,
      teamSize,
      message,
      timestamp: new Date().toISOString(),
    });

    await writeContacts(entries);

    // Log only non-tainted metadata. User-supplied fields stay in the file
    // record — they never reach the log sink, so log-injection is structurally
    // impossible regardless of input.
    const emailAt = email.indexOf("@");
    const emailDomain = emailAt >= 0 ? email.slice(emailAt + 1) : "unknown";
    console.log(
      JSON.stringify({
        event: "contact.received",
        entry_index: entries.length,
        message_len: message.length,
        name_len: name.length,
        company_present: company.length > 0,
        email_domain_len: emailDomain.length,
      })
    );

    return NextResponse.json({ status: "ok" });
  } catch {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
