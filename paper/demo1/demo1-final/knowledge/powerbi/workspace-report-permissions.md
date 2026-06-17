# Power BI Report Permission Rules

この文書は ERP/CRM SSO demo 用のローカル知識ベースです。
各規則は rg / grep 検索で参照されることを想定しています。

## Rule PBI-001: Power BI / Workspace permission denied
- rule_id: PBI-001
- system: Power BI
- category: Workspace permission denied
- route: BI 管理者
- priority: P3
- keywords: Power BI, Workspace permission denied, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Power BI に関する Workspace permission denied の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は BI 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-002: Fabric Workspace / Dataset permission missing
- rule_id: PBI-002
- system: Fabric Workspace
- category: Dataset permission missing
- route: Data Platform Team
- priority: P3
- keywords: Fabric Workspace, Dataset permission missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Fabric Workspace に関する Dataset permission missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Data Platform Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-003: Owner App / Report app not installed
- rule_id: PBI-003
- system: Owner App
- category: Report app not installed
- route: Microsoft 365 ライセンス管理チーム
- priority: P3
- keywords: Owner App, Report app not installed, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Owner App に関する Report app not installed の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Microsoft 365 ライセンス管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-004: Executive Dashboard / RLS filtered
- rule_id: PBI-004
- system: Executive Dashboard
- category: RLS filtered
- route: BI 管理者
- priority: P3
- keywords: Executive Dashboard, RLS filtered, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Executive Dashboard に関する RLS filtered の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は BI 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-005: Power BI / License missing
- rule_id: PBI-005
- system: Power BI
- category: License missing
- route: Data Platform Team
- priority: P3
- keywords: Power BI, License missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Power BI に関する License missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Data Platform Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-006: Fabric Workspace / Workspace permission denied
- rule_id: PBI-006
- system: Fabric Workspace
- category: Workspace permission denied
- route: Microsoft 365 ライセンス管理チーム
- priority: P3
- keywords: Fabric Workspace, Workspace permission denied, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Fabric Workspace に関する Workspace permission denied の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Microsoft 365 ライセンス管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-007: Owner App / Dataset permission missing
- rule_id: PBI-007
- system: Owner App
- category: Dataset permission missing
- route: BI 管理者
- priority: P3
- keywords: Owner App, Dataset permission missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Owner App に関する Dataset permission missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は BI 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-008: Executive Dashboard / Report app not installed
- rule_id: PBI-008
- system: Executive Dashboard
- category: Report app not installed
- route: Data Platform Team
- priority: P3
- keywords: Executive Dashboard, Report app not installed, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Executive Dashboard に関する Report app not installed の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Data Platform Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-009: Power BI / RLS filtered
- rule_id: PBI-009
- system: Power BI
- category: RLS filtered
- route: Microsoft 365 ライセンス管理チーム
- priority: P3
- keywords: Power BI, RLS filtered, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Power BI に関する RLS filtered の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Microsoft 365 ライセンス管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-010: Fabric Workspace / License missing
- rule_id: PBI-010
- system: Fabric Workspace
- category: License missing
- route: BI 管理者
- priority: P3
- keywords: Fabric Workspace, License missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Fabric Workspace に関する License missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は BI 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-011: Owner App / Workspace permission denied
- rule_id: PBI-011
- system: Owner App
- category: Workspace permission denied
- route: Data Platform Team
- priority: P3
- keywords: Owner App, Workspace permission denied, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Owner App に関する Workspace permission denied の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Data Platform Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-012: Executive Dashboard / Dataset permission missing
- rule_id: PBI-012
- system: Executive Dashboard
- category: Dataset permission missing
- route: Microsoft 365 ライセンス管理チーム
- priority: P3
- keywords: Executive Dashboard, Dataset permission missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Executive Dashboard に関する Dataset permission missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Microsoft 365 ライセンス管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-013: Power BI / Report app not installed
- rule_id: PBI-013
- system: Power BI
- category: Report app not installed
- route: BI 管理者
- priority: P3
- keywords: Power BI, Report app not installed, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Power BI に関する Report app not installed の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は BI 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-014: Fabric Workspace / RLS filtered
- rule_id: PBI-014
- system: Fabric Workspace
- category: RLS filtered
- route: Data Platform Team
- priority: P3
- keywords: Fabric Workspace, RLS filtered, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Fabric Workspace に関する RLS filtered の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Data Platform Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-015: Owner App / License missing
- rule_id: PBI-015
- system: Owner App
- category: License missing
- route: Microsoft 365 ライセンス管理チーム
- priority: P3
- keywords: Owner App, License missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Owner App に関する License missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Microsoft 365 ライセンス管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-016: Executive Dashboard / Workspace permission denied
- rule_id: PBI-016
- system: Executive Dashboard
- category: Workspace permission denied
- route: BI 管理者
- priority: P3
- keywords: Executive Dashboard, Workspace permission denied, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Executive Dashboard に関する Workspace permission denied の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は BI 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-017: Power BI / Dataset permission missing
- rule_id: PBI-017
- system: Power BI
- category: Dataset permission missing
- route: Data Platform Team
- priority: P2
- keywords: Power BI, Dataset permission missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Power BI に関する Dataset permission missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Data Platform Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-018: Fabric Workspace / Report app not installed
- rule_id: PBI-018
- system: Fabric Workspace
- category: Report app not installed
- route: Microsoft 365 ライセンス管理チーム
- priority: P3
- keywords: Fabric Workspace, Report app not installed, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Fabric Workspace に関する Report app not installed の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Microsoft 365 ライセンス管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-019: Owner App / RLS filtered
- rule_id: PBI-019
- system: Owner App
- category: RLS filtered
- route: BI 管理者
- priority: P3
- keywords: Owner App, RLS filtered, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Owner App に関する RLS filtered の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は BI 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-020: Executive Dashboard / License missing
- rule_id: PBI-020
- system: Executive Dashboard
- category: License missing
- route: Data Platform Team
- priority: P3
- keywords: Executive Dashboard, License missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Executive Dashboard に関する License missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Data Platform Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-021: Power BI / Workspace permission denied
- rule_id: PBI-021
- system: Power BI
- category: Workspace permission denied
- route: Microsoft 365 ライセンス管理チーム
- priority: P3
- keywords: Power BI, Workspace permission denied, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Power BI に関する Workspace permission denied の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Microsoft 365 ライセンス管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-022: Fabric Workspace / Dataset permission missing
- rule_id: PBI-022
- system: Fabric Workspace
- category: Dataset permission missing
- route: BI 管理者
- priority: P3
- keywords: Fabric Workspace, Dataset permission missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Fabric Workspace に関する Dataset permission missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は BI 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-023: Owner App / Report app not installed
- rule_id: PBI-023
- system: Owner App
- category: Report app not installed
- route: Data Platform Team
- priority: P3
- keywords: Owner App, Report app not installed, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Owner App に関する Report app not installed の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Data Platform Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-024: Executive Dashboard / RLS filtered
- rule_id: PBI-024
- system: Executive Dashboard
- category: RLS filtered
- route: Microsoft 365 ライセンス管理チーム
- priority: P3
- keywords: Executive Dashboard, RLS filtered, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Executive Dashboard に関する RLS filtered の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Microsoft 365 ライセンス管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-025: Power BI / License missing
- rule_id: PBI-025
- system: Power BI
- category: License missing
- route: BI 管理者
- priority: P3
- keywords: Power BI, License missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Power BI に関する License missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は BI 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-026: Fabric Workspace / Workspace permission denied
- rule_id: PBI-026
- system: Fabric Workspace
- category: Workspace permission denied
- route: Data Platform Team
- priority: P3
- keywords: Fabric Workspace, Workspace permission denied, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Fabric Workspace に関する Workspace permission denied の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Data Platform Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-027: Owner App / Dataset permission missing
- rule_id: PBI-027
- system: Owner App
- category: Dataset permission missing
- route: Microsoft 365 ライセンス管理チーム
- priority: P3
- keywords: Owner App, Dataset permission missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Owner App に関する Dataset permission missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Microsoft 365 ライセンス管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-028: Executive Dashboard / Report app not installed
- rule_id: PBI-028
- system: Executive Dashboard
- category: Report app not installed
- route: BI 管理者
- priority: P3
- keywords: Executive Dashboard, Report app not installed, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Executive Dashboard に関する Report app not installed の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は BI 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-029: Power BI / RLS filtered
- rule_id: PBI-029
- system: Power BI
- category: RLS filtered
- route: Data Platform Team
- priority: P3
- keywords: Power BI, RLS filtered, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Power BI に関する RLS filtered の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Data Platform Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-030: Fabric Workspace / License missing
- rule_id: PBI-030
- system: Fabric Workspace
- category: License missing
- route: Microsoft 365 ライセンス管理チーム
- priority: P3
- keywords: Fabric Workspace, License missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Fabric Workspace に関する License missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Microsoft 365 ライセンス管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-031: Owner App / Workspace permission denied
- rule_id: PBI-031
- system: Owner App
- category: Workspace permission denied
- route: BI 管理者
- priority: P3
- keywords: Owner App, Workspace permission denied, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Owner App に関する Workspace permission denied の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は BI 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-032: Executive Dashboard / Dataset permission missing
- rule_id: PBI-032
- system: Executive Dashboard
- category: Dataset permission missing
- route: Data Platform Team
- priority: P3
- keywords: Executive Dashboard, Dataset permission missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Executive Dashboard に関する Dataset permission missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Data Platform Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-033: Power BI / Report app not installed
- rule_id: PBI-033
- system: Power BI
- category: Report app not installed
- route: Microsoft 365 ライセンス管理チーム
- priority: P3
- keywords: Power BI, Report app not installed, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Power BI に関する Report app not installed の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Microsoft 365 ライセンス管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-034: Fabric Workspace / RLS filtered
- rule_id: PBI-034
- system: Fabric Workspace
- category: RLS filtered
- route: BI 管理者
- priority: P2
- keywords: Fabric Workspace, RLS filtered, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Fabric Workspace に関する RLS filtered の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は BI 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-035: Owner App / License missing
- rule_id: PBI-035
- system: Owner App
- category: License missing
- route: Data Platform Team
- priority: P3
- keywords: Owner App, License missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Owner App に関する License missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Data Platform Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-036: Executive Dashboard / Workspace permission denied
- rule_id: PBI-036
- system: Executive Dashboard
- category: Workspace permission denied
- route: Microsoft 365 ライセンス管理チーム
- priority: P3
- keywords: Executive Dashboard, Workspace permission denied, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Executive Dashboard に関する Workspace permission denied の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Microsoft 365 ライセンス管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-037: Power BI / Dataset permission missing
- rule_id: PBI-037
- system: Power BI
- category: Dataset permission missing
- route: BI 管理者
- priority: P3
- keywords: Power BI, Dataset permission missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Power BI に関する Dataset permission missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は BI 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-038: Fabric Workspace / Report app not installed
- rule_id: PBI-038
- system: Fabric Workspace
- category: Report app not installed
- route: Data Platform Team
- priority: P3
- keywords: Fabric Workspace, Report app not installed, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Fabric Workspace に関する Report app not installed の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Data Platform Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-039: Owner App / RLS filtered
- rule_id: PBI-039
- system: Owner App
- category: RLS filtered
- route: Microsoft 365 ライセンス管理チーム
- priority: P3
- keywords: Owner App, RLS filtered, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Owner App に関する RLS filtered の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Microsoft 365 ライセンス管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-040: Executive Dashboard / License missing
- rule_id: PBI-040
- system: Executive Dashboard
- category: License missing
- route: BI 管理者
- priority: P3
- keywords: Executive Dashboard, License missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Executive Dashboard に関する License missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は BI 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-041: Power BI / Workspace permission denied
- rule_id: PBI-041
- system: Power BI
- category: Workspace permission denied
- route: Data Platform Team
- priority: P3
- keywords: Power BI, Workspace permission denied, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Power BI に関する Workspace permission denied の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Data Platform Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-042: Fabric Workspace / Dataset permission missing
- rule_id: PBI-042
- system: Fabric Workspace
- category: Dataset permission missing
- route: Microsoft 365 ライセンス管理チーム
- priority: P3
- keywords: Fabric Workspace, Dataset permission missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Fabric Workspace に関する Dataset permission missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Microsoft 365 ライセンス管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-043: Owner App / Report app not installed
- rule_id: PBI-043
- system: Owner App
- category: Report app not installed
- route: BI 管理者
- priority: P3
- keywords: Owner App, Report app not installed, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Owner App に関する Report app not installed の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は BI 管理者 にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-044: Executive Dashboard / RLS filtered
- rule_id: PBI-044
- system: Executive Dashboard
- category: RLS filtered
- route: Data Platform Team
- priority: P3
- keywords: Executive Dashboard, RLS filtered, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Executive Dashboard に関する RLS filtered の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Data Platform Team にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。

## Rule PBI-045: Power BI / License missing
- rule_id: PBI-045
- system: Power BI
- category: License missing
- route: Microsoft 365 ライセンス管理チーム
- priority: P3
- keywords: Power BI, License missing, 権限, 申請, ログイン, MFA, ライセンス, メニュー, 監査
- policy: Power BI に関する License missing の問い合わせは、利用者、部署、対象画面、発生時刻、エラーコードまたは症状を確認してから一次切り分けする。
- self_service: 利用者はブラウザ再起動、InPrivate モード、会社端末、VPN、MFA 状態、申請済み権限を確認する。
- escalation: 自助対応で解決しない場合は Microsoft 365 ライセンス管理チーム にチケットを起票する。高リスク操作は自動実行せず承認を必須とする。
- audit_note: Agent は分類、参照した規則、提案したルート、実行しなかった高リスク操作を記録する。
