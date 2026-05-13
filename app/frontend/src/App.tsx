import { useState, useEffect, useMemo } from 'react';
import type { PipelineResult, SampleApplication, LedgerEntry, LedgerForm, ProcessResponse } from './types';
import { fetchSamples, processApplication, confirmResult, exportResult, fetchLedger, createLedger, updateLedger, deleteLedger } from './api';

const STEP_LABELS = ['フィールド抽出', '不備チェック', 'リスク評価', '受付判定', '台帳生成'];

const EMPTY_FORM: LedgerForm = {
  applicant_name: '', applicant_dept: '', application_type: '',
  application_date: '', application_summary: '', estimated_cost: '',
  priority_level: '低', risk_level: '低', decision: '受付', status: '審査中',
};

const TYPE_OPTIONS = ['設備変更', '人事異動', '予算申請', '契約更新', 'その他'];
const PRIORITY_OPTIONS = ['高', '中', '低'];
const RISK_OPTIONS = ['致命', '高', '中', '低'];
const DECISION_OPTIONS = ['受付', '差戻', '要確認'];
const STATUS_OPTIONS = ['受付済', '差戻', '審査中'];

function toBool(v: unknown): boolean {
  if (typeof v === 'boolean') return v;
  if (typeof v === 'string') return v.toLowerCase() === 'true';
  return false;
}

function displayValue(v: unknown): string {
  if (v == null || v === '') return '-';
  if (typeof v === 'string' && v.startsWith('{')) return v.slice(0, 60) + '…';
  return String(v);
}

function cleanFields(fields: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(fields)) {
    if (k.startsWith('_raw_text') || k === '_unclear') continue;
    out[k] = v;
  }
  return out;
}

function statusBadge(s: string) {
  if (s.includes('差戻')) return 'badge badge-danger';
  if (s.includes('審査')) return 'badge badge-warning';
  return 'badge badge-success';
}

function decisionBadge(d: string) {
  if (d.includes('差戻')) return 'badge badge-danger';
  if (d.includes('確認')) return 'badge badge-warning';
  return 'badge badge-success';
}

function riskBadge(r: string) {
  if (r.includes('致命') || r.includes('高')) return 'badge badge-danger';
  if (r.includes('中')) return 'badge badge-warning';
  return 'badge badge-success';
}

function priorityBadge(p: string) {
  if (p === '高') return 'badge badge-danger';
  if (p === '中') return 'badge badge-warning';
  return 'badge badge-info';
}

type ModalMode = 'closed' | 'create' | 'edit';

function hasRawText(obj: Record<string, unknown>): boolean {
  return Object.keys(obj).some(k => k.startsWith('_raw_text'));
}

function App() {
  const [samples, setSamples] = useState<SampleApplication[]>([]);
  const [inputText, setInputText] = useState('');
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [processing, setProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(-1);
  const [confirmed, setConfirmed] = useState(false);
  const [showJson, setShowJson] = useState(false);
  const [error, setError] = useState('');

  // Ledger state
  const [allEntries, setAllEntries] = useState<LedgerEntry[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [modalMode, setModalMode] = useState<ModalMode>('closed');
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState<LedgerForm>({ ...EMPTY_FORM });
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [loadingLedger, setLoadingLedger] = useState(false);

  const loadLedger = async () => {
    setLoadingLedger(true);
    try {
      const data = await fetchLedger();
      setAllEntries(data);
    } catch { /* ignore */ }
    setLoadingLedger(false);
  };

  useEffect(() => {
    fetchSamples().then(setSamples).catch(() => {});
    loadLedger();
  }, []);

  const entries = useMemo(() => {
    if (!searchQuery) return allEntries;
    const q = searchQuery.toLowerCase();
    return allEntries.filter(e =>
      e.applicant_name.toLowerCase().includes(q) ||
      e.application_type.toLowerCase().includes(q) ||
      e.ledger_id.toLowerCase().includes(q)
    );
  }, [allEntries, searchQuery]);

  const handleProcess = async () => {
    if (!inputText.trim()) return;
    setProcessing(true);
    setResult(null);
    setConfirmed(false);
    setError('');
    setCurrentStep(0);

    try {
      const res = await processApplication(inputText);
      setResult(res as unknown as PipelineResult);
      if (res.is_unclear || hasRawText(res.extracted) || hasRawText(res.deficiency)) {
        setCurrentStep(5);
      } else {
        setCurrentStep(5);
      }
      await loadLedger();
    } catch {
      setError('サーバー接続エラー。llama-serverが起動しているか確認してください。');
    } finally {
      setProcessing(false);
    }
  };

  const handleConfirm = async () => {
    if (!result) return;
    try {
      const updated = await confirmResult(result.id);
      setResult(updated as unknown as PipelineResult);
      setConfirmed(true);
      await loadLedger();
    } catch { setError('確認処理エラー'); }
  };

  const handleExport = async (format: 'json' | 'csv') => {
    if (!result) return;
    try {
      const data = await exportResult(result.id, format);
      const blob = new Blob([data], { type: format === 'csv' ? 'text/csv' : 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ledger_${result.id}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch { setError('エクスポートエラー'); }
  };

  // ─── Modal handlers ──────────────────────────────

  const openCreate = () => {
    setForm({ ...EMPTY_FORM });
    setEditId(null);
    setModalMode('create');
  };

  const openEdit = (e: LedgerEntry) => {
    setForm({
      applicant_name: e.applicant_name,
      applicant_dept: e.applicant_dept,
      application_type: e.application_type,
      application_date: e.application_date,
      application_summary: e.application_summary,
      estimated_cost: e.estimated_cost,
      priority_level: e.priority_level || '低',
      risk_level: e.risk_level || '低',
      decision: e.decision || '受付',
      status: e.status || '審査中',
    });
    setEditId(e.id);
    setModalMode('edit');
  };

  const handleModalSave = async () => {
    try {
      if (modalMode === 'create') {
        await createLedger(form);
      } else if (editId) {
        await updateLedger(editId, form);
      }
      setModalMode('closed');
      await loadLedger();
    } catch { setError('保存エラー'); }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteLedger(id);
      setDeleteConfirm(null);
      await loadLedger();
    } catch { setError('削除エラー'); }
  };

  // ─── Prepare display data ────────────────────────

  const extracted = result ? cleanFields(result.extracted) : {};
  const deficiency = result ? cleanFields(result.deficiency) : {};
  const risk = result ? cleanFields(result.risk) : {};
  const decision = result ? cleanFields(result.decision) : {};

  // ─── Render ──────────────────────────────────────

  return (
    <div>
      {/* ───── Header ───── */}
      <div className="header">
        <h1>ローカルAI申請受付支援 Demo</h1>
        <p>LFM2-1.2B-Tool による申請内容解析・台帳データ管理</p>
      </div>

      {/* ───── AI Processing Section ───── */}
      <div className="card input-area">
        <div className="section-title">
          <span className="section-icon">🤖</span>
          <span>AI 申請処理</span>
        </div>
        <div className="sample-select">
          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>サンプル選択:</span>
          {samples.map((s) => (
            <button key={s.id} className="sample-btn" onClick={() => setInputText(s.text)}>
              {s.title}
            </button>
          ))}
        </div>
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="申請内容を入力してください..."
        />
        <button className="process-btn" onClick={handleProcess} disabled={processing || !inputText.trim()}>
          {processing ? '処理中...' : '処理開始'}
        </button>
      </div>

      {error && <div className="card" style={{ borderColor: 'var(--danger)' }}><p style={{ color: 'var(--danger)' }}>{error}</p></div>}

      {processing && (
        <div className="card">
          <div className="progress-bar">
            {STEP_LABELS.map((_, i) => (
              <div key={i} className={`progress-step ${i <= currentStep ? (i < currentStep ? 'done' : 'active') : ''}`} />
            ))}
          </div>
          <div className="loading">
            <span className="spinner" /> {STEP_LABELS[currentStep] || '処理中...'}
          </div>
        </div>
      )}

      {result && result.is_unclear && (
        <div className="card unclear-card">
          <h3>申請内容が不明確</h3>
          <p className="reason">理由: {result.unclear_reason}</p>
          <p className="suggestion">提案: {result.unclear_suggestion}</p>
        </div>
      )}

      {result && !result.is_unclear && (
        <>
          <div className="card step-card">
            <div className="step-header">
              <div className="step-number">1</div>
              <div className="step-title">フィールド抽出</div>
            </div>
            <table className="field-table">
              <tbody>
                {Object.entries(extracted).map(([k, v]) => (
                  <tr key={k}>
                    <td>{k}</td>
                    <td>{Array.isArray(v) ? v.join(', ') : displayValue(v)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="card step-card">
            <div className="step-header">
              <div className="step-number">2</div>
              <div className="step-title">不備チェック</div>
              <span className={`badge ${toBool(deficiency.deficiency_found) ? 'badge-warning' : 'badge-success'}`}>
                {toBool(deficiency.deficiency_found) ? '不備あり' : '不備なし'}
              </span>
            </div>
            <table className="field-table">
              <tbody>
                <tr><td>完全性スコア</td><td>{displayValue(deficiency.completeness_score)} / 100</td></tr>
                {Array.isArray(deficiency.missing_documents) && deficiency.missing_documents.length > 0 && (
                  <tr><td>不足書類</td><td>{(deficiency.missing_documents as string[]).join(', ')}</td></tr>
                )}
                {Array.isArray(deficiency.deficiency_fields) && deficiency.deficiency_fields.length > 0 && (
                  <tr><td>不備項目</td><td>{(deficiency.deficiency_fields as string[]).join(', ')}</td></tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="card step-card">
            <div className="step-header">
              <div className="step-number">3</div>
              <div className="step-title">リスク評価</div>
              <span className={riskBadge(String(risk.risk_level ?? ''))}>
                {displayValue(risk.risk_level)}
              </span>
            </div>
            <table className="field-table">
              <tbody>
                <tr><td>要人工審査</td><td>{toBool(risk.requires_manual_review) ? 'Yes' : 'No'}</td></tr>
                {Array.isArray(risk.approval_chain) && risk.approval_chain.length > 0 && (
                  <tr><td>承認フロー</td><td>{(risk.approval_chain as string[]).join(' → ')}</td></tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="card step-card">
            <div className="step-header">
              <div className="step-number">4</div>
              <div className="step-title">受付判定</div>
              <span className={decisionBadge(String(decision.decision ?? ''))}>
                {displayValue(decision.decision)}
              </span>
            </div>
            <table className="field-table">
              <tbody>
                <tr><td>判定理由</td><td>{displayValue(decision.reason)}</td></tr>
                {Array.isArray(decision.conditions) && decision.conditions.length > 0 && (
                  <tr><td>条件</td><td>{(decision.conditions as string[]).join(', ')}</td></tr>
                )}
                <tr><td>次のアクション</td><td>{displayValue(decision.next_action)}</td></tr>
                <tr><td>担当部署</td><td>{displayValue(decision.assign_to)}</td></tr>
              </tbody>
            </table>
          </div>

          <div className="card step-card">
            <div className="step-header">
              <div className="step-number">5</div>
              <div className="step-title">台帳データ</div>
              <span className="badge badge-info">{displayValue(result.ledger.status)}</span>
            </div>
            <table className="field-table">
              <tbody>
                <tr><td>台帳ID</td><td>{displayValue(result.ledger.ledger_id)}</td></tr>
                <tr><td>記載日</td><td>{displayValue(result.ledger.entry_date)}</td></tr>
                <tr><td>信頼度スコア</td><td>{displayValue(result.ledger.confidence_score)} / 100</td></tr>
              </tbody>
            </table>
            {showJson && (
              <div className="json-output">{JSON.stringify(result.ledger, null, 2)}</div>
            )}
            <div className="export-btns">
              <button className="export-btn" onClick={() => setShowJson(!showJson)}>
                {showJson ? 'JSON非表示' : 'JSON表示'}
              </button>
              <button className="export-btn" onClick={() => handleExport('json')}>JSONダウンロード</button>
              <button className="export-btn" onClick={() => handleExport('csv')}>CSVダウンロード</button>
            </div>
          </div>

          {!confirmed && (
            <div className="card review-section">
              <h3>审核員確認</h3>
              <p style={{ marginBottom: 12, color: 'var(--text-secondary)' }}>
                AIの提案内容を確認し、問題なければ台帳登録を行います。
              </p>
              <button className="confirm-btn" onClick={handleConfirm}>確認・台帳登録</button>
            </div>
          )}

          {confirmed && (
            <div className="card" style={{ textAlign: 'center', borderColor: 'var(--success)' }}>
              <h3 style={{ color: 'var(--success)' }}>台帳登録完了</h3>
              <p>申請ID: {result.id} が台帳に登録されました。</p>
            </div>
          )}
        </>
      )}

      {/* ───── Ledger Database Section ───── */}
      <div className="card ledger-section">
        <div className="section-title">
          <span className="section-icon">🗄️</span>
          <span>台帳データベース</span>
          <span className="entry-count">{allEntries.length} 件</span>
        </div>

        <div className="ledger-toolbar">
          <button className="add-btn" onClick={openCreate}>＋ 新規追加</button>
          <button className="refresh-btn" onClick={loadLedger} disabled={loadingLedger}>
            {loadingLedger ? '読込中...' : '🔄 更新'}
          </button>
          <input
            className="search-input"
            type="text"
            placeholder="検索..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="ledger-table-wrap">
          <table className="ledger-table">
            <thead>
              <tr>
                <th>台帳ID</th>
                <th>申請者</th>
                <th>種別</th>
                <th>日付</th>
                <th>優先度</th>
                <th>リスク</th>
                <th>判定</th>
                <th>ステータス</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {entries.length === 0 && (
                <tr><td colSpan={9} className="empty-row">データがありません。「＋ 新規追加」またはAI処理結果を確認して台帳登録してください。</td></tr>
              )}
              {entries.map(entry => (
                <tr key={entry.id}>
                  <td className="cell-id">{entry.ledger_id || '-'}</td>
                  <td>{entry.applicant_name || '-'}</td>
                  <td>{entry.application_type || '-'}</td>
                  <td>{entry.application_date || entry.entry_date || '-'}</td>
                  <td><span className={priorityBadge(entry.priority_level)}>{entry.priority_level || '-'}</span></td>
                  <td><span className={riskBadge(entry.risk_level)}>{entry.risk_level || '-'}</span></td>
                  <td><span className={decisionBadge(entry.decision)}>{entry.decision || '-'}</span></td>
                  <td><span className={statusBadge(entry.status)}>{entry.status || '-'}</span></td>
                  <td className="cell-actions">
                    <button className="action-btn edit-btn" onClick={() => openEdit(entry)} title="編集">✏️</button>
                    {deleteConfirm === entry.id ? (
                      <span className="delete-confirm">
                        削除？
                        <button className="action-btn confirm-yes" onClick={() => handleDelete(entry.id)}>はい</button>
                        <button className="action-btn confirm-no" onClick={() => setDeleteConfirm(null)}>いいえ</button>
                      </span>
                    ) : (
                      <button className="action-btn delete-btn" onClick={() => setDeleteConfirm(entry.id)} title="削除">🗑️</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ───── Create/Edit Modal ───── */}
      {modalMode !== 'closed' && (
        <div className="modal-overlay" onClick={() => setModalMode('closed')}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{modalMode === 'create' ? '新規台帳追加' : '台帳編集'}</h3>
              <button className="modal-close" onClick={() => setModalMode('closed')}>✕</button>
            </div>
            <div className="modal-body">
              <div className="form-grid">
                <label>申請者名
                  <input value={form.applicant_name} onChange={e => setForm({...form, applicant_name: e.target.value})} />
                </label>
                <label>所属部署
                  <input value={form.applicant_dept} onChange={e => setForm({...form, applicant_dept: e.target.value})} />
                </label>
                <label>申請種別
                  <select value={form.application_type} onChange={e => setForm({...form, application_type: e.target.value})}>
                    <option value="">--</option>
                    {TYPE_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </label>
                <label>申請日
                  <input type="date" value={form.application_date} onChange={e => setForm({...form, application_date: e.target.value})} />
                </label>
                <label className="full-width">内容要約
                  <textarea value={form.application_summary} onChange={e => setForm({...form, application_summary: e.target.value})} rows={2} />
                </label>
                <label>推定費用
                  <input value={form.estimated_cost} onChange={e => setForm({...form, estimated_cost: e.target.value})} placeholder="例: 350万円" />
                </label>
                <label>優先度
                  <select value={form.priority_level} onChange={e => setForm({...form, priority_level: e.target.value})}>
                    {PRIORITY_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </label>
                <label>リスク
                  <select value={form.risk_level} onChange={e => setForm({...form, risk_level: e.target.value})}>
                    {RISK_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </label>
                <label>判定
                  <select value={form.decision} onChange={e => setForm({...form, decision: e.target.value})}>
                    {DECISION_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </label>
                <label>ステータス
                  <select value={form.status} onChange={e => setForm({...form, status: e.target.value})}>
                    {STATUS_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </label>
              </div>
            </div>
            <div className="modal-footer">
              <button className="cancel-btn" onClick={() => setModalMode('closed')}>キャンセル</button>
              <button className="save-btn" onClick={handleModalSave}>
                {modalMode === 'create' ? '追加' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;