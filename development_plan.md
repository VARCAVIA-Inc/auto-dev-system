Ok, team. Qui è il ProjectBot.

Ho analizzato l'obiettivo di business e l'ho tradotto nel seguente piano tecnico dettagliato. La nostra priorità è integrare un robusto ciclo di Test-Driven Development (TDD) nel nostro workflow per migliorare la qualità e l'affidabilità del codice.

Seguite i task in sequenza. Massima attenzione ai dettagli.

---

# **Piano Tecnico: Implementazione Sviluppo Guidato dai Test (TDD)**

**Obiettivo:** Potenziare il ProjectBot per generare file di test unitari (`*_test.py`) per ogni nuovo file Python. Potenziare l'OperatorBot per eseguire `pytest` dopo aver scritto il codice e prima di creare la PR. Il workflow dell'OperatorBot deve fallire se i test non passano.

## **Fase 1: Configurazione dell'Ambiente di Test**

Il primo passo è preparare il nostro progetto per i test unitari introducendo `pytest`.

1.  **Aggiornare le dipendenze di sviluppo.**
    Aggiungeremo `pytest` e `pytest-mock` per la gestione dei test e il mocking delle dipendenze (come le chiamate AI o i comandi di sistema).
    `[requirements.txt]`
    ```diff
    + pytest
    + pytest-mock
    # Existing dependencies below
    google-cloud-aiplatform
    google-api-python-client
    ```

2.  **Installare le nuove dipendenze.**
    Assicuriamoci che l'ambiente sia aggiornato.
    `[shell-command]`
    ```
    pip install -r requirements.txt
    ```

## **Fase 2: Creazione dei Test Unitari per il Codice Esistente**

Ora creeremo i file di test per ogni modulo Python esistente nella directory `src`. Questo ci fornirà una base di test solida prima di modificare la logica dei bot.

1.  **Creare test per `ai_utils.py`.**
    `[src/utils/test_ai_utils.py]`
    ```python
    import pytest
    from src.utils.ai_utils import AIAgent

    def test_ai_agent_initialization():
        """
        Testa che la classe AIAgent possa essere istanziata correttamente.
        """
        try:
            agent = AIAgent(project_id="test-project", location="test-location")
            assert agent.project_id == "test-project"
            assert agent.location == "test-location"
        except Exception as e:
            pytest.fail(f"L'istanziazione di AIAgent non dovrebbe fallire: {e}")

    def test_generate_response_mocked(mocker):
        """
        Testa il metodo generate_response con un mock per evitare chiamate API reali.
        """
        # Mock della dipendenza interna 'prediction_service_client.predict'
        mock_predict = mocker.patch(
            'google.cloud.aiplatform.gapic.PredictionServiceClient.predict',
            return_value='mocked response'
        )

        agent = AIAgent(project_id="test-project", location="test-location")
        response = agent.generate_response("test prompt")

        assert response == 'mocked response'
        mock_predict.assert_called_once()
    ```

2.  **Creare test per `email_sender.py`.**
    `[src/utils/test_email_sender.py]`
    ```python
    import pytest
    from src.utils.email_sender import EmailSender

    def test_email_sender_initialization():
        """
        Testa l'inizializzazione di EmailSender.
        """
        sender = EmailSender(smtp_server="smtp.test.com", port=587, sender_email="test@example.com")
        assert sender.smtp_server == "smtp.test.com"
        assert sender.port == 587
        assert sender.sender_email == "test@example.com"

    def test_send_email_mocked(mocker):
        """
        Testa l'invio dell'email mockando la libreria smtplib.
        """
        # Mock del server SMTP per evitare connessioni di rete reali
        mock_smtp = mocker.patch('smtplib.SMTP')
        instance = mock_smtp.return_value
        
        sender = EmailSender(smtp_server="smtp.test.com", port=587, sender_email="sender@test.com")
        sender.send_email("recipient@test.com", "Test Subject", "Test Body")

        mock_smtp.assert_called_with("smtp.test.com", 587)
        instance.starttls.assert_called_once()
        instance.login.assert_called_once()
        instance.sendmail.assert_called_once()
        instance.quit.assert_called_once()
    ```

3.  **Creare test per `git_utils.py`.**
    `[src/utils/test_git_utils.py]`
    ```python
    import pytest
    from src.utils import git_utils
    
    def test_run_git_command_mocked(mocker):
        """
        Testa che la funzione run_git_command costruisca ed esegua correttamente i comandi git.
        """
        # Mock di subprocess.run per intercettare i comandi di sistema
        mock_run = mocker.patch('subprocess.run')
        
        git_utils.run_git_command(['status'])
        
        # Verifica che subprocess.run sia stato chiamato con il comando corretto
        mock_run.assert_called_once_with(['git', 'status'], check=True, capture_output=True, text=True)
    ```

4.  **Creare test per `logging_utils.py`.**
    `[src/utils/test_logging_utils.py]`
    ```python
    import logging
    from src.utils.logging_utils import setup_logging

    def test_setup_logging_returns_logger():
        """
        Testa che la funzione setup_logging restituisca un'istanza di logger.
        """
        logger = setup_logging()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "ProjectBotLogger"
        assert logger.level == logging.INFO
    ```

5.  **Creare test per `report_generator.py`.**
    `[src/utils/test_report_generator.py]`
    ```python
    import pytest
    from src.utils.report_generator import ReportGenerator

    def test_report_generator_creation():
        """
        Testa la creazione di un'istanza del generatore di report.
        """
        report_gen = ReportGenerator(report_dir="test_reports")
        assert report_gen.report_dir == "test_reports"

    def test_generate_report_returns_path(mocker):
        """
        Testa che la generazione di un report restituisca un path valido.
        """
        # Mock della scrittura su file
        mocker.patch("builtins.open", mocker.mock_open())
        
        report_gen = ReportGenerator(report_dir="test_reports")
        report_path = report_gen.generate("Test Title", "Test Content")
        
        assert "Test_Title" in report_path
        assert report_path.startswith("test_reports/")
        assert report_path.endswith(".md")
    ```

6.  **Creare test per `audit_bot.py`.**
    `[src/bots/test_audit_bot.py]`
    ```python
    import pytest
    from src.bots.audit_bot import AuditBot

    def test_audit_bot_initialization(mocker):
        """
        Testa l'inizializzazione di AuditBot.
        """
        mocker.patch('src.utils.ai_utils.AIAgent') # Mock della dipendenza
        bot = AuditBot()
        assert bot is not None
        assert hasattr(bot, 'run_audit')
    ```

7.  **Creare test per `manager_bot.py`.**
    `[src/bots/test_manager_bot.py]`
    ```python
    import pytest
    from src.bots.manager_bot import ManagerBot

    def test_manager_bot_initialization(mocker):
        """
        Testa l'inizializzazione di ManagerBot.
        """
        mocker.patch('src.utils.ai_utils.AIAgent') # Mock della dipendenza
        bot = ManagerBot()
        assert bot is not None
        assert hasattr(bot, 'process_request')
    ```

8.  **Creare test per `operator_bot.py`.**
    `[src/bots/test_operator_bot.py]`
    ```python
    import pytest
    from src.bots.operator_bot import OperatorBot

    def test_operator_bot_initialization():
        """
        Testa l'inizializzazione di OperatorBot.
        """
        bot = OperatorBot("test_plan.md")
        assert bot.plan_file == "test_plan.md"
        assert hasattr(bot, 'execute_plan')
    ```

9.  **Creare test per `project_bot.py`.**
    `[src/bots/test_project_bot.py]`
    ```python
    import pytest
    from src.bots.project_bot import ProjectBot

    def test_project_bot_initialization(mocker):
        """
        Testa l'inizializzazione di ProjectBot.
        """
        mocker.patch('src.utils.ai_utils.AIAgent') # Mock della dipendenza
        bot = ProjectBot()
        assert bot is not None
        assert hasattr(bot, 'generate_plan')
    ```

## **Fase 3: Integrazione del Workflow di Test nei Bot**

Con i test di base in posizione, modifichiamo i bot per incorporare il ciclo TDD.

1.  **Potenziare `OperatorBot` per eseguire i test.**
    Modificheremo `OperatorBot` per eseguire `pytest` dopo aver completato le modifiche al codice e prima di procedere con il commit e la PR. Il processo si interromperà se i test falliscono.
    `[src/bots/operator_bot.py]`
    ```python
    import subprocess
    import logging

    # ... (import e codice esistente)

    logger = logging.getLogger(__name__)

    class OperatorBot:
        # ... (codice __init__ e metodi esistenti)

        def _run_tests(self):
            """Esegue pytest e fallisce se i test non passano."""
            logger.info("Fase di test: Esecuzione di pytest...")
            try:
                # Usiamo check=True per sollevare un'eccezione se il comando restituisce un codice di uscita diverso da zero.
                result = subprocess.run(['pytest', 'src/'], check=True, capture_output=True, text=True)
                logger.info("Pytest output:\n" + result.stdout)
                logger.info("Tutti i test sono passati con successo.")
                return True
            except subprocess.CalledProcessError as e:
                logger.error("!!! I TEST SONO FALLITI !!!")
                logger.error("Il workflow dell'OperatorBot è stato interrotto.")
                logger.error("Pytest stdout:\n" + e.stdout)
                logger.error("Pytest stderr:\n" + e.stderr)
                # L'eccezione interromperà l'esecuzione, rispettando il requisito.
                raise
            except FileNotFoundError:
                logger.error("Comando 'pytest' non trovato. Assicurarsi che sia installato e nel PATH.")
                raise

        def execute_plan(self):
            """
            Esegue il piano tecnico, applicando le modifiche e poi eseguendo i test.
            """
            logger.info(f"Inizio esecuzione del piano da {self.plan_file}")
            # ... (logica esistente per parsare ed eseguire i task del piano)
            # Qui si assume che il ciclo di esecuzione dei task sia completato.

            logger.info("Tutti i task di modifica del codice sono stati completati.")
            
            # NUOVO STEP: ESECUZIONE DEI TEST
            self._run_tests()

            # Se i test passano, il bot può procedere con commit, push e PR.
            logger.info("Poiché i test sono passati, procedo con le operazioni Git.")
            # ... (logica esistente per git commit, push, pr)

    # ... (codice main o di esecuzione esistente)

    ```

2.  **Potenziare `ProjectBot` per generare piani con test.**
    Infine, modifichiamo `ProjectBot` in modo che, da ora in poi, ogni piano generato includa automaticamente i task per la creazione dei file di test, seguendo la regola `file.py` -> `test_file.py`. Questo è un task di modifica del comportamento intrinseco del bot.
    `[src/bots/project_bot.py]`
    ```python
    # ... (import e codice esistente)

    class ProjectBot:
        # ... (codice __init__ esistente)

        def generate_plan(self, objective, file_structure):
            """

            Genera un piano tecnico basato su un obiettivo di business,
            assicurando l'inclusione di task di test per ogni file di codice.
            """
            # AGGIORNAMENTO DEL PROMPT DI SISTEMA PER L'IA
            system_prompt = f"""
            Sei il ProjectBot (CTO). Il tuo compito è tradurre un obiettivo di business in un piano tecnico dettagliato in Markdown per i tuoi OperatorBot.
            La struttura del progetto attuale è:
            {file_structure}
            
            REGOLE CRITICHE PER IL PIANO:
            1. Per ogni file di codice sorgente Python creato o modificato (es. `[path/to/my_file.py]`), DEVI includere un task successivo per creare o aggiornare un file di test corrispondente (es. `[path/to/test_my_file.py]`).
            2. I file di test devono usare la libreria `pytest`. Devono contenere test di base ma significativi (es. test di istanziazione, test di funzioni con input/output semplici, o test con mock se necessario).
            3. I task per i comandi di sistema devono usare '[shell-command]' e contenere solo il comando puro.
            4. Il piano deve essere dettagliato, sequenziale e pronto per essere eseguito.
            """
            
            user_prompt = f"Traduci questo obiettivo di business in un piano tecnico: '{objective}'"
            
            # La logica di generazione della risposta rimane la stessa, ma il prompt aggiornato
            # guiderà l'IA a rispettare i nostri nuovi standard TDD.
            plan = self.ai_agent.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            
            # Potremmo anche aggiungere una post-elaborazione qui per verificare programmaticamente
            # che ogni task di codice abbia un task di test, ma per ora ci affidiamo al prompt potenziato.
            
            return plan

    # ... (codice main o di esecuzione esistente)
    ```

## **Fase 4: Verifica Finale**

Eseguiamo l'intera suite di test una volta per assicurarci che tutti i nuovi file di test funzionino correttamente e che la nostra base di codice sia solida.

1.  **Eseguire `pytest` sull'intero progetto.**
    `[shell-command]`
    ```
    pytest src/
    ```

**Risultato Atteso:** Il comando `pytest` deve essere eseguito e riportare che tutti i test sono passati. Se ci sono errori, correggerli prima di considerare il piano completato.

---

Team, questo piano è la nostra roadmap per una maggiore qualità del software. L'esecuzione precisa è fondamentale. Iniziamo.

**ProjectBot (CTO)**