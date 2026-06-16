# Security Exception and Vendor Access Rules

この文書は ERP/CRM SSO demo 用のローカル知識ベースです。
各規則は rg / grep 検索で参照されることを想定しています。

## Rule SEC-001: Vendor Access / MFA exception request
- rule_id: SEC-001
- system: Vendor Access
- category: MFA exception request
- route: Security Team
- priority: P3
- keywords: Vendor Access, MFA exception request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Vendor Access に関する MFA exception request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-002: Integration Account / No MFA vendor demand
- rule_id: SEC-002
- system: Integration Account
- category: No MFA vendor demand
- route: Identity Governance
- priority: P3
- keywords: Integration Account, No MFA vendor demand, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Integration Account に関する No MFA vendor demand の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity Governance にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-003: Service Principal / Global Admin risk
- rule_id: SEC-003
- system: Service Principal
- category: Global Admin risk
- route: IAM Approval Board
- priority: P3
- keywords: Service Principal, Global Admin risk, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Service Principal に関する Global Admin risk の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は IAM Approval Board にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-004: Conditional Access / API automation failed
- rule_id: SEC-004
- system: Conditional Access
- category: API automation failed
- route: Security Team
- priority: P3
- keywords: Conditional Access, API automation failed, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Conditional Access に関する API automation failed の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-005: Vendor Access / Privileged access
- rule_id: SEC-005
- system: Vendor Access
- category: Privileged access
- route: Identity Governance
- priority: P3
- keywords: Vendor Access, Privileged access, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Vendor Access に関する Privileged access の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity Governance にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-006: Integration Account / MFA exception request
- rule_id: SEC-006
- system: Integration Account
- category: MFA exception request
- route: IAM Approval Board
- priority: P3
- keywords: Integration Account, MFA exception request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Integration Account に関する MFA exception request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は IAM Approval Board にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-007: Service Principal / No MFA vendor demand
- rule_id: SEC-007
- system: Service Principal
- category: No MFA vendor demand
- route: Security Team
- priority: P3
- keywords: Service Principal, No MFA vendor demand, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Service Principal に関する No MFA vendor demand の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-008: Conditional Access / Global Admin risk
- rule_id: SEC-008
- system: Conditional Access
- category: Global Admin risk
- route: Identity Governance
- priority: P3
- keywords: Conditional Access, Global Admin risk, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Conditional Access に関する Global Admin risk の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity Governance にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-009: Vendor Access / API automation failed
- rule_id: SEC-009
- system: Vendor Access
- category: API automation failed
- route: IAM Approval Board
- priority: P3
- keywords: Vendor Access, API automation failed, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Vendor Access に関する API automation failed の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は IAM Approval Board にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-010: Integration Account / Privileged access
- rule_id: SEC-010
- system: Integration Account
- category: Privileged access
- route: Security Team
- priority: P3
- keywords: Integration Account, Privileged access, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Integration Account に関する Privileged access の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-011: Service Principal / MFA exception request
- rule_id: SEC-011
- system: Service Principal
- category: MFA exception request
- route: Identity Governance
- priority: P3
- keywords: Service Principal, MFA exception request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Service Principal に関する MFA exception request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity Governance にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-012: Conditional Access / No MFA vendor demand
- rule_id: SEC-012
- system: Conditional Access
- category: No MFA vendor demand
- route: IAM Approval Board
- priority: P3
- keywords: Conditional Access, No MFA vendor demand, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Conditional Access に関する No MFA vendor demand の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は IAM Approval Board にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-013: Vendor Access / Global Admin risk
- rule_id: SEC-013
- system: Vendor Access
- category: Global Admin risk
- route: Security Team
- priority: P3
- keywords: Vendor Access, Global Admin risk, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Vendor Access に関する Global Admin risk の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-014: Integration Account / API automation failed
- rule_id: SEC-014
- system: Integration Account
- category: API automation failed
- route: Identity Governance
- priority: P3
- keywords: Integration Account, API automation failed, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Integration Account に関する API automation failed の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity Governance にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-015: Service Principal / Privileged access
- rule_id: SEC-015
- system: Service Principal
- category: Privileged access
- route: IAM Approval Board
- priority: P3
- keywords: Service Principal, Privileged access, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Service Principal に関する Privileged access の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は IAM Approval Board にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-016: Conditional Access / MFA exception request
- rule_id: SEC-016
- system: Conditional Access
- category: MFA exception request
- route: Security Team
- priority: P3
- keywords: Conditional Access, MFA exception request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Conditional Access に関する MFA exception request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-017: Vendor Access / No MFA vendor demand
- rule_id: SEC-017
- system: Vendor Access
- category: No MFA vendor demand
- route: Identity Governance
- priority: P2
- keywords: Vendor Access, No MFA vendor demand, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Vendor Access に関する No MFA vendor demand の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity Governance にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-018: Integration Account / Global Admin risk
- rule_id: SEC-018
- system: Integration Account
- category: Global Admin risk
- route: IAM Approval Board
- priority: P3
- keywords: Integration Account, Global Admin risk, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Integration Account に関する Global Admin risk の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は IAM Approval Board にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-019: Service Principal / API automation failed
- rule_id: SEC-019
- system: Service Principal
- category: API automation failed
- route: Security Team
- priority: P3
- keywords: Service Principal, API automation failed, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Service Principal に関する API automation failed の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-020: Conditional Access / Privileged access
- rule_id: SEC-020
- system: Conditional Access
- category: Privileged access
- route: Identity Governance
- priority: P3
- keywords: Conditional Access, Privileged access, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Conditional Access に関する Privileged access の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity Governance にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-021: Vendor Access / MFA exception request
- rule_id: SEC-021
- system: Vendor Access
- category: MFA exception request
- route: IAM Approval Board
- priority: P3
- keywords: Vendor Access, MFA exception request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Vendor Access に関する MFA exception request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は IAM Approval Board にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-022: Integration Account / No MFA vendor demand
- rule_id: SEC-022
- system: Integration Account
- category: No MFA vendor demand
- route: Security Team
- priority: P3
- keywords: Integration Account, No MFA vendor demand, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Integration Account に関する No MFA vendor demand の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-023: Service Principal / Global Admin risk
- rule_id: SEC-023
- system: Service Principal
- category: Global Admin risk
- route: Identity Governance
- priority: P3
- keywords: Service Principal, Global Admin risk, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Service Principal に関する Global Admin risk の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity Governance にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-024: Conditional Access / API automation failed
- rule_id: SEC-024
- system: Conditional Access
- category: API automation failed
- route: IAM Approval Board
- priority: P3
- keywords: Conditional Access, API automation failed, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Conditional Access に関する API automation failed の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は IAM Approval Board にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-025: Vendor Access / Privileged access
- rule_id: SEC-025
- system: Vendor Access
- category: Privileged access
- route: Security Team
- priority: P3
- keywords: Vendor Access, Privileged access, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Vendor Access に関する Privileged access の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-026: Integration Account / MFA exception request
- rule_id: SEC-026
- system: Integration Account
- category: MFA exception request
- route: Identity Governance
- priority: P3
- keywords: Integration Account, MFA exception request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Integration Account に関する MFA exception request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity Governance にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-027: Service Principal / No MFA vendor demand
- rule_id: SEC-027
- system: Service Principal
- category: No MFA vendor demand
- route: IAM Approval Board
- priority: P3
- keywords: Service Principal, No MFA vendor demand, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Service Principal に関する No MFA vendor demand の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は IAM Approval Board にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-028: Conditional Access / Global Admin risk
- rule_id: SEC-028
- system: Conditional Access
- category: Global Admin risk
- route: Security Team
- priority: P3
- keywords: Conditional Access, Global Admin risk, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Conditional Access に関する Global Admin risk の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-029: Vendor Access / API automation failed
- rule_id: SEC-029
- system: Vendor Access
- category: API automation failed
- route: Identity Governance
- priority: P3
- keywords: Vendor Access, API automation failed, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Vendor Access に関する API automation failed の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity Governance にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-030: Integration Account / Privileged access
- rule_id: SEC-030
- system: Integration Account
- category: Privileged access
- route: IAM Approval Board
- priority: P3
- keywords: Integration Account, Privileged access, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Integration Account に関する Privileged access の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は IAM Approval Board にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-031: Service Principal / MFA exception request
- rule_id: SEC-031
- system: Service Principal
- category: MFA exception request
- route: Security Team
- priority: P3
- keywords: Service Principal, MFA exception request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Service Principal に関する MFA exception request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-032: Conditional Access / No MFA vendor demand
- rule_id: SEC-032
- system: Conditional Access
- category: No MFA vendor demand
- route: Identity Governance
- priority: P3
- keywords: Conditional Access, No MFA vendor demand, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Conditional Access に関する No MFA vendor demand の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity Governance にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-033: Vendor Access / Global Admin risk
- rule_id: SEC-033
- system: Vendor Access
- category: Global Admin risk
- route: IAM Approval Board
- priority: P3
- keywords: Vendor Access, Global Admin risk, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Vendor Access に関する Global Admin risk の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は IAM Approval Board にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-034: Integration Account / API automation failed
- rule_id: SEC-034
- system: Integration Account
- category: API automation failed
- route: Security Team
- priority: P2
- keywords: Integration Account, API automation failed, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Integration Account に関する API automation failed の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-035: Service Principal / Privileged access
- rule_id: SEC-035
- system: Service Principal
- category: Privileged access
- route: Identity Governance
- priority: P3
- keywords: Service Principal, Privileged access, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Service Principal に関する Privileged access の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity Governance にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-036: Conditional Access / MFA exception request
- rule_id: SEC-036
- system: Conditional Access
- category: MFA exception request
- route: IAM Approval Board
- priority: P3
- keywords: Conditional Access, MFA exception request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Conditional Access に関する MFA exception request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は IAM Approval Board にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-037: Vendor Access / No MFA vendor demand
- rule_id: SEC-037
- system: Vendor Access
- category: No MFA vendor demand
- route: Security Team
- priority: P3
- keywords: Vendor Access, No MFA vendor demand, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Vendor Access に関する No MFA vendor demand の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-038: Integration Account / Global Admin risk
- rule_id: SEC-038
- system: Integration Account
- category: Global Admin risk
- route: Identity Governance
- priority: P3
- keywords: Integration Account, Global Admin risk, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Integration Account に関する Global Admin risk の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity Governance にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-039: Service Principal / API automation failed
- rule_id: SEC-039
- system: Service Principal
- category: API automation failed
- route: IAM Approval Board
- priority: P3
- keywords: Service Principal, API automation failed, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Service Principal に関する API automation failed の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は IAM Approval Board にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-040: Conditional Access / Privileged access
- rule_id: SEC-040
- system: Conditional Access
- category: Privileged access
- route: Security Team
- priority: P3
- keywords: Conditional Access, Privileged access, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Conditional Access に関する Privileged access の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-041: Vendor Access / MFA exception request
- rule_id: SEC-041
- system: Vendor Access
- category: MFA exception request
- route: Identity Governance
- priority: P3
- keywords: Vendor Access, MFA exception request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Vendor Access に関する MFA exception request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity Governance にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-042: Integration Account / No MFA vendor demand
- rule_id: SEC-042
- system: Integration Account
- category: No MFA vendor demand
- route: IAM Approval Board
- priority: P3
- keywords: Integration Account, No MFA vendor demand, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Integration Account に関する No MFA vendor demand の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は IAM Approval Board にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-043: Service Principal / Global Admin risk
- rule_id: SEC-043
- system: Service Principal
- category: Global Admin risk
- route: Security Team
- priority: P3
- keywords: Service Principal, Global Admin risk, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Service Principal に関する Global Admin risk の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-044: Conditional Access / API automation failed
- rule_id: SEC-044
- system: Conditional Access
- category: API automation failed
- route: Identity Governance
- priority: P3
- keywords: Conditional Access, API automation failed, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Conditional Access に関する API automation failed の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity Governance にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SEC-045: Vendor Access / Privileged access
- rule_id: SEC-045
- system: Vendor Access
- category: Privileged access
- route: IAM Approval Board
- priority: P3
- keywords: Vendor Access, Privileged access, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Vendor Access に関する Privileged access の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は IAM Approval Board にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。
