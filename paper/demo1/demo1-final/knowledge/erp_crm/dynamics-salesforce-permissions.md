# ERP CRM Permission Rules

この文書は ERP/CRM SSO demo 用のローカル知識ベースです。
各規則は rg / grep 検索で参照されることを想定しています。

## Rule CRM-001: Dynamics 365 Sales / Security role missing
- rule_id: CRM-001
- system: Dynamics 365 Sales
- category: Security role missing
- route: Dynamics 管理者
- priority: P3
- keywords: Dynamics 365 Sales, Security role missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Sales に関する Security role missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Dynamics 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-002: Dynamics 365 Finance / Business unit mismatch
- rule_id: CRM-002
- system: Dynamics 365 Finance
- category: Business unit mismatch
- route: CRM Owner
- priority: P3
- keywords: Dynamics 365 Finance, Business unit mismatch, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Finance に関する Business unit mismatch の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は CRM Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-003: Salesforce Sales Cloud / Menu hidden
- rule_id: CRM-003
- system: Salesforce Sales Cloud
- category: Menu hidden
- route: 業務システム権限管理チーム
- priority: P3
- keywords: Salesforce Sales Cloud, Menu hidden, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce Sales Cloud に関する Menu hidden の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は 業務システム権限管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-004: 社内ERP / Button disabled
- rule_id: CRM-004
- system: 社内ERP
- category: Button disabled
- route: Dynamics 管理者
- priority: P3
- keywords: 社内ERP, Button disabled, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する Button disabled の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Dynamics 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-005: Dynamics 365 Sales / Customer data access denied
- rule_id: CRM-005
- system: Dynamics 365 Sales
- category: Customer data access denied
- route: CRM Owner
- priority: P3
- keywords: Dynamics 365 Sales, Customer data access denied, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Sales に関する Customer data access denied の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は CRM Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-006: Dynamics 365 Finance / Security role missing
- rule_id: CRM-006
- system: Dynamics 365 Finance
- category: Security role missing
- route: 業務システム権限管理チーム
- priority: P3
- keywords: Dynamics 365 Finance, Security role missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Finance に関する Security role missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は 業務システム権限管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-007: Salesforce Sales Cloud / Business unit mismatch
- rule_id: CRM-007
- system: Salesforce Sales Cloud
- category: Business unit mismatch
- route: Dynamics 管理者
- priority: P3
- keywords: Salesforce Sales Cloud, Business unit mismatch, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce Sales Cloud に関する Business unit mismatch の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Dynamics 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-008: 社内ERP / Menu hidden
- rule_id: CRM-008
- system: 社内ERP
- category: Menu hidden
- route: CRM Owner
- priority: P3
- keywords: 社内ERP, Menu hidden, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する Menu hidden の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は CRM Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-009: Dynamics 365 Sales / Button disabled
- rule_id: CRM-009
- system: Dynamics 365 Sales
- category: Button disabled
- route: 業務システム権限管理チーム
- priority: P3
- keywords: Dynamics 365 Sales, Button disabled, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Sales に関する Button disabled の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は 業務システム権限管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-010: Dynamics 365 Finance / Customer data access denied
- rule_id: CRM-010
- system: Dynamics 365 Finance
- category: Customer data access denied
- route: Dynamics 管理者
- priority: P3
- keywords: Dynamics 365 Finance, Customer data access denied, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Finance に関する Customer data access denied の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Dynamics 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-011: Salesforce Sales Cloud / Security role missing
- rule_id: CRM-011
- system: Salesforce Sales Cloud
- category: Security role missing
- route: CRM Owner
- priority: P3
- keywords: Salesforce Sales Cloud, Security role missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce Sales Cloud に関する Security role missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は CRM Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-012: 社内ERP / Business unit mismatch
- rule_id: CRM-012
- system: 社内ERP
- category: Business unit mismatch
- route: 業務システム権限管理チーム
- priority: P3
- keywords: 社内ERP, Business unit mismatch, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する Business unit mismatch の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は 業務システム権限管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-013: Dynamics 365 Sales / Menu hidden
- rule_id: CRM-013
- system: Dynamics 365 Sales
- category: Menu hidden
- route: Dynamics 管理者
- priority: P3
- keywords: Dynamics 365 Sales, Menu hidden, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Sales に関する Menu hidden の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Dynamics 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-014: Dynamics 365 Finance / Button disabled
- rule_id: CRM-014
- system: Dynamics 365 Finance
- category: Button disabled
- route: CRM Owner
- priority: P3
- keywords: Dynamics 365 Finance, Button disabled, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Finance に関する Button disabled の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は CRM Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-015: Salesforce Sales Cloud / Customer data access denied
- rule_id: CRM-015
- system: Salesforce Sales Cloud
- category: Customer data access denied
- route: 業務システム権限管理チーム
- priority: P3
- keywords: Salesforce Sales Cloud, Customer data access denied, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce Sales Cloud に関する Customer data access denied の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は 業務システム権限管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-016: 社内ERP / Security role missing
- rule_id: CRM-016
- system: 社内ERP
- category: Security role missing
- route: Dynamics 管理者
- priority: P3
- keywords: 社内ERP, Security role missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する Security role missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Dynamics 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-017: Dynamics 365 Sales / Business unit mismatch
- rule_id: CRM-017
- system: Dynamics 365 Sales
- category: Business unit mismatch
- route: CRM Owner
- priority: P2
- keywords: Dynamics 365 Sales, Business unit mismatch, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Sales に関する Business unit mismatch の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は CRM Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-018: Dynamics 365 Finance / Menu hidden
- rule_id: CRM-018
- system: Dynamics 365 Finance
- category: Menu hidden
- route: 業務システム権限管理チーム
- priority: P3
- keywords: Dynamics 365 Finance, Menu hidden, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Finance に関する Menu hidden の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は 業務システム権限管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-019: Salesforce Sales Cloud / Button disabled
- rule_id: CRM-019
- system: Salesforce Sales Cloud
- category: Button disabled
- route: Dynamics 管理者
- priority: P3
- keywords: Salesforce Sales Cloud, Button disabled, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce Sales Cloud に関する Button disabled の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Dynamics 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-020: 社内ERP / Customer data access denied
- rule_id: CRM-020
- system: 社内ERP
- category: Customer data access denied
- route: CRM Owner
- priority: P3
- keywords: 社内ERP, Customer data access denied, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する Customer data access denied の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は CRM Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-021: Dynamics 365 Sales / Security role missing
- rule_id: CRM-021
- system: Dynamics 365 Sales
- category: Security role missing
- route: 業務システム権限管理チーム
- priority: P3
- keywords: Dynamics 365 Sales, Security role missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Sales に関する Security role missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は 業務システム権限管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-022: Dynamics 365 Finance / Business unit mismatch
- rule_id: CRM-022
- system: Dynamics 365 Finance
- category: Business unit mismatch
- route: Dynamics 管理者
- priority: P3
- keywords: Dynamics 365 Finance, Business unit mismatch, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Finance に関する Business unit mismatch の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Dynamics 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-023: Salesforce Sales Cloud / Menu hidden
- rule_id: CRM-023
- system: Salesforce Sales Cloud
- category: Menu hidden
- route: CRM Owner
- priority: P3
- keywords: Salesforce Sales Cloud, Menu hidden, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce Sales Cloud に関する Menu hidden の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は CRM Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-024: 社内ERP / Button disabled
- rule_id: CRM-024
- system: 社内ERP
- category: Button disabled
- route: 業務システム権限管理チーム
- priority: P3
- keywords: 社内ERP, Button disabled, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する Button disabled の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は 業務システム権限管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-025: Dynamics 365 Sales / Customer data access denied
- rule_id: CRM-025
- system: Dynamics 365 Sales
- category: Customer data access denied
- route: Dynamics 管理者
- priority: P3
- keywords: Dynamics 365 Sales, Customer data access denied, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Sales に関する Customer data access denied の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Dynamics 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-026: Dynamics 365 Finance / Security role missing
- rule_id: CRM-026
- system: Dynamics 365 Finance
- category: Security role missing
- route: CRM Owner
- priority: P3
- keywords: Dynamics 365 Finance, Security role missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Finance に関する Security role missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は CRM Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-027: Salesforce Sales Cloud / Business unit mismatch
- rule_id: CRM-027
- system: Salesforce Sales Cloud
- category: Business unit mismatch
- route: 業務システム権限管理チーム
- priority: P3
- keywords: Salesforce Sales Cloud, Business unit mismatch, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce Sales Cloud に関する Business unit mismatch の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は 業務システム権限管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-028: 社内ERP / Menu hidden
- rule_id: CRM-028
- system: 社内ERP
- category: Menu hidden
- route: Dynamics 管理者
- priority: P3
- keywords: 社内ERP, Menu hidden, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する Menu hidden の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Dynamics 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-029: Dynamics 365 Sales / Button disabled
- rule_id: CRM-029
- system: Dynamics 365 Sales
- category: Button disabled
- route: CRM Owner
- priority: P3
- keywords: Dynamics 365 Sales, Button disabled, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Sales に関する Button disabled の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は CRM Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-030: Dynamics 365 Finance / Customer data access denied
- rule_id: CRM-030
- system: Dynamics 365 Finance
- category: Customer data access denied
- route: 業務システム権限管理チーム
- priority: P3
- keywords: Dynamics 365 Finance, Customer data access denied, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Finance に関する Customer data access denied の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は 業務システム権限管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-031: Salesforce Sales Cloud / Security role missing
- rule_id: CRM-031
- system: Salesforce Sales Cloud
- category: Security role missing
- route: Dynamics 管理者
- priority: P3
- keywords: Salesforce Sales Cloud, Security role missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce Sales Cloud に関する Security role missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Dynamics 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-032: 社内ERP / Business unit mismatch
- rule_id: CRM-032
- system: 社内ERP
- category: Business unit mismatch
- route: CRM Owner
- priority: P3
- keywords: 社内ERP, Business unit mismatch, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する Business unit mismatch の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は CRM Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-033: Dynamics 365 Sales / Menu hidden
- rule_id: CRM-033
- system: Dynamics 365 Sales
- category: Menu hidden
- route: 業務システム権限管理チーム
- priority: P3
- keywords: Dynamics 365 Sales, Menu hidden, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Sales に関する Menu hidden の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は 業務システム権限管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-034: Dynamics 365 Finance / Button disabled
- rule_id: CRM-034
- system: Dynamics 365 Finance
- category: Button disabled
- route: Dynamics 管理者
- priority: P2
- keywords: Dynamics 365 Finance, Button disabled, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Finance に関する Button disabled の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Dynamics 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-035: Salesforce Sales Cloud / Customer data access denied
- rule_id: CRM-035
- system: Salesforce Sales Cloud
- category: Customer data access denied
- route: CRM Owner
- priority: P3
- keywords: Salesforce Sales Cloud, Customer data access denied, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce Sales Cloud に関する Customer data access denied の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は CRM Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-036: 社内ERP / Security role missing
- rule_id: CRM-036
- system: 社内ERP
- category: Security role missing
- route: 業務システム権限管理チーム
- priority: P3
- keywords: 社内ERP, Security role missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する Security role missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は 業務システム権限管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-037: Dynamics 365 Sales / Business unit mismatch
- rule_id: CRM-037
- system: Dynamics 365 Sales
- category: Business unit mismatch
- route: Dynamics 管理者
- priority: P3
- keywords: Dynamics 365 Sales, Business unit mismatch, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Sales に関する Business unit mismatch の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Dynamics 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-038: Dynamics 365 Finance / Menu hidden
- rule_id: CRM-038
- system: Dynamics 365 Finance
- category: Menu hidden
- route: CRM Owner
- priority: P3
- keywords: Dynamics 365 Finance, Menu hidden, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Finance に関する Menu hidden の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は CRM Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-039: Salesforce Sales Cloud / Button disabled
- rule_id: CRM-039
- system: Salesforce Sales Cloud
- category: Button disabled
- route: 業務システム権限管理チーム
- priority: P3
- keywords: Salesforce Sales Cloud, Button disabled, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce Sales Cloud に関する Button disabled の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は 業務システム権限管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-040: 社内ERP / Customer data access denied
- rule_id: CRM-040
- system: 社内ERP
- category: Customer data access denied
- route: Dynamics 管理者
- priority: P3
- keywords: 社内ERP, Customer data access denied, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する Customer data access denied の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Dynamics 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-041: Dynamics 365 Sales / Security role missing
- rule_id: CRM-041
- system: Dynamics 365 Sales
- category: Security role missing
- route: CRM Owner
- priority: P3
- keywords: Dynamics 365 Sales, Security role missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Sales に関する Security role missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は CRM Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-042: Dynamics 365 Finance / Business unit mismatch
- rule_id: CRM-042
- system: Dynamics 365 Finance
- category: Business unit mismatch
- route: 業務システム権限管理チーム
- priority: P3
- keywords: Dynamics 365 Finance, Business unit mismatch, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Finance に関する Business unit mismatch の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は 業務システム権限管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-043: Salesforce Sales Cloud / Menu hidden
- rule_id: CRM-043
- system: Salesforce Sales Cloud
- category: Menu hidden
- route: Dynamics 管理者
- priority: P3
- keywords: Salesforce Sales Cloud, Menu hidden, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce Sales Cloud に関する Menu hidden の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Dynamics 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-044: 社内ERP / Button disabled
- rule_id: CRM-044
- system: 社内ERP
- category: Button disabled
- route: CRM Owner
- priority: P3
- keywords: 社内ERP, Button disabled, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する Button disabled の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は CRM Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-045: Dynamics 365 Sales / Customer data access denied
- rule_id: CRM-045
- system: Dynamics 365 Sales
- category: Customer data access denied
- route: 業務システム権限管理チーム
- priority: P3
- keywords: Dynamics 365 Sales, Customer data access denied, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Sales に関する Customer data access denied の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は 業務システム権限管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-046: Dynamics 365 Finance / Security role missing
- rule_id: CRM-046
- system: Dynamics 365 Finance
- category: Security role missing
- route: Dynamics 管理者
- priority: P3
- keywords: Dynamics 365 Finance, Security role missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Finance に関する Security role missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Dynamics 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-047: Salesforce Sales Cloud / Business unit mismatch
- rule_id: CRM-047
- system: Salesforce Sales Cloud
- category: Business unit mismatch
- route: CRM Owner
- priority: P3
- keywords: Salesforce Sales Cloud, Business unit mismatch, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce Sales Cloud に関する Business unit mismatch の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は CRM Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-048: 社内ERP / Menu hidden
- rule_id: CRM-048
- system: 社内ERP
- category: Menu hidden
- route: 業務システム権限管理チーム
- priority: P3
- keywords: 社内ERP, Menu hidden, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する Menu hidden の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は 業務システム権限管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-049: Dynamics 365 Sales / Button disabled
- rule_id: CRM-049
- system: Dynamics 365 Sales
- category: Button disabled
- route: Dynamics 管理者
- priority: P3
- keywords: Dynamics 365 Sales, Button disabled, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Sales に関する Button disabled の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Dynamics 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-050: Dynamics 365 Finance / Customer data access denied
- rule_id: CRM-050
- system: Dynamics 365 Finance
- category: Customer data access denied
- route: CRM Owner
- priority: P3
- keywords: Dynamics 365 Finance, Customer data access denied, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Finance に関する Customer data access denied の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は CRM Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-051: Salesforce Sales Cloud / Security role missing
- rule_id: CRM-051
- system: Salesforce Sales Cloud
- category: Security role missing
- route: 業務システム権限管理チーム
- priority: P2
- keywords: Salesforce Sales Cloud, Security role missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce Sales Cloud に関する Security role missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は 業務システム権限管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-052: 社内ERP / Business unit mismatch
- rule_id: CRM-052
- system: 社内ERP
- category: Business unit mismatch
- route: Dynamics 管理者
- priority: P3
- keywords: 社内ERP, Business unit mismatch, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する Business unit mismatch の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Dynamics 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-053: Dynamics 365 Sales / Menu hidden
- rule_id: CRM-053
- system: Dynamics 365 Sales
- category: Menu hidden
- route: CRM Owner
- priority: P3
- keywords: Dynamics 365 Sales, Menu hidden, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Sales に関する Menu hidden の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は CRM Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-054: Dynamics 365 Finance / Button disabled
- rule_id: CRM-054
- system: Dynamics 365 Finance
- category: Button disabled
- route: 業務システム権限管理チーム
- priority: P3
- keywords: Dynamics 365 Finance, Button disabled, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Finance に関する Button disabled の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は 業務システム権限管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-055: Salesforce Sales Cloud / Customer data access denied
- rule_id: CRM-055
- system: Salesforce Sales Cloud
- category: Customer data access denied
- route: Dynamics 管理者
- priority: P3
- keywords: Salesforce Sales Cloud, Customer data access denied, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce Sales Cloud に関する Customer data access denied の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Dynamics 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-056: 社内ERP / Security role missing
- rule_id: CRM-056
- system: 社内ERP
- category: Security role missing
- route: CRM Owner
- priority: P3
- keywords: 社内ERP, Security role missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する Security role missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は CRM Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-057: Dynamics 365 Sales / Business unit mismatch
- rule_id: CRM-057
- system: Dynamics 365 Sales
- category: Business unit mismatch
- route: 業務システム権限管理チーム
- priority: P3
- keywords: Dynamics 365 Sales, Business unit mismatch, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Sales に関する Business unit mismatch の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は 業務システム権限管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-058: Dynamics 365 Finance / Menu hidden
- rule_id: CRM-058
- system: Dynamics 365 Finance
- category: Menu hidden
- route: Dynamics 管理者
- priority: P3
- keywords: Dynamics 365 Finance, Menu hidden, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Dynamics 365 Finance に関する Menu hidden の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Dynamics 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-059: Salesforce Sales Cloud / Button disabled
- rule_id: CRM-059
- system: Salesforce Sales Cloud
- category: Button disabled
- route: CRM Owner
- priority: P3
- keywords: Salesforce Sales Cloud, Button disabled, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Salesforce Sales Cloud に関する Button disabled の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は CRM Owner にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule CRM-060: 社内ERP / Customer data access denied
- rule_id: CRM-060
- system: 社内ERP
- category: Customer data access denied
- route: 業務システム権限管理チーム
- priority: P3
- keywords: 社内ERP, Customer data access denied, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: 社内ERP に関する Customer data access denied の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は 業務システム権限管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。
