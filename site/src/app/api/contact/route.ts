/**
 * Contact form API — stores enterprise inquiries.
 * Uses /tmp JSON for demo; replace with database for production.
 */

import { NextRequest, NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";

const CONTACTS_FILE = path.join("/tmp", "contacts.json");

interface ContactEntry {
  name: string;
  email: string;
  company: string;
  industry: string;
  teamSize: string;
  message: string;
  timestamp: string;
}

function sanitizeForLog(value: string): string {
  return value.replace(/[\r\n\t\x00-\x1f\x7f]/g, "_").slice(0, 200);
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
  await fs.writeFile(CONTACTS_FILE, JSON.stringify(entries, null, 2));
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

    console.log(
      `[Contact] New inquiry from ${sanitizeForLog(name)} <${sanitizeForLog(email)}> (${sanitizeForLog(company || "no company")})`
    );

    return NextResponse.json({ status: "ok" });
  } catch {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
