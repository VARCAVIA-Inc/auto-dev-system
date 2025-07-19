Assolutamente. Ecco il piano tecnico dettagliato per gli OperatorBot.

---

**A:** OperatorBot
**DA:** ProjectBot (CTO)
**OGGETTO:** Piano Tecnico - Integrazione del Framework di Test Unitario

Ho analizzato l'obiettivo di business e ho preparato il seguente piano tecnico per la sua implementazione. Questo piano è suddiviso in fasi sequenziali. Seguite ogni passaggio con precisione. La qualità del codice e il rispetto delle procedure sono fondamentali per il successo di questa iniziativa.

### **Obiettivo di Business**
Potenziare il ProjectBot per generare un file di test unitario (`*_test.py`) per ogni nuovo file Python. Potenziare l'OperatorBot per eseguire `pytest` dopo aver scritto il codice e prima di creare la PR. Il workflow dell'OperatorBot deve fallire se i test non passano.

---

### **Piano Tecnico Dettagliato**

#### **Fase 1: Preparazione dell'Ambiente e delle Dipendenze**

L'obiettivo di questa fase è strutturare il progetto per supportare i test e aggiungere le librerie necessarie.

- [x] [shell-command] `mkdir tests`
- [x] [shell-command] `touch tests/__init__.py`
- [x] [requirements.txt] Aggiungere `pytest` e `pytest-mock` al file delle dipendenze per l'esecuzione dei test e la gestione dei mock.
    ```
    pytest
    pytest-mock
    ```
- [x] [.gitignore] Aggiungere le directory della cache di `pytest` e `mypy` per evitare che vengano tracciate da git.
    ```
    # Pytest
    .pytest_cache/
    
    # Mypy
    .mypy_cache/
    ```

#### **Fase 2: Creazione di Utility per la Generazione dei Test**

Centralizzeremo la logica di generazione dei test in un nuovo modulo di utility per mantenere il codice pulito e modulare.

- [x] [src/utils/test_utils.py] Creare un nuovo file per le utility di generazione dei test.
- [ ] [src/utils/test_utils.py] Importare le dipendenze necessarie, inclusa la nostra utility AI.
    ```python
    from src.utils import ai_utils
    ```
- [ ] [src/utils/test_utils.py] Implementare la funzione `generate_test_file_content(source_code: str, file_path: str) -> str`. Questa funzione:
    1.  Prende in input il codice sorgente di un file Python e il suo percorso.
    2.  Crea un prompt specifico per l'LLM, istruendolo a generare test unitari usando `pytest` e `unittest.mock`. Il prompt deve enfatizzare la necessità di testare tutte le funzioni pubbliche, gestire le dipendenze con i mock e seguire le best practice di `pytest`.
    3.  Invoca `ai_utils.get_completion()` con il prompt.
    4.  Restituisce il codice di test generato dall'AI.
- [ ] [src/utils/__init__.py] Esponi la nuova utility aggiornando il file `__init__.py` della directory utils.

#### **Fase 3: Potenziamento del ProjectBot**

Modificheremo il `ProjectBot` per includere la creazione dei file di test nel piano tecnico che genera.

- [ ] [src/bots/project_bot.py] Importare la nuova utility di generazione test: `from src.utils.test_utils import generate_test_file_content`.
- [ ] [src/bots/project_bot.py] Modificare il metodo che genera il piano tecnico. La logica deve essere aggiornata come segue:
    - Quando un task per la creazione di un nuovo file Python (es. `[src/bots/new_bot.py]`) viene generato, il `ProjectBot` deve:
        1. Generare il contenuto del codice per `new_bot.py`.
        2. Invocare `generate_test_file_content()` passando il codice appena generato e il percorso del file.
        3. Aggiungere un nuovo task sequenziale al piano tecnico per creare il file di test corrispondente. Il percorso del file di test deve essere `tests/test_new_bot.py`.
        
    **Esempio di logica da integrare:**
    ```python
    # ... all'interno della generazione del piano ...
    if task_is_new_python_file(task):
        # ... logica esistente per generare il contenuto del file sorgente ...
        source_code_content = generate_source_code(...)
        
        # Nuova logica
        test_code_content = generate_test_file_content(source_code=source_code_content, file_path=task.path)
        test_file_path = "tests/test_" + os.path.basename(task.path)
        
        # Aggiungere il task di scrittura del file di test al piano
        new_test_task = f"- [ ] [{test_file_path}] Creare test unitari per {os.path.basename(task.path)}."
        # ... inserire new_test_task e il suo contenuto nel piano ...
    ```

#### **Fase 4: Potenziamento dell'OperatorBot**

Modificheremo l'`OperatorBot` per eseguire i test e condizionare il workflow al loro esito.

- [ ] [src/bots/operator_bot.py] Importare i moduli `subprocess` e `sys` per eseguire comandi esterni e gestire l'uscita.
- [ ] [src/bots/operator_bot.py] Nel metodo principale che esegue i task del piano tecnico, individuare il punto **dopo** che tutti i file sono stati scritti/modificati e **prima** dell'esecuzione di `git add`.
- [ ] [src/bots/operator_bot.py] Inserire una nuova funzione o blocco di codice per eseguire i test. Questo blocco deve:
    1.  Eseguire il comando `pytest` usando `subprocess.run()`. Assicurarsi di catturare `stdout`, `stderr` e il codice di ritorno.
    2.  Controllare il `returncode` del processo.
    3.  **Se il `returncode` è diverso da 0:**
        - Loggare un messaggio di errore critico.
        - Includere l'output completo di `stdout` e `stderr` di `pytest` nel log per facilitare il debug.
        - Interrompere l'esecuzione del bot immediatamente, causando il fallimento del workflow (es. `sys.exit(1)`).
    4.  **Se il `returncode` è 0:**
        - Loggare un messaggio di successo (es. "Tutti i test sono passati con successo.").
        - Permettere al bot di procedere con `git add`, `git commit` e la creazione della Pull Request.
    
    **Esempio di codice da implementare:**
    ```python
    # ... dopo il loop di scrittura dei file ...
    
    print("--- ESECUZIONE DEI TEST UNITARI ---")
    result = subprocess.run(["pytest"], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("!!! FALLIMENTO DEI TEST UNITARI !!!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        print("Workflow interrotto. La Pull Request non verrà creata.")
        sys.exit(1)
    else:
        print("--- Tutti i test sono passati con successo. Procedo con il commit. ---")
        print(result.stdout)

    # ... logica di git add, commit, push ...
    ```

La corretta implementazione di questo piano garantirà che ogni nuova funzionalità sia accompagnata da test di qualità e che solo il codice funzionante venga proposto per l'integrazione. Procedete.