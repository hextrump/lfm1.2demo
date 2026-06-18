"""Test scenario fixtures — mirror the SCENARIOS dict in app.py and the
scenarios in runtime/pi_erp_extension.ts so runtime tests can construct
realistic current_error.json payloads."""

AADSTS50076 = {
    "active": True,
    "scenario_key": "AADSTS50076",
    "system": "Dynamics 365",
    "title": "Additional authentication required",
    "error_text": "Due to a configuration change made by your administrator, or because you moved to a new location, you must use multi-factor authentication.",
    "error_code": "AADSTS50076",
    "symptom": "login_failed",
    "category": "Microsoft Entra ID / MFA / Conditional Access",
    "risk": "Medium",
    "priority": "P3",
    "route": "Identity / Entra ID 管理チーム",
    "impact": "single_user",
    "trace_id": "trc-aadsts50076-test01",
    "correlation_id": "corr-test-20260618",
    "timestamp": "2026-06-18 11:00:01 JST",
    "user_email": "taro.yamada@demo.local",
    "user_name": "山田 太郎",
    "department": "営業部",
    "role": "Sales",
    "location": "Tokyo HQ",
}

AADSTS50105 = {
    **AADSTS50076,
    "scenario_key": "AADSTS50105",
    "title": "User not assigned to app",
    "error_text": "The signed in user is not assigned to a role for the application.",
    "error_code": "AADSTS50105",
    "symptom": "app_assignment_missing",
    "category": "Application Assignment / Permission",
    "route": "業務システム権限管理チーム",
}

LICENSE_MISSING = {
    **AADSTS50076,
    "scenario_key": "LICENSE_MISSING",
    "title": "License required",
    "error_text": "This user does not have the required Dynamics 365 license.",
    "error_code": "LICENSE_MISSING",
    "symptom": "license_missing",
    "category": "License / Microsoft 365",
    "route": "Microsoft 365 ライセンス管理チーム",
}

CA_BLOCK = {
    **AADSTS50076,
    "scenario_key": "CA_BLOCK",
    "title": "Access blocked by policy",
    "error_text": "Access has been blocked by Conditional Access policy.",
    "error_code": "CA_BLOCK",
    "symptom": "conditional_access_block",
    "category": "Security / Conditional Access",
    "risk": "High",
    "priority": "P2",
    "route": "Security / Conditional Access チーム",
}

CRM_MENU_MISSING = {
    **AADSTS50076,
    "scenario_key": "CRM_MENU_MISSING",
    "title": "CRM menu missing after login",
    "error_text": "Login succeeded, but Sales Hub menu and customer opportunities are not visible.",
    "error_code": "NO_ERROR_CODE",
    "symptom": "menu_missing",
    "category": "CRM Role / Business Unit Permission",
    "route": "CRM Owner / Dynamics 管理者",
}

POWERBI_DENIED = {
    **AADSTS50076,
    "scenario_key": "POWERBI_DENIED",
    "title": "Power BI report access denied",
    "error_text": "You do not have permission to view this report or dataset.",
    "error_code": "PBI_ACCESS_DENIED",
    "symptom": "report_permission_denied",
    "category": "Power BI Workspace / Dataset Permission",
    "risk": "Low",
    "route": "BI 管理者 / Data Platform Team",
}

MULTI_USER_OUTAGE = {
    **AADSTS50076,
    "scenario_key": "MULTI_USER_OUTAGE",
    "title": "Service access degraded",
    "error_text": "Multiple affected users. Service incident signal.",
    "error_code": "MULTI_USER_OUTAGE",
    "symptom": "multi_user_outage",
    "category": "IT Ops / Service Incident",
    "risk": "High",
    "priority": "P2",
    "route": "IT Ops / Incident Manager",
    "impact": "multiple_users",
}

VENDOR_MFA_EXCEPTION = {
    **AADSTS50076,
    "scenario_key": "VENDOR_MFA_EXCEPTION",
    "title": "Vendor MFA exception requested",
    "error_text": "Integration account needs MFA exception.",
    "error_code": "VENDOR_MFA_EXCEPTION",
    "symptom": "vendor_mfa_exception",
    "category": "Security Exception / Vendor Access",
    "risk": "High",
    "priority": "P2",
    "route": "Security Team + IAM Approval Board",
    "impact": "privileged_account",
}

SCENARIOS = {
    "AADSTS50076": AADSTS50076,
    "AADSTS50105": AADSTS50105,
    "LICENSE_MISSING": LICENSE_MISSING,
    "CA_BLOCK": CA_BLOCK,
    "CRM_MENU_MISSING": CRM_MENU_MISSING,
    "POWERBI_DENIED": POWERBI_DENIED,
    "MULTI_USER_OUTAGE": MULTI_USER_OUTAGE,
    "VENDOR_MFA_EXCEPTION": VENDOR_MFA_EXCEPTION,
}
