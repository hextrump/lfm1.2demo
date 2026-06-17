# Helpdesk Routing and Priority Matrix

この文書は ERP/CRM SSO demo 用のローカル知識ベースです。
各規則は rg / grep 検索で参照されることを想定しています。

## Rule HD-001: Helpdesk Portal / Single user incident
- rule_id: HD-001
- system: Helpdesk Portal
- category: Single user incident
- route: Helpdesk L1
- priority: P3
- keywords: Helpdesk Portal, Single user incident, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Helpdesk Portal に関する Single user incident の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-002: ITSM / Multiple users incident
- rule_id: HD-002
- system: ITSM
- category: Multiple users incident
- route: Incident Manager
- priority: P3
- keywords: ITSM, Multiple users incident, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: ITSM に関する Multiple users incident の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Incident Manager にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-003: ServiceNow / Password reset
- rule_id: HD-003
- system: ServiceNow
- category: Password reset
- route: Application Owner
- priority: P3
- keywords: ServiceNow, Password reset, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: ServiceNow に関する Password reset の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Application Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-004: Jira Service Management / License request
- rule_id: HD-004
- system: Jira Service Management
- category: License request
- route: Helpdesk L1
- priority: P3
- keywords: Jira Service Management, License request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Jira Service Management に関する License request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-005: Helpdesk Portal / Access request
- rule_id: HD-005
- system: Helpdesk Portal
- category: Access request
- route: Incident Manager
- priority: P3
- keywords: Helpdesk Portal, Access request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Helpdesk Portal に関する Access request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Incident Manager にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-006: ITSM / Single user incident
- rule_id: HD-006
- system: ITSM
- category: Single user incident
- route: Application Owner
- priority: P3
- keywords: ITSM, Single user incident, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: ITSM に関する Single user incident の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Application Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-007: ServiceNow / Multiple users incident
- rule_id: HD-007
- system: ServiceNow
- category: Multiple users incident
- route: Helpdesk L1
- priority: P3
- keywords: ServiceNow, Multiple users incident, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: ServiceNow に関する Multiple users incident の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-008: Jira Service Management / Password reset
- rule_id: HD-008
- system: Jira Service Management
- category: Password reset
- route: Incident Manager
- priority: P3
- keywords: Jira Service Management, Password reset, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Jira Service Management に関する Password reset の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Incident Manager にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-009: Helpdesk Portal / License request
- rule_id: HD-009
- system: Helpdesk Portal
- category: License request
- route: Application Owner
- priority: P3
- keywords: Helpdesk Portal, License request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Helpdesk Portal に関する License request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Application Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-010: ITSM / Access request
- rule_id: HD-010
- system: ITSM
- category: Access request
- route: Helpdesk L1
- priority: P3
- keywords: ITSM, Access request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: ITSM に関する Access request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-011: ServiceNow / Single user incident
- rule_id: HD-011
- system: ServiceNow
- category: Single user incident
- route: Incident Manager
- priority: P3
- keywords: ServiceNow, Single user incident, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: ServiceNow に関する Single user incident の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Incident Manager にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-012: Jira Service Management / Multiple users incident
- rule_id: HD-012
- system: Jira Service Management
- category: Multiple users incident
- route: Application Owner
- priority: P3
- keywords: Jira Service Management, Multiple users incident, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Jira Service Management に関する Multiple users incident の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Application Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-013: Helpdesk Portal / Password reset
- rule_id: HD-013
- system: Helpdesk Portal
- category: Password reset
- route: Helpdesk L1
- priority: P3
- keywords: Helpdesk Portal, Password reset, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Helpdesk Portal に関する Password reset の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-014: ITSM / License request
- rule_id: HD-014
- system: ITSM
- category: License request
- route: Incident Manager
- priority: P3
- keywords: ITSM, License request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: ITSM に関する License request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Incident Manager にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-015: ServiceNow / Access request
- rule_id: HD-015
- system: ServiceNow
- category: Access request
- route: Application Owner
- priority: P3
- keywords: ServiceNow, Access request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: ServiceNow に関する Access request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Application Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-016: Jira Service Management / Single user incident
- rule_id: HD-016
- system: Jira Service Management
- category: Single user incident
- route: Helpdesk L1
- priority: P3
- keywords: Jira Service Management, Single user incident, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Jira Service Management に関する Single user incident の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-017: Helpdesk Portal / Multiple users incident
- rule_id: HD-017
- system: Helpdesk Portal
- category: Multiple users incident
- route: Incident Manager
- priority: P2
- keywords: Helpdesk Portal, Multiple users incident, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Helpdesk Portal に関する Multiple users incident の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Incident Manager にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-018: ITSM / Password reset
- rule_id: HD-018
- system: ITSM
- category: Password reset
- route: Application Owner
- priority: P3
- keywords: ITSM, Password reset, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: ITSM に関する Password reset の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Application Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-019: ServiceNow / License request
- rule_id: HD-019
- system: ServiceNow
- category: License request
- route: Helpdesk L1
- priority: P3
- keywords: ServiceNow, License request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: ServiceNow に関する License request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-020: Jira Service Management / Access request
- rule_id: HD-020
- system: Jira Service Management
- category: Access request
- route: Incident Manager
- priority: P3
- keywords: Jira Service Management, Access request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Jira Service Management に関する Access request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Incident Manager にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-021: Helpdesk Portal / Single user incident
- rule_id: HD-021
- system: Helpdesk Portal
- category: Single user incident
- route: Application Owner
- priority: P3
- keywords: Helpdesk Portal, Single user incident, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Helpdesk Portal に関する Single user incident の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Application Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-022: ITSM / Multiple users incident
- rule_id: HD-022
- system: ITSM
- category: Multiple users incident
- route: Helpdesk L1
- priority: P3
- keywords: ITSM, Multiple users incident, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: ITSM に関する Multiple users incident の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-023: ServiceNow / Password reset
- rule_id: HD-023
- system: ServiceNow
- category: Password reset
- route: Incident Manager
- priority: P3
- keywords: ServiceNow, Password reset, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: ServiceNow に関する Password reset の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Incident Manager にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-024: Jira Service Management / License request
- rule_id: HD-024
- system: Jira Service Management
- category: License request
- route: Application Owner
- priority: P3
- keywords: Jira Service Management, License request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Jira Service Management に関する License request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Application Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-025: Helpdesk Portal / Access request
- rule_id: HD-025
- system: Helpdesk Portal
- category: Access request
- route: Helpdesk L1
- priority: P3
- keywords: Helpdesk Portal, Access request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Helpdesk Portal に関する Access request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-026: ITSM / Single user incident
- rule_id: HD-026
- system: ITSM
- category: Single user incident
- route: Incident Manager
- priority: P3
- keywords: ITSM, Single user incident, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: ITSM に関する Single user incident の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Incident Manager にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-027: ServiceNow / Multiple users incident
- rule_id: HD-027
- system: ServiceNow
- category: Multiple users incident
- route: Application Owner
- priority: P3
- keywords: ServiceNow, Multiple users incident, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: ServiceNow に関する Multiple users incident の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Application Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-028: Jira Service Management / Password reset
- rule_id: HD-028
- system: Jira Service Management
- category: Password reset
- route: Helpdesk L1
- priority: P3
- keywords: Jira Service Management, Password reset, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Jira Service Management に関する Password reset の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-029: Helpdesk Portal / License request
- rule_id: HD-029
- system: Helpdesk Portal
- category: License request
- route: Incident Manager
- priority: P3
- keywords: Helpdesk Portal, License request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Helpdesk Portal に関する License request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Incident Manager にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-030: ITSM / Access request
- rule_id: HD-030
- system: ITSM
- category: Access request
- route: Application Owner
- priority: P3
- keywords: ITSM, Access request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: ITSM に関する Access request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Application Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-031: ServiceNow / Single user incident
- rule_id: HD-031
- system: ServiceNow
- category: Single user incident
- route: Helpdesk L1
- priority: P3
- keywords: ServiceNow, Single user incident, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: ServiceNow に関する Single user incident の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-032: Jira Service Management / Multiple users incident
- rule_id: HD-032
- system: Jira Service Management
- category: Multiple users incident
- route: Incident Manager
- priority: P3
- keywords: Jira Service Management, Multiple users incident, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Jira Service Management に関する Multiple users incident の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Incident Manager にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-033: Helpdesk Portal / Password reset
- rule_id: HD-033
- system: Helpdesk Portal
- category: Password reset
- route: Application Owner
- priority: P3
- keywords: Helpdesk Portal, Password reset, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Helpdesk Portal に関する Password reset の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Application Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-034: ITSM / License request
- rule_id: HD-034
- system: ITSM
- category: License request
- route: Helpdesk L1
- priority: P2
- keywords: ITSM, License request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: ITSM に関する License request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-035: ServiceNow / Access request
- rule_id: HD-035
- system: ServiceNow
- category: Access request
- route: Incident Manager
- priority: P3
- keywords: ServiceNow, Access request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: ServiceNow に関する Access request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Incident Manager にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-036: Jira Service Management / Single user incident
- rule_id: HD-036
- system: Jira Service Management
- category: Single user incident
- route: Application Owner
- priority: P3
- keywords: Jira Service Management, Single user incident, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Jira Service Management に関する Single user incident の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Application Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-037: Helpdesk Portal / Multiple users incident
- rule_id: HD-037
- system: Helpdesk Portal
- category: Multiple users incident
- route: Helpdesk L1
- priority: P3
- keywords: Helpdesk Portal, Multiple users incident, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Helpdesk Portal に関する Multiple users incident の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-038: ITSM / Password reset
- rule_id: HD-038
- system: ITSM
- category: Password reset
- route: Incident Manager
- priority: P3
- keywords: ITSM, Password reset, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: ITSM に関する Password reset の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Incident Manager にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-039: ServiceNow / License request
- rule_id: HD-039
- system: ServiceNow
- category: License request
- route: Application Owner
- priority: P3
- keywords: ServiceNow, License request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: ServiceNow に関する License request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Application Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule HD-040: Jira Service Management / Access request
- rule_id: HD-040
- system: Jira Service Management
- category: Access request
- route: Helpdesk L1
- priority: P3
- keywords: Jira Service Management, Access request, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Jira Service Management に関する Access request の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Helpdesk L1 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。
