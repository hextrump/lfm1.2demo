import { Type } from "@earendil-works/pi-ai";
import { defineTool, type ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { execFile } from "node:child_process";
import { readFile } from "node:fs/promises";
import { resolve, relative } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const appDir = resolve(__dirname, "..");
const knowledgeDir = resolve(appDir, "knowledge");
const currentErrorPath = resolve(appDir, "erp_state", "current_error.json");
const ticketsPath = resolve(appDir, "erp_state", "tickets.json");

async function readTicketsStore(): Promise<{ tickets: any[] }> {
  try {
    const text = await readFile(ticketsPath, "utf8");
    return JSON.parse(text);
  } catch (_error) {
    return { tickets: [] };
  }
}

async function writeTicketsStore(store: { tickets: any[] }): Promise<void> {
  const { writeFile, mkdir } = await import("node:fs/promises");
  const { dirname } = await import("node:path");
  await mkdir(dirname(ticketsPath), { recursive: true });
  await writeFile(ticketsPath, JSON.stringify(store, null, 2), "utf8");
}

const TICKET_STATUSES = ["New", "Triaged", "In Progress", "Resolved", "Closed"] as const;
type TicketStatus = (typeof TICKET_STATUSES)[number];

function asString(v: unknown, fallback = ""): string {
  return v == null ? fallback : String(v);
}
function nowIso(): string {
  return new Date().toISOString();
}

type ScenarioKey =
	| "AADSTS50076"
	| "AADSTS50105"
	| "LICENSE_MISSING"
	| "CA_BLOCK"
	| "CRM_MENU_MISSING"
	| "POWERBI_DENIED"
	| "MULTI_USER_OUTAGE"
	| "VENDOR_MFA_EXCEPTION";

type EvidenceHit = { path: string; line: number; snippet: string };

const scenarios: Record<ScenarioKey, Record<string, unknown>> = {
	AADSTS50076: {
		system: "Dynamics 365",
		symptom: "login_failed",
		error_code: "AADSTS50076",
		category: "Microsoft Entra ID / MFA / Conditional Access",
		risk: "Medium",
		priority: "P3",
		route: "Identity / Entra ID 管理チーム",
		impact: "single_user",
		allowed_actions: ["guide_user", "collect_context", "create_ticket", "handoff_to_it_agent"],
		blocked_actions: ["password_reset", "mfa_disable", "permission_grant", "conditional_access_change"],
	},
	AADSTS50105: {
		system: "Salesforce",
		symptom: "app_assignment_missing",
		error_code: "AADSTS50105",
		category: "Application Assignment / Permission",
		risk: "Medium",
		priority: "P3",
		route: "業務システム権限管理チーム",
		impact: "single_user",
		allowed_actions: ["collect_approval", "create_ticket", "handoff_to_it_agent"],
		blocked_actions: ["permission_grant", "license_assignment"],
	},
	LICENSE_MISSING: {
		system: "Dynamics 365",
		symptom: "license_missing",
		error_code: "LICENSE_MISSING",
		category: "License / Microsoft 365",
		risk: "Medium",
		priority: "P3",
		route: "Microsoft 365 ライセンス管理チーム",
		impact: "single_user",
		allowed_actions: ["collect_business_need", "create_ticket", "handoff_to_it_agent"],
		blocked_actions: ["license_assignment"],
	},
	CA_BLOCK: {
		system: "社内ERP",
		symptom: "conditional_access_block",
		error_code: "CA_BLOCK",
		category: "Security / Conditional Access",
		risk: "High",
		priority: "P2",
		route: "Security / Conditional Access チーム",
		impact: "single_user",
		allowed_actions: ["collect_context", "create_ticket", "handoff_to_it_agent"],
		blocked_actions: ["conditional_access_change", "mfa_disable"],
	},
	CRM_MENU_MISSING: {
		system: "Dynamics 365 Sales",
		symptom: "menu_missing",
		error_code: "NO_ERROR_CODE",
		category: "CRM Role / Business Unit Permission",
		risk: "Medium",
		priority: "P3",
		route: "CRM Owner / Dynamics 管理者",
		impact: "single_user",
		allowed_actions: ["collect_approval", "create_ticket", "handoff_to_it_agent"],
		blocked_actions: ["permission_grant"],
	},
	POWERBI_DENIED: {
		system: "Power BI",
		symptom: "report_permission_denied",
		error_code: "PBI_ACCESS_DENIED",
		category: "Power BI Workspace / Dataset Permission",
		risk: "Low",
		priority: "P3",
		route: "BI 管理者 / Data Platform Team",
		impact: "single_user",
		allowed_actions: ["collect_report_name", "create_ticket", "handoff_to_it_agent"],
		blocked_actions: ["permission_grant"],
	},
	MULTI_USER_OUTAGE: {
		system: "社内ERP",
		symptom: "multi_user_outage",
		error_code: "MULTI_USER_OUTAGE",
		category: "IT Ops / Service Incident",
		risk: "High",
		priority: "P2",
		route: "IT Ops / Incident Manager",
		impact: "multiple_users",
		allowed_actions: ["create_incident_candidate", "create_ticket", "handoff_to_it_agent"],
		blocked_actions: ["user_specific_reset"],
	},
	VENDOR_MFA_EXCEPTION: {
		system: "Integration Account",
		symptom: "vendor_mfa_exception",
		error_code: "VENDOR_MFA_EXCEPTION",
		category: "Security Exception / Vendor Access",
		risk: "High",
		priority: "P2",
		route: "Security Team + IAM Approval Board",
		impact: "privileged_account",
		allowed_actions: ["create_security_review", "create_ticket", "handoff_to_it_agent"],
		blocked_actions: ["mfa_disable", "conditional_access_change", "privilege_grant"],
	},
};

async function readCurrentErrorState() {
	try {
		const text = await readFile(currentErrorPath, "utf8");
		return JSON.parse(text);
	} catch (_error) {
		return { active: false };
	}
}

async function searchKnowledge(query: string, limit = 8, signal?: AbortSignal) {
	const safeLimit = Math.max(1, Math.min(limit, 20));
	const { stdout } = await execFileAsync("rg", ["-n", "-i", "--context", "1", query, knowledgeDir], {
		signal,
		timeout: 4000,
		maxBuffer: 128 * 1024,
	}).catch((error) => ({ stdout: error.stdout ?? "" }));
	const hits: EvidenceHit[] = [];
	for (const line of stdout.split(/\r?\n/)) {
		if (!line || line === "--") continue;
		const hit = parseRgLine(line);
		if (!hit) continue; // skip rg section separators like "path-5-" with no content
		hits.push(hit);
		if (hits.length >= safeLimit) break;
	}
	return hits;
}

function parseRgLine(line: string): EvidenceHit | null {
	// rg match line:  path:line:content
	let m = line.match(/^(.+?):(\d+):(.*)$/);
	if (m) {
		return {
			path: relative(appDir, m[1]),
			line: Number(m[2]),
			snippet: m[3].trim(),
		};
	}
	// rg context line:  path-line-content  (snippet may itself contain colons)
	m = line.match(/^(.+?)-(\d+)-(.*)$/);
	if (m) {
		return {
			path: relative(appDir, m[1]),
			line: Number(m[2]),
			snippet: m[3].trim(),
		};
	}
	// rg section separator like "path-5-" (no content) — drop it
	return null;
}

function detectScenario(input: string): ScenarioKey {
	const text = input.toLowerCase();
	if (text.includes("aadsts50105")) return "AADSTS50105";
	if (text.includes("license") || text.includes("ライセンス")) return "LICENSE_MISSING";
	if (text.includes("conditional") || text.includes("ca_block") || text.includes("条件付き")) return "CA_BLOCK";
	if (text.includes("power bi") || text.includes("pbi")) return "POWERBI_DENIED";
	if (text.includes("複数") || text.includes("multiple") || text.includes("outage")) return "MULTI_USER_OUTAGE";
	if (text.includes("vendor") || text.includes("ベンダー") || text.includes("mfa を無効")) return "VENDOR_MFA_EXCEPTION";
	if (text.includes("menu") || text.includes("メニュー")) return "CRM_MENU_MISSING";
	return "AADSTS50076";
}

function makeTicketId(input: string): string {
	let hash = 0;
	for (const char of input) hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
	return `KW-${String((hash % 9000) + 1000).padStart(4, "0")}`;
}

const erpGetCurrentError = defineTool({
	name: "erp_get_current_error",
	label: "Current ERP Error",
	description: "Read the current simulated ERP web page error log, including visible error text, trace ID, correlation ID, user, and selected system.",
	promptSnippet: "Read the active ERP page error shown to the human user.",
	promptGuidelines: [
		"Use erp_get_current_error when the user asks you to inspect the current ERP screen, current error, current log, trace ID, or browser-visible problem.",
	],
	parameters: Type.Object({}),
	async execute() {
		const state = await readCurrentErrorState();
		return {
			content: [{ type: "text", text: state.active === false ? "No active ERP error log is available." : JSON.stringify(state, null, 2) }],
			details: state,
		};
	},
});

const erpInspectCurrentErrorWithKb = defineTool({
	name: "erp_inspect_current_error_with_kb",
	label: "Inspect Current ERP Error With KB",
	description: "Read the current ERP page error and search the local knowledge base for policy evidence in one business workflow.",
	promptSnippet: "Inspect active ERP error and retrieve KB evidence.",
	promptGuidelines: [
		"Use this tool when the user asks to inspect the current error and also asks for rules, policy, evidence, 社内規程, 根拠, or 検索.",
		"Use this tool when a small multi-step ERP diagnosis would otherwise require erp_get_current_error followed by kb_rg_search.",
	],
	parameters: Type.Object({
		query: Type.Optional(Type.String({ description: "Optional KB query. If omitted, the current error code or system is used." })),
	}),
	async execute(_toolCallId, params, signal) {
		const error = await readCurrentErrorState();
		const query = params.query || error.error_code || error.system || error.symptom || "";
		const evidence = query ? await searchKnowledge(String(query), 8, signal) : [];
		const details = { error, query, evidence };
		return {
			content: [{ type: "text", text: JSON.stringify(details, null, 2) }],
			details,
		};
	},
});

const erpAnalyzePastedErrorWithKb = defineTool({
	name: "erp_analyze_pasted_error_with_kb",
	label: "Analyze Pasted ERP Error With KB",
	description: "Analyze pasted ERP/SSO/CRM error text and search the local knowledge base without creating a ticket.",
	promptSnippet: "Analyze pasted business-system error text and retrieve local policy evidence.",
	promptGuidelines: [
		"Use this tool when the user pastes an ERP/SSO/CRM error log, error code, Trace ID, or sign-in failure text.",
		"Do not create a ticket from pasted error text unless the user explicitly asks for IT contact or ticket creation.",
	],
	parameters: Type.Object({
		user_message: Type.String({ description: "The pasted user-visible error text or problem report" }),
	}),
	async execute(_toolCallId, params, signal) {
		const scenario_key = detectScenario(params.user_message);
		const state = scenarios[scenario_key];
		const traceMatch = params.user_message.match(/Trace ID:\s*([^\s]+)/i);
		const correlationMatch = params.user_message.match(/Correlation ID:\s*([^\s]+)/i);
		const query = String(state.error_code || scenario_key);
		const evidence = await searchKnowledge(query, 8, signal);
		const details = {
			scenario_key,
			...state,
			trace_id: traceMatch?.[1] ?? "",
			correlation_id: correlationMatch?.[1] ?? "",
			pasted_text: params.user_message,
			evidence,
			next_action: "explain_and_collect_context",
			ticket_created: false,
		};
		return {
			content: [{ type: "text", text: JSON.stringify(details, null, 2) }],
			details,
		};
	},
});

const erpQueryState = defineTool({
	name: "erp_query_state",
	label: "ERP State",
	description: "Inspect the simulated ERP/CRM/SSO state for a user's support issue.",
	promptSnippet: "Query simulated ERP state, scenario, error, route, risk, allowed actions, and blocked actions.",
	promptGuidelines: [
		"Use erp_query_state first when the user reports login, permission, license, CRM, Power BI, vendor, or outage issues.",
	],
	parameters: Type.Object({
		user_message: Type.String({ description: "The user's natural-language problem report" }),
	}),
	async execute(_toolCallId, params) {
		const scenario_key = detectScenario(params.user_message);
		const state = { scenario_key, ...scenarios[scenario_key] };
		return {
			content: [{ type: "text", text: JSON.stringify(state, null, 2) }],
			details: state,
		};
	},
});

const kbRgSearch = defineTool({
	name: "kb_rg_search",
	label: "Knowledge Search",
	description: "Search the local enterprise policy knowledge base with ripgrep.",
	promptSnippet: "Search local ERP, SSO, CRM, Power BI, security, and helpdesk policy files.",
	promptGuidelines: [
		"Use kb_rg_search after erp_query_state to find local policy evidence before answering or creating a ticket.",
	],
	parameters: Type.Object({
		query: Type.String({ description: "Search query such as an error code, system, policy, or route" }),
		limit: Type.Optional(Type.Number({ description: "Maximum number of hits to return" })),
	}),
	async execute(_toolCallId, params, signal) {
		const limit = Math.max(1, Math.min(params.limit ?? 8, 20));
		const hits = await searchKnowledge(params.query, limit, signal);
		return {
			content: [{ type: "text", text: JSON.stringify({ query: params.query, hits }, null, 2) }],
			details: { query: params.query, hits },
		};
	},
});

const kbReadKnowledge = defineTool({
	name: "kb_read_knowledge",
	label: "Read Knowledge",
	description: "Read a local knowledge-base markdown file returned by kb_rg_search.",
	promptSnippet: "Read a whitelisted local knowledge-base document.",
	promptGuidelines: [
		"Use kb_read_knowledge only for files under the knowledge directory returned by kb_rg_search.",
	],
	parameters: Type.Object({
		path: Type.String({ description: "Relative knowledge file path, for example knowledge/sso/entra-id-login-errors.md" }),
		max_chars: Type.Optional(Type.Number({ description: "Maximum characters to return" })),
	}),
	async execute(_toolCallId, params) {
		const absolute = resolve(appDir, params.path.replace(/^@/, ""));
		if (!absolute.startsWith(knowledgeDir)) {
			throw new Error("Path is outside the knowledge directory.");
		}
		const text = await readFile(absolute, "utf8");
		const maxChars = Math.max(200, Math.min(params.max_chars ?? 3000, 8000));
		return {
			content: [{ type: "text", text: text.slice(0, maxChars) }],
			details: { path: relative(appDir, absolute), chars: Math.min(text.length, maxChars) },
		};
	},
});

const erpDraftTicket = defineTool({
	name: "erp_draft_ticket",
	label: "Draft Ticket",
	description: "Draft a simulated IT ticket from ERP state, user issue, and knowledge evidence.",
	promptSnippet: "Create a structured draft for helpdesk/IT operations.",
	promptGuidelines: [
		"Use erp_draft_ticket when the issue is unresolved, high risk, multi-user, or needs IT routing.",
	],
	parameters: Type.Object({
		user_message: Type.String(),
		scenario_key: Type.String(),
		requester: Type.Optional(Type.String()),
		evidence_summary: Type.Optional(Type.String()),
	}),
	async execute(_toolCallId, params) {
		const key = (params.scenario_key in scenarios ? params.scenario_key : detectScenario(params.user_message)) as ScenarioKey;
		const state = scenarios[key];
		const draft = {
			requester: params.requester ?? "demo.user@demo.local",
			system: state.system,
			error_code: state.error_code,
			category: state.category,
			risk: state.risk,
			priority: state.priority,
			route: state.route,
			impact: state.impact,
			summary: params.user_message,
			evidence_summary: params.evidence_summary ?? "",
			blocked_actions: state.blocked_actions,
		};
		return {
			content: [{ type: "text", text: JSON.stringify(draft, null, 2) }],
			details: draft,
		};
	},
});

const erpCreateTicket = defineTool({
	name: "erp_create_ticket",
	label: "Create Ticket",
	description: "Create a simulated ITSM ticket only when the user explicitly asks for IT contact, helpdesk escalation, or ticket creation.",
	promptSnippet: "Create a simulated ticket after an explicit ticket/helpdesk request and return a KW ticket id.",
	promptGuidelines: [
		"Use erp_create_ticket only after erp_draft_ticket. It is allowed because this is the simulated ERP helpdesk system.",
		"Do not use erp_create_ticket for pasted error text alone. Analyze pasted errors first.",
	],
	parameters: Type.Object({
		summary: Type.String(),
		route: Type.String(),
		priority: Type.Optional(Type.String()),
		risk: Type.Optional(Type.String()),
		requester: Type.Optional(Type.String()),
		system: Type.Optional(Type.String()),
		error_code: Type.Optional(Type.String()),
		category: Type.Optional(Type.String()),
		impact: Type.Optional(Type.String()),
		evidence_summary: Type.Optional(Type.String()),
	}),
	async execute(_toolCallId, params) {
		const ticket = {
			ticket_id: makeTicketId(`${params.summary}:${params.route}`),
			status: "New",
			requester: params.requester ?? "",
			route: params.route,
			priority: params.priority ?? "P3",
			risk: params.risk ?? "Medium",
			summary: params.summary,
			system: params.system ?? "fake-erp-helpdesk",
			error_code: params.error_code ?? "",
			category: params.category ?? "Agent P ticket",
			impact: params.impact ?? "unknown",
			evidence_summary: params.evidence_summary ?? "",
		};
		return {
			content: [{ type: "text", text: JSON.stringify(ticket, null, 2) }],
			details: ticket,
		};
	},
});

const erpCreateTicketFromCurrentError = defineTool({
	name: "erp_create_ticket_from_current_error",
	label: "Create Ticket From Current ERP Error",
	description: "Create a simulated IT ticket and handoff package from the active ERP error log.",
	promptSnippet: "Create a ticket from the current ERP error in one business workflow.",
	promptGuidelines: [
		"Use this tool when the user asks to contact IT, helpdesk, ITに連絡, or create a ticket for the current ERP error.",
		"This tool is preferred over manually chaining draft/create/handoff for small local models.",
	],
	parameters: Type.Object({
		user_message: Type.String(),
	}),
	async execute(_toolCallId, params, signal) {
		const error = await readCurrentErrorState();
		const scenarioKey = (error.scenario_key && error.scenario_key in scenarios ? error.scenario_key : detectScenario(params.user_message)) as ScenarioKey;
		const state = scenarios[scenarioKey];
		const query = String(error.error_code || state.error_code || state.system || scenarioKey);
		const evidence = await searchKnowledge(query, 5, signal);
		const summary = `${params.user_message} / ${String(error.system || state.system)} / ${String(error.error_code || state.error_code)} / trace ${String(error.trace_id || "")}`;
		const ticket = {
			ticket_id: makeTicketId(`${summary}:${String(state.route)}`),
			status: "New",
			requester: error.user_email ?? "demo.user@demo.local",
			system: error.system ?? state.system,
			error_code: error.error_code ?? state.error_code,
			category: state.category,
			risk: state.risk,
			priority: state.priority,
			route: state.route,
			impact: state.impact,
			summary,
			evidence,
			evidence_summary: "current ERP error and local KB evidence",
			blocked_actions: state.blocked_actions,
		};
		const handoff = {
			accepted_by: "IT Operations Agent P",
			ticket_id: ticket.ticket_id,
			route: ticket.route,
			evidence_summary: ticket.evidence_summary,
			blocked_actions: ticket.blocked_actions,
			next_queue: ticket.route,
		};
		const details = { ticket, handoff };
		return {
			content: [{ type: "text", text: JSON.stringify(details, null, 2) }],
			details,
		};
	},
});

const erpHandoff = defineTool({
	name: "erp_handoff_to_it_agent",
	label: "Handoff To IT Agent",
	description: "Send a simulated ticket and evidence package to the IT-side Agent P.",
	promptSnippet: "Handoff a ticket to IT Agent P with route, evidence, and blocked actions.",
	promptGuidelines: [
		"Use erp_handoff_to_it_agent after erp_create_ticket when the user asks IT to handle the issue or the risk is high.",
	],
	parameters: Type.Object({
		ticket_id: Type.String(),
		route: Type.String(),
		evidence_summary: Type.Optional(Type.String()),
		blocked_actions: Type.Optional(Type.Array(Type.String())),
	}),
	async execute(_toolCallId, params) {
		const handoff = {
			accepted_by: "IT Operations Agent P",
			ticket_id: params.ticket_id,
			route: params.route,
			evidence_summary: params.evidence_summary ?? "",
			blocked_actions: params.blocked_actions ?? [],
			next_queue: params.route,
		};
		return {
			content: [{ type: "text", text: JSON.stringify(handoff, null, 2) }],
			details: handoff,
		};
	},
});

const erpExecuteAdminAction = defineTool({
	name: "erp_execute_admin_action",
	label: "Execute Admin Action",
	description: "Execute only approved low-risk simulated admin actions in the fake ERP system.",
	promptSnippet: "Execute safe simulated ERP actions such as guide_user, collect_context, create_incident_candidate.",
	promptGuidelines: [
		"Use erp_execute_admin_action only for allowed low-risk simulated actions from erp_query_state.",
		"erp_execute_admin_action must refuse password_reset, mfa_disable, permission_grant, conditional_access_change, license_assignment, and privilege_grant.",
	],
	parameters: Type.Object({
		action: Type.String(),
		target: Type.String(),
		reason: Type.String(),
	}),
	async execute(_toolCallId, params) {
		const blocked = new Set([
			"password_reset",
			"mfa_disable",
			"permission_grant",
			"conditional_access_change",
			"license_assignment",
			"privilege_grant",
		]);
		if (blocked.has(params.action)) {
			throw new Error(`Refused high-risk admin action: ${params.action}. IT approval is required.`);
		}
		const result = {
			action: params.action,
			target: params.target,
			reason: params.reason,
			status: "simulated_success",
		};
		return {
			content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
			details: result,
		};
	},
});

// ═══════════════════════════════════════════════════════════════════════════
// IT Agent tools — for the IT Operations page agent that triages / resolves /
// closes / re-assigns / comments on tickets persisted in erp_state/tickets.json
// ═══════════════════════════════════════════════════════════════════════════

const erpItListTickets = defineTool({
	name: "erp_it_list_tickets",
	label: "List IT Tickets",
	description: "List tickets in the IT Operations queue with optional filters.",
	promptSnippet: "List IT tickets in the queue.",
	promptGuidelines: [
		"Use this tool to see what tickets are open / triaged / in progress / resolved / closed.",
		"Optional filters: status, priority, scenario_key.",
	],
	parameters: Type.Object({
		status: Type.Optional(Type.String({ description: "Filter by status: New / Triaged / In Progress / Resolved / Closed" })),
		priority: Type.Optional(Type.String({ description: "Filter by priority: P1 / P2 / P3" })),
		scenario_key: Type.Optional(Type.String({ description: "Filter by ERP scenario key" })),
		limit: Type.Optional(Type.Number({ description: "Max number of tickets to return (default 20)" })),
	}),
	async execute(_id, params) {
		const store = await readTicketsStore();
		const limit = Math.max(1, Math.min(params.limit ?? 20, 100));
		let rows = store.tickets.slice();
		if (params.status) rows = rows.filter((t: any) => t.status === params.status);
		if (params.priority) rows = rows.filter((t: any) => t.priority === params.priority);
		if (params.scenario_key) rows = rows.filter((t: any) => t.scenario_key === params.scenario_key);
		rows.sort((a: any, b: any) => asString(b.created_at, "").localeCompare(asString(a.created_at, "")));
		rows = rows.slice(0, limit);
		return {
			content: [{ type: "text", text: JSON.stringify({ count: rows.length, tickets: rows }, null, 2) }],
			details: { count: rows.length, tickets: rows },
		};
	},
});

const erpItGetTicket = defineTool({
	name: "erp_it_get_ticket",
	label: "Get IT Ticket",
	description: "Get full details for a single IT ticket by its KW-#### id, including evidence, comments, and history.",
	promptSnippet: "Show full details of one IT ticket.",
	promptGuidelines: [
		"Use when the user names a specific ticket (e.g. 'KW-1234') and wants the full record.",
	],
	parameters: Type.Object({
		ticket_id: Type.String({ description: "Ticket id, e.g. KW-1234" }),
	}),
	async execute(_id, params) {
		const store = await readTicketsStore();
		const t = store.tickets.find((x: any) => x.ticket_id === params.ticket_id);
		if (!t) {
			return {
				content: [{ type: "text", text: `Ticket ${params.ticket_id} not found.` }],
				details: { found: false, ticket_id: params.ticket_id },
			};
		}
		return {
			content: [{ type: "text", text: JSON.stringify(t, null, 2) }],
			details: t,
		};
	},
});

function updateTicketInStore(ticket_id: string, mutate: (t: any) => any): { ok: boolean; ticket?: any; error?: string } {
	const store = (() => {
		try {
			const fs = require("node:fs") as typeof import("node:fs");
			return JSON.parse(fs.readFileSync(ticketsPath, "utf8"));
		} catch {
			return { tickets: [] };
		}
	})();
	const idx = store.tickets.findIndex((t: any) => t.ticket_id === ticket_id);
	if (idx < 0) return { ok: false, error: `Ticket ${ticket_id} not found` };
	store.tickets[idx] = mutate(store.tickets[idx]);
	try {
		const fs = require("node:fs") as typeof import("node:fs");
		fs.writeFileSync(ticketsPath, JSON.stringify(store, null, 2), "utf8");
	} catch (e) {
		return { ok: false, error: `Failed to persist: ${(e as Error).message}` };
	}
	return { ok: true, ticket: store.tickets[idx] };
}

const erpItResolveTicket = defineTool({
	name: "erp_it_resolve_ticket",
	label: "Resolve IT Ticket",
	description: "Mark an IT ticket as Resolved with a resolution note. Use this when the issue has been fixed or answered.",
	promptSnippet: "Resolve an IT ticket with a note.",
	promptGuidelines: [
		"Use after you have actually fixed or answered the underlying issue.",
		"The resolution_note is required and shown to the requester.",
	],
	parameters: Type.Object({
		ticket_id: Type.String({ description: "Ticket id, e.g. KW-1234" }),
		resolution_note: Type.String({ description: "Short Japanese summary of what was done to resolve the issue" }),
	}),
	async execute(_id, params) {
		const result = updateTicketInStore(params.ticket_id, (t: any) => ({
			...t,
			status: "Resolved",
			resolution_note: params.resolution_note,
			resolved_at: nowIso(),
			history: [
				...(Array.isArray(t.history) ? t.history : []),
				{ at: nowIso(), action: "resolved", note: params.resolution_note },
			],
		}));
		return {
			content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
			details: result,
		};
	},
});

const erpItCloseTicket = defineTool({
	name: "erp_it_close_ticket",
	label: "Close IT Ticket",
	description: "Close a Resolved ticket (no further action). The requester can no longer reply.",
	promptSnippet: "Close a resolved IT ticket.",
	promptGuidelines: [
		"Only use after a ticket has been Resolved (or when the requester is unresponsive and you want to archive it).",
	],
	parameters: Type.Object({
		ticket_id: Type.String({ description: "Ticket id, e.g. KW-1234" }),
		close_note: Type.Optional(Type.String({ description: "Optional closing reason / archive note" })),
	}),
	async execute(_id, params) {
		const result = updateTicketInStore(params.ticket_id, (t: any) => ({
			...t,
			status: "Closed",
			close_note: params.close_note ?? "",
			closed_at: nowIso(),
			history: [
				...(Array.isArray(t.history) ? t.history : []),
				{ at: nowIso(), action: "closed", note: params.close_note ?? "" },
			],
		}));
		return {
			content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
			details: result,
		};
	},
});

const erpItReassignTicket = defineTool({
	name: "erp_it_reassign_ticket",
	label: "Reassign IT Ticket",
	description: "Change the routing team for an IT ticket (e.g. when the original route was wrong).",
	promptSnippet: "Reassign a ticket to another team.",
	promptGuidelines: [
		"Use when the ticket is in the wrong queue. Provide the new route string.",
	],
	parameters: Type.Object({
		ticket_id: Type.String({ description: "Ticket id, e.g. KW-1234" }),
		new_route: Type.String({ description: "New routing team, e.g. 'CRM Owner / Dynamics 管理者'" }),
		reason: Type.Optional(Type.String({ description: "Why the ticket is being reassigned" })),
	}),
	async execute(_id, params) {
		const result = updateTicketInStore(params.ticket_id, (t: any) => ({
			...t,
			route: params.new_route,
			reassign_reason: params.reason ?? "",
			history: [
				...(Array.isArray(t.history) ? t.history : []),
				{ at: nowIso(), action: "reassigned", to: params.new_route, note: params.reason ?? "" },
			],
		}));
		return {
			content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
			details: result,
		};
	},
});

const erpItAddComment = defineTool({
	name: "erp_it_add_comment",
	label: "Add IT Comment",
	description: "Append a comment to a ticket without changing its status.",
	promptSnippet: "Add a comment to an IT ticket.",
	promptGuidelines: [
		"Use to add information, ask the requester for more details, or document a workaround.",
	],
	parameters: Type.Object({
		ticket_id: Type.String({ description: "Ticket id, e.g. KW-1234" }),
		comment: Type.String({ description: "Comment text in Japanese" }),
	}),
	async execute(_id, params) {
		const result = updateTicketInStore(params.ticket_id, (t: any) => ({
			...t,
			comments: [
				...(Array.isArray(t.comments) ? t.comments : []),
				{ at: nowIso(), author: "IT Operations Agent P", comment: params.comment },
			],
			history: [
				...(Array.isArray(t.history) ? t.history : []),
				{ at: nowIso(), action: "comment", note: params.comment },
			],
		}));
		return {
			content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
			details: result,
		};
	},
});

const erpItTriageTicket = defineTool({
	name: "erp_it_triage_ticket",
	label: "Triage IT Ticket",
	description: "Triage a New ticket: confirm / re-classify priority and route before working on it.",
	promptSnippet: "Triage a new IT ticket.",
	promptGuidelines: [
		"Use for tickets in 'New' status before resolving.",
		"Can optionally change priority and route based on your assessment.",
	],
	parameters: Type.Object({
		ticket_id: Type.String({ description: "Ticket id, e.g. KW-1234" }),
		priority: Type.Optional(Type.String({ description: "Override priority: P1 / P2 / P3" })),
		new_route: Type.Optional(Type.String({ description: "Override routing team" })),
		notes: Type.Optional(Type.String({ description: "Triage notes" })),
	}),
	async execute(_id, params) {
		const result = updateTicketInStore(params.ticket_id, (t: any) => ({
			...t,
			status: "Triaged",
			priority: params.priority ?? t.priority,
			route: params.new_route ?? t.route,
			triage_notes: params.notes ?? "",
			triaged_at: nowIso(),
			history: [
				...(Array.isArray(t.history) ? t.history : []),
				{
					at: nowIso(),
					action: "triaged",
					priority: params.priority ?? t.priority,
					route: params.new_route ?? t.route,
					note: params.notes ?? "",
				},
			],
		}));
		return {
			content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
			details: result,
		};
	},
});

export default function erpAgentTools(pi: ExtensionAPI) {
	pi.registerTool(erpGetCurrentError);
	pi.registerTool(erpInspectCurrentErrorWithKb);
	pi.registerTool(erpAnalyzePastedErrorWithKb);
	pi.registerTool(erpQueryState);
	pi.registerTool(kbRgSearch);
	pi.registerTool(kbReadKnowledge);
	pi.registerTool(erpDraftTicket);
	pi.registerTool(erpCreateTicket);
	pi.registerTool(erpCreateTicketFromCurrentError);
	pi.registerTool(erpHandoff);
	pi.registerTool(erpExecuteAdminAction);
	// IT-side tools
	pi.registerTool(erpItListTickets);
	pi.registerTool(erpItGetTicket);
	pi.registerTool(erpItTriageTicket);
	pi.registerTool(erpItResolveTicket);
	pi.registerTool(erpItCloseTicket);
	pi.registerTool(erpItReassignTicket);
	pi.registerTool(erpItAddComment);
}
