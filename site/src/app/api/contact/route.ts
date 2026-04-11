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
    const { name, email, company, industry, teamSize, message } = body as Record<string, string>;

    if (!name || !email || !message) {
      return NextResponse.json(
        { error: "Name, email, and message are required" },
        { status: 400 }
      );
    }

    if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return NextResponse.json(
        { error: "Valid email required" },
        { status: 400 }
      );
    }

    const entries = await readContacts();
    entries.push({
      name,
      email: email.toLowerCase(),
      company: company ?? "",
      industry: industry ?? "",
      teamSize: teamSize ?? "",
      message,
      timestamp: new Date().toISOString(),
    });

    await writeContacts(entries);

    console.log(`[Contact] New inquiry from ${name} <${email}> (${company || "no company"})`);

    return NextResponse.json({ status: "ok" });
  } catch {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
