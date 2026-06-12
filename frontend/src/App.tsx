import { useState, useCallback } from "react";
import FingerprintJS from "@fingerprintjs/fingerprintjs";

import ConsentPage from "./components/ConsentPage";
import FingerprintStatus from "./components/FingerprintStatus";
import { submitFingerprint } from "./services/apiService";
import type {
  SubmissionStatus,
  FingerprintPayload,
  ApiSubmitResponse,
} from "./types";

import "./App.css";

function App() {
  const [participantName, setParticipantName] = useState("");
  const [consentGiven, setConsentGiven] = useState(false);
  const [status, setStatus] = useState<SubmissionStatus>("idle");
  const [successResponse, setSuccessResponse] = useState<ApiSubmitResponse | null>(null);
  const [durationMs, setDurationMs] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [nameError, setNameError] = useState<string | null>(null);
  const [consentError, setConsentError] = useState<string | null>(null);

  const validate = useCallback((): boolean => {
    let valid = true;
    if (!participantName.trim()) {
      setNameError("Por favor, informe seu nome.");
      valid = false;
    } else {
      setNameError(null);
    }
    if (!consentGiven) {
      setConsentError("É necessário marcar o consentimento para continuar.");
      valid = false;
    } else {
      setConsentError(null);
    }
    return valid;
  }, [participantName, consentGiven]);

  const handleSubmit = useCallback(async () => {
    if (!validate()) return;

    setStatus("loading");
    setErrorMessage(null);

    const t0 = performance.now();

    try {
      // FingerprintJS só é carregado e executado aqui — após consentimento explícito
      const fpAgent = await FingerprintJS.load();
      const fpResult = await fpAgent.get();

      const t1 = performance.now();
      const totalDuration = t1 - t0;

      setDurationMs(totalDuration);

      // Enviamos o retorno COMPLETO e INTACTO do FingerprintJS OSS.
      // - components: objeto com TODAS as features, cada uma com { value, duration }
      //   O userAgent é apenas mais um componente dentro de components (userAgentData),
      //   sem nenhum tratamento especial.
      // - raw_result: o objeto inteiro retornado por fpAgent.get(), sem modificação.
      // - visitor_id e confidence vêm diretamente de fpResult, sem manipulação.
      // - user_agent no nível raiz NÃO é mais enviado separadamente — está em components.
      const payload: FingerprintPayload = {
      participant_name: participantName.trim(),
      fingerprint_result: fpResult as unknown as Record<string, unknown>,
    };

      const response = await submitFingerprint(payload);
      setSuccessResponse(response);
      setStatus("success");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erro desconhecido. Tente novamente.";
      setErrorMessage(msg);
      setStatus("error");
    }
  }, [validate, participantName]);

  const handleReset = useCallback(() => {
    setParticipantName("");
    setConsentGiven(false);
    setStatus("idle");
    setSuccessResponse(null);
    setDurationMs(null);
    setErrorMessage(null);
    setNameError(null);
    setConsentError(null);
  }, []);

  return (
    <div className="app">
      <div className="container">
        {status === "success" && successResponse ? (
          <FingerprintStatus
            response={successResponse}
            durationMs={durationMs}
            onReset={handleReset}
          />
        ) : (
          <>
            <ConsentPage
              participantName={participantName}
              onNameChange={setParticipantName}
              consentGiven={consentGiven}
              onConsentChange={setConsentGiven}
              onSubmit={handleSubmit}
              isLoading={status === "loading"}
              nameError={nameError}
              consentError={consentError}
            />
            {status === "error" && errorMessage && (
              <div className="card error-banner">
                <strong>Erro ao enviar:</strong> {errorMessage}
              </div>
            )}
          </>
        )}
      </div>
      <footer className="footer">
        <p>
          Experimento acadêmico · Dados coletados com consentimento explícito ·
          FingerprintJS OSS
        </p>
      </footer>
    </div>
  );
}

export default App;
