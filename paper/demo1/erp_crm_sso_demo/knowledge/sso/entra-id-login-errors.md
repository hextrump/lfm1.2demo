# Entra ID / SSO Login Error Rules

この文書は ERP/CRM SSO demo 用のローカル知識ベースです。
各規則は rg / grep 検索で参照されることを想定しています。

## Rule SSO-001: Microsoft Entra ID / AADSTS50076 MFA 強認証
- rule_id: SSO-001
- system: Microsoft Entra ID
- category: AADSTS50076 MFA 強認証
- route: Identity / Entra ID 管理チーム
- priority: P3
- keywords: Microsoft Entra ID, AADSTS50076 MFA 強認証, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Microsoft Entra ID に関する AADSTS50076 MFA 強認証 の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity / Entra ID 管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-002: Dynamics 365 / AADSTS50105 User not assigned
- rule_id: SSO-002
- system: Dynamics 365
- category: AADSTS50105 User not assigned
- route: Helpdesk L1
- priority: P3
- keywords: Dynamics 365, AADSTS50105 User not assigned, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 に関する AADSTS50105 User not assigned の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-003: Salesforce / AADSTS50034 Account not found
- rule_id: SSO-003
- system: Salesforce
- category: AADSTS50034 Account not found
- route: Security / Conditional Access
- priority: P3
- keywords: Salesforce, AADSTS50034 Account not found, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce に関する AADSTS50034 Account not found の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security / Conditional Access にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-004: 社内ERP / Conditional Access blocked
- rule_id: SSO-004
- system: 社内ERP
- category: Conditional Access blocked
- route: Identity / Entra ID 管理チーム
- priority: P3
- keywords: 社内ERP, Conditional Access blocked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する Conditional Access blocked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity / Entra ID 管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-005: Microsoft Entra ID / Account locked
- rule_id: SSO-005
- system: Microsoft Entra ID
- category: Account locked
- route: Helpdesk L1
- priority: P3
- keywords: Microsoft Entra ID, Account locked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Microsoft Entra ID に関する Account locked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-006: Dynamics 365 / AADSTS50076 MFA 強認証
- rule_id: SSO-006
- system: Dynamics 365
- category: AADSTS50076 MFA 強認証
- route: Security / Conditional Access
- priority: P3
- keywords: Dynamics 365, AADSTS50076 MFA 強認証, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 に関する AADSTS50076 MFA 強認証 の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security / Conditional Access にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-007: Salesforce / AADSTS50105 User not assigned
- rule_id: SSO-007
- system: Salesforce
- category: AADSTS50105 User not assigned
- route: Identity / Entra ID 管理チーム
- priority: P3
- keywords: Salesforce, AADSTS50105 User not assigned, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce に関する AADSTS50105 User not assigned の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity / Entra ID 管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-008: 社内ERP / AADSTS50034 Account not found
- rule_id: SSO-008
- system: 社内ERP
- category: AADSTS50034 Account not found
- route: Helpdesk L1
- priority: P3
- keywords: 社内ERP, AADSTS50034 Account not found, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する AADSTS50034 Account not found の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-009: Microsoft Entra ID / Conditional Access blocked
- rule_id: SSO-009
- system: Microsoft Entra ID
- category: Conditional Access blocked
- route: Security / Conditional Access
- priority: P3
- keywords: Microsoft Entra ID, Conditional Access blocked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Microsoft Entra ID に関する Conditional Access blocked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security / Conditional Access にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-010: Dynamics 365 / Account locked
- rule_id: SSO-010
- system: Dynamics 365
- category: Account locked
- route: Identity / Entra ID 管理チーム
- priority: P3
- keywords: Dynamics 365, Account locked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 に関する Account locked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity / Entra ID 管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-011: Salesforce / AADSTS50076 MFA 強認証
- rule_id: SSO-011
- system: Salesforce
- category: AADSTS50076 MFA 強認証
- route: Helpdesk L1
- priority: P3
- keywords: Salesforce, AADSTS50076 MFA 強認証, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce に関する AADSTS50076 MFA 強認証 の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-012: 社内ERP / AADSTS50105 User not assigned
- rule_id: SSO-012
- system: 社内ERP
- category: AADSTS50105 User not assigned
- route: Security / Conditional Access
- priority: P3
- keywords: 社内ERP, AADSTS50105 User not assigned, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する AADSTS50105 User not assigned の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security / Conditional Access にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-013: Microsoft Entra ID / AADSTS50034 Account not found
- rule_id: SSO-013
- system: Microsoft Entra ID
- category: AADSTS50034 Account not found
- route: Identity / Entra ID 管理チーム
- priority: P3
- keywords: Microsoft Entra ID, AADSTS50034 Account not found, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Microsoft Entra ID に関する AADSTS50034 Account not found の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity / Entra ID 管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-014: Dynamics 365 / Conditional Access blocked
- rule_id: SSO-014
- system: Dynamics 365
- category: Conditional Access blocked
- route: Helpdesk L1
- priority: P3
- keywords: Dynamics 365, Conditional Access blocked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 に関する Conditional Access blocked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-015: Salesforce / Account locked
- rule_id: SSO-015
- system: Salesforce
- category: Account locked
- route: Security / Conditional Access
- priority: P3
- keywords: Salesforce, Account locked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce に関する Account locked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security / Conditional Access にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-016: 社内ERP / AADSTS50076 MFA 強認証
- rule_id: SSO-016
- system: 社内ERP
- category: AADSTS50076 MFA 強認証
- route: Identity / Entra ID 管理チーム
- priority: P3
- keywords: 社内ERP, AADSTS50076 MFA 強認証, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する AADSTS50076 MFA 強認証 の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity / Entra ID 管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-017: Microsoft Entra ID / AADSTS50105 User not assigned
- rule_id: SSO-017
- system: Microsoft Entra ID
- category: AADSTS50105 User not assigned
- route: Helpdesk L1
- priority: P2
- keywords: Microsoft Entra ID, AADSTS50105 User not assigned, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Microsoft Entra ID に関する AADSTS50105 User not assigned の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-018: Dynamics 365 / AADSTS50034 Account not found
- rule_id: SSO-018
- system: Dynamics 365
- category: AADSTS50034 Account not found
- route: Security / Conditional Access
- priority: P3
- keywords: Dynamics 365, AADSTS50034 Account not found, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 に関する AADSTS50034 Account not found の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security / Conditional Access にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-019: Salesforce / Conditional Access blocked
- rule_id: SSO-019
- system: Salesforce
- category: Conditional Access blocked
- route: Identity / Entra ID 管理チーム
- priority: P3
- keywords: Salesforce, Conditional Access blocked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce に関する Conditional Access blocked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity / Entra ID 管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-020: 社内ERP / Account locked
- rule_id: SSO-020
- system: 社内ERP
- category: Account locked
- route: Helpdesk L1
- priority: P3
- keywords: 社内ERP, Account locked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する Account locked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-021: Microsoft Entra ID / AADSTS50076 MFA 強認証
- rule_id: SSO-021
- system: Microsoft Entra ID
- category: AADSTS50076 MFA 強認証
- route: Security / Conditional Access
- priority: P3
- keywords: Microsoft Entra ID, AADSTS50076 MFA 強認証, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Microsoft Entra ID に関する AADSTS50076 MFA 強認証 の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security / Conditional Access にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-022: Dynamics 365 / AADSTS50105 User not assigned
- rule_id: SSO-022
- system: Dynamics 365
- category: AADSTS50105 User not assigned
- route: Identity / Entra ID 管理チーム
- priority: P3
- keywords: Dynamics 365, AADSTS50105 User not assigned, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 に関する AADSTS50105 User not assigned の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity / Entra ID 管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-023: Salesforce / AADSTS50034 Account not found
- rule_id: SSO-023
- system: Salesforce
- category: AADSTS50034 Account not found
- route: Helpdesk L1
- priority: P3
- keywords: Salesforce, AADSTS50034 Account not found, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce に関する AADSTS50034 Account not found の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-024: 社内ERP / Conditional Access blocked
- rule_id: SSO-024
- system: 社内ERP
- category: Conditional Access blocked
- route: Security / Conditional Access
- priority: P3
- keywords: 社内ERP, Conditional Access blocked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する Conditional Access blocked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security / Conditional Access にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-025: Microsoft Entra ID / Account locked
- rule_id: SSO-025
- system: Microsoft Entra ID
- category: Account locked
- route: Identity / Entra ID 管理チーム
- priority: P3
- keywords: Microsoft Entra ID, Account locked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Microsoft Entra ID に関する Account locked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity / Entra ID 管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-026: Dynamics 365 / AADSTS50076 MFA 強認証
- rule_id: SSO-026
- system: Dynamics 365
- category: AADSTS50076 MFA 強認証
- route: Helpdesk L1
- priority: P3
- keywords: Dynamics 365, AADSTS50076 MFA 強認証, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 に関する AADSTS50076 MFA 強認証 の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-027: Salesforce / AADSTS50105 User not assigned
- rule_id: SSO-027
- system: Salesforce
- category: AADSTS50105 User not assigned
- route: Security / Conditional Access
- priority: P3
- keywords: Salesforce, AADSTS50105 User not assigned, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce に関する AADSTS50105 User not assigned の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security / Conditional Access にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-028: 社内ERP / AADSTS50034 Account not found
- rule_id: SSO-028
- system: 社内ERP
- category: AADSTS50034 Account not found
- route: Identity / Entra ID 管理チーム
- priority: P3
- keywords: 社内ERP, AADSTS50034 Account not found, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する AADSTS50034 Account not found の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity / Entra ID 管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-029: Microsoft Entra ID / Conditional Access blocked
- rule_id: SSO-029
- system: Microsoft Entra ID
- category: Conditional Access blocked
- route: Helpdesk L1
- priority: P3
- keywords: Microsoft Entra ID, Conditional Access blocked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Microsoft Entra ID に関する Conditional Access blocked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-030: Dynamics 365 / Account locked
- rule_id: SSO-030
- system: Dynamics 365
- category: Account locked
- route: Security / Conditional Access
- priority: P3
- keywords: Dynamics 365, Account locked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 に関する Account locked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security / Conditional Access にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-031: Salesforce / AADSTS50076 MFA 強認証
- rule_id: SSO-031
- system: Salesforce
- category: AADSTS50076 MFA 強認証
- route: Identity / Entra ID 管理チーム
- priority: P3
- keywords: Salesforce, AADSTS50076 MFA 強認証, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce に関する AADSTS50076 MFA 強認証 の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity / Entra ID 管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-032: 社内ERP / AADSTS50105 User not assigned
- rule_id: SSO-032
- system: 社内ERP
- category: AADSTS50105 User not assigned
- route: Helpdesk L1
- priority: P3
- keywords: 社内ERP, AADSTS50105 User not assigned, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する AADSTS50105 User not assigned の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-033: Microsoft Entra ID / AADSTS50034 Account not found
- rule_id: SSO-033
- system: Microsoft Entra ID
- category: AADSTS50034 Account not found
- route: Security / Conditional Access
- priority: P3
- keywords: Microsoft Entra ID, AADSTS50034 Account not found, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Microsoft Entra ID に関する AADSTS50034 Account not found の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security / Conditional Access にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-034: Dynamics 365 / Conditional Access blocked
- rule_id: SSO-034
- system: Dynamics 365
- category: Conditional Access blocked
- route: Identity / Entra ID 管理チーム
- priority: P2
- keywords: Dynamics 365, Conditional Access blocked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 に関する Conditional Access blocked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity / Entra ID 管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-035: Salesforce / Account locked
- rule_id: SSO-035
- system: Salesforce
- category: Account locked
- route: Helpdesk L1
- priority: P3
- keywords: Salesforce, Account locked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce に関する Account locked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-036: 社内ERP / AADSTS50076 MFA 強認証
- rule_id: SSO-036
- system: 社内ERP
- category: AADSTS50076 MFA 強認証
- route: Security / Conditional Access
- priority: P3
- keywords: 社内ERP, AADSTS50076 MFA 強認証, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する AADSTS50076 MFA 強認証 の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security / Conditional Access にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-037: Microsoft Entra ID / AADSTS50105 User not assigned
- rule_id: SSO-037
- system: Microsoft Entra ID
- category: AADSTS50105 User not assigned
- route: Identity / Entra ID 管理チーム
- priority: P3
- keywords: Microsoft Entra ID, AADSTS50105 User not assigned, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Microsoft Entra ID に関する AADSTS50105 User not assigned の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity / Entra ID 管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-038: Dynamics 365 / AADSTS50034 Account not found
- rule_id: SSO-038
- system: Dynamics 365
- category: AADSTS50034 Account not found
- route: Helpdesk L1
- priority: P3
- keywords: Dynamics 365, AADSTS50034 Account not found, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 に関する AADSTS50034 Account not found の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-039: Salesforce / Conditional Access blocked
- rule_id: SSO-039
- system: Salesforce
- category: Conditional Access blocked
- route: Security / Conditional Access
- priority: P3
- keywords: Salesforce, Conditional Access blocked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce に関する Conditional Access blocked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security / Conditional Access にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-040: 社内ERP / Account locked
- rule_id: SSO-040
- system: 社内ERP
- category: Account locked
- route: Identity / Entra ID 管理チーム
- priority: P3
- keywords: 社内ERP, Account locked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する Account locked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity / Entra ID 管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-041: Microsoft Entra ID / AADSTS50076 MFA 強認証
- rule_id: SSO-041
- system: Microsoft Entra ID
- category: AADSTS50076 MFA 強認証
- route: Helpdesk L1
- priority: P3
- keywords: Microsoft Entra ID, AADSTS50076 MFA 強認証, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Microsoft Entra ID に関する AADSTS50076 MFA 強認証 の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-042: Dynamics 365 / AADSTS50105 User not assigned
- rule_id: SSO-042
- system: Dynamics 365
- category: AADSTS50105 User not assigned
- route: Security / Conditional Access
- priority: P3
- keywords: Dynamics 365, AADSTS50105 User not assigned, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 に関する AADSTS50105 User not assigned の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security / Conditional Access にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-043: Salesforce / AADSTS50034 Account not found
- rule_id: SSO-043
- system: Salesforce
- category: AADSTS50034 Account not found
- route: Identity / Entra ID 管理チーム
- priority: P3
- keywords: Salesforce, AADSTS50034 Account not found, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce に関する AADSTS50034 Account not found の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity / Entra ID 管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-044: 社内ERP / Conditional Access blocked
- rule_id: SSO-044
- system: 社内ERP
- category: Conditional Access blocked
- route: Helpdesk L1
- priority: P3
- keywords: 社内ERP, Conditional Access blocked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する Conditional Access blocked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-045: Microsoft Entra ID / Account locked
- rule_id: SSO-045
- system: Microsoft Entra ID
- category: Account locked
- route: Security / Conditional Access
- priority: P3
- keywords: Microsoft Entra ID, Account locked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Microsoft Entra ID に関する Account locked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security / Conditional Access にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-046: Dynamics 365 / AADSTS50076 MFA 強認証
- rule_id: SSO-046
- system: Dynamics 365
- category: AADSTS50076 MFA 強認証
- route: Identity / Entra ID 管理チーム
- priority: P3
- keywords: Dynamics 365, AADSTS50076 MFA 強認証, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 に関する AADSTS50076 MFA 強認証 の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity / Entra ID 管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-047: Salesforce / AADSTS50105 User not assigned
- rule_id: SSO-047
- system: Salesforce
- category: AADSTS50105 User not assigned
- route: Helpdesk L1
- priority: P3
- keywords: Salesforce, AADSTS50105 User not assigned, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce に関する AADSTS50105 User not assigned の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-048: 社内ERP / AADSTS50034 Account not found
- rule_id: SSO-048
- system: 社内ERP
- category: AADSTS50034 Account not found
- route: Security / Conditional Access
- priority: P3
- keywords: 社内ERP, AADSTS50034 Account not found, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する AADSTS50034 Account not found の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security / Conditional Access にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-049: Microsoft Entra ID / Conditional Access blocked
- rule_id: SSO-049
- system: Microsoft Entra ID
- category: Conditional Access blocked
- route: Identity / Entra ID 管理チーム
- priority: P3
- keywords: Microsoft Entra ID, Conditional Access blocked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Microsoft Entra ID に関する Conditional Access blocked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity / Entra ID 管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-050: Dynamics 365 / Account locked
- rule_id: SSO-050
- system: Dynamics 365
- category: Account locked
- route: Helpdesk L1
- priority: P3
- keywords: Dynamics 365, Account locked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 に関する Account locked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-051: Salesforce / AADSTS50076 MFA 強認証
- rule_id: SSO-051
- system: Salesforce
- category: AADSTS50076 MFA 強認証
- route: Security / Conditional Access
- priority: P2
- keywords: Salesforce, AADSTS50076 MFA 強認証, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce に関する AADSTS50076 MFA 強認証 の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security / Conditional Access にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-052: 社内ERP / AADSTS50105 User not assigned
- rule_id: SSO-052
- system: 社内ERP
- category: AADSTS50105 User not assigned
- route: Identity / Entra ID 管理チーム
- priority: P3
- keywords: 社内ERP, AADSTS50105 User not assigned, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する AADSTS50105 User not assigned の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity / Entra ID 管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-053: Microsoft Entra ID / AADSTS50034 Account not found
- rule_id: SSO-053
- system: Microsoft Entra ID
- category: AADSTS50034 Account not found
- route: Helpdesk L1
- priority: P3
- keywords: Microsoft Entra ID, AADSTS50034 Account not found, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Microsoft Entra ID に関する AADSTS50034 Account not found の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-054: Dynamics 365 / Conditional Access blocked
- rule_id: SSO-054
- system: Dynamics 365
- category: Conditional Access blocked
- route: Security / Conditional Access
- priority: P3
- keywords: Dynamics 365, Conditional Access blocked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 に関する Conditional Access blocked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security / Conditional Access にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-055: Salesforce / Account locked
- rule_id: SSO-055
- system: Salesforce
- category: Account locked
- route: Identity / Entra ID 管理チーム
- priority: P3
- keywords: Salesforce, Account locked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce に関する Account locked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity / Entra ID 管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-056: 社内ERP / AADSTS50076 MFA 強認証
- rule_id: SSO-056
- system: 社内ERP
- category: AADSTS50076 MFA 強認証
- route: Helpdesk L1
- priority: P3
- keywords: 社内ERP, AADSTS50076 MFA 強認証, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する AADSTS50076 MFA 強認証 の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-057: Microsoft Entra ID / AADSTS50105 User not assigned
- rule_id: SSO-057
- system: Microsoft Entra ID
- category: AADSTS50105 User not assigned
- route: Security / Conditional Access
- priority: P3
- keywords: Microsoft Entra ID, AADSTS50105 User not assigned, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Microsoft Entra ID に関する AADSTS50105 User not assigned の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security / Conditional Access にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-058: Dynamics 365 / AADSTS50034 Account not found
- rule_id: SSO-058
- system: Dynamics 365
- category: AADSTS50034 Account not found
- route: Identity / Entra ID 管理チーム
- priority: P3
- keywords: Dynamics 365, AADSTS50034 Account not found, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 に関する AADSTS50034 Account not found の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Identity / Entra ID 管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-059: Salesforce / Conditional Access blocked
- rule_id: SSO-059
- system: Salesforce
- category: Conditional Access blocked
- route: Helpdesk L1
- priority: P3
- keywords: Salesforce, Conditional Access blocked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce に関する Conditional Access blocked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule SSO-060: 社内ERP / Account locked
- rule_id: SSO-060
- system: 社内ERP
- category: Account locked
- route: Security / Conditional Access
- priority: P3
- keywords: 社内ERP, Account locked, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する Account locked の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Security / Conditional Access にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。
