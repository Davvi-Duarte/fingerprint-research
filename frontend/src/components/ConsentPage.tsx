import React from "react";

interface ConsentPageProps {
  participantName: string;
  onNameChange: (name: string) => void;
  consentGiven: boolean;
  onConsentChange: (given: boolean) => void;
  onSubmit: () => void;
  isLoading: boolean;
  nameError: string | null;
  consentError: string | null;
}

const ConsentPage: React.FC<ConsentPageProps> = ({
  participantName,
  onNameChange,
  consentGiven,
  onConsentChange,
  onSubmit,
  isLoading,
  nameError,
  consentError,
}) => {
  return (
    <div className="consent-page">
      <header className="hero">
        <div className="hero-badge">Pesquisa Acadêmica</div>
        <h1>
          Identificação de Usuários Web por
          <span className="highlight"> Browser Fingerprinting</span>
        </h1>
        <p className="hero-sub">
          Replicação metodológica adaptada de Salomatin, Iskhakov &amp; Iskhakova
        </p>
      </header>

      <section className="card info-card">
        <h2>Sobre este experimento</h2>
        <p>
          Este sistema coleta impressões digitais de navegador (
          <em>browser fingerprints</em>) de participantes voluntários para
          fins exclusivamente acadêmicos. Os dados gerados serão utilizados
          para reproduzir parcialmente o estudo{" "}
          <strong>
            "Web user identification based on browser fingerprints using machine
            learning methods"
          </strong>
          , aplicando o algoritmo K-Nearest Neighbors (KNN) na identificação
          de usuários web.
        </p>
        <p>
          A coleta utiliza a biblioteca de código aberto{" "}
          <strong>FingerprintJS OSS</strong> e registra atributos técnicos do
          seu navegador — como fontes instaladas, configurações de canvas,
          fuso horário, idioma e informações de hardware — sem acessar
          arquivos pessoais, histórico ou credenciais.
        </p>
      </section>

      <section className="card privacy-card">
        <h2>
          <span className="icon">🔒</span> Aviso de Privacidade
        </h2>
        <ul>
          <li>
            <strong>Não</strong> coletamos senhas, credenciais, histórico de
            navegação, conteúdo acessado ou cookies de terceiros.
          </li>
          <li>
            Seu nome é utilizado apenas para organização interna das amostras
            e <strong>não será publicado</strong> na versão pública dos dados.
          </li>
          <li>
            A base bruta é interna. A versão pública usará identificadores
            anônimos.
          </li>
          <li>
            A coleta <strong>só ocorre após seu consentimento explícito</strong>{" "}
            e clique no botão abaixo.
          </li>
          <li>
            O endereço IP é armazenado apenas como hash SHA-256 unidirecional.
          </li>
        </ul>
      </section>

      <section className="card consent-card">
        <h2>Participar</h2>

        <div className="field-group">
          <label htmlFor="participant-name" className="field-label">
            Seu nome completo <span className="required">*</span>
          </label>
          <input
            id="participant-name"
            type="text"
            className={`text-input ${nameError ? "input-error" : ""}`}
            placeholder="Digite seu nome..."
            value={participantName}
            onChange={(e) => onNameChange(e.target.value)}
            disabled={isLoading}
            autoComplete="off"
          />
          {nameError && <p className="error-msg">{nameError}</p>}
        </div>

        <div className={`checkbox-group ${consentError ? "checkbox-error" : ""}`}>
          <label className="checkbox-label">
            <input
              type="checkbox"
              className="checkbox-input"
              checked={consentGiven}
              onChange={(e) => onConsentChange(e.target.checked)}
              disabled={isLoading}
            />
            <span className="checkbox-custom" />
            <span className="checkbox-text">
              Li e compreendi as informações acima. Consinto voluntariamente com
              a coleta do fingerprint do meu navegador para fins de pesquisa
              acadêmica, conforme descrito.
            </span>
          </label>
          {consentError && <p className="error-msg">{consentError}</p>}
        </div>

        <button
          className={`btn-primary ${isLoading ? "btn-loading" : ""}`}
          onClick={onSubmit}
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <span className="spinner" />
              Coletando e enviando…
            </>
          ) : (
            "Gerar e enviar fingerprint"
          )}
        </button>
      </section>
    </div>
  );
};

export default ConsentPage;
