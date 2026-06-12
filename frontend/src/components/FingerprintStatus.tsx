import React from "react";
import type { ApiSubmitResponse } from "../types";

interface FingerprintStatusProps {
  response: ApiSubmitResponse;
  durationMs: number | null;
  onReset: () => void;
}

const FingerprintStatus: React.FC<FingerprintStatusProps> = ({
  response,
  durationMs,
  onReset,
}) => {
  return (
    <div className="status-page">
      <div className="status-icon success-icon">✓</div>
      <h2 className="status-title">Fingerprint registrado com sucesso!</h2>
      <p className="status-sub">
        Obrigado pela sua participação nesta pesquisa acadêmica.
      </p>

      <div className="card summary-card">
        <h3>Resumo da coleta</h3>
        <dl className="summary-list">
          <div className="summary-row">
            <dt>ID da coleta</dt>
            <dd>
              <code>{response.id}</code>
            </dd>
          </div>
          <div className="summary-row">
            <dt>ID do participante</dt>
            <dd>
              <code className="truncate">{response.participant_id}</code>
            </dd>
          </div>
          <div className="summary-row">
            <dt>Session ID</dt>
            <dd>
              <code className="truncate">{response.session_id}</code>
            </dd>
          </div>
          <div className="summary-row">
            <dt>Registrado em</dt>
            <dd>
              {new Date(response.created_at).toLocaleString("pt-BR", {
                dateStyle: "long",
                timeStyle: "medium",
              })}
            </dd>
          </div>
          {durationMs !== null && (
            <div className="summary-row">
              <dt>Duração da coleta</dt>
              <dd>{durationMs.toFixed(1)} ms</dd>
            </div>
          )}
        </dl>
        <p className="summary-note">
          Os dados brutos completos não são exibidos aqui por razões de
          privacidade e segurança da pesquisa.
        </p>
      </div>

      <button className="btn-secondary" onClick={onReset}>
        Realizar nova coleta
      </button>
    </div>
  );
};

export default FingerprintStatus;
