# Briefing di Progetto: VARCAVIA Office

## 1. Visione e Obiettivo
L'obiettivo è creare un sistema di sviluppo completamente autonomo ("sistema vivente") che, partendo da un `business_plan.yaml`, si auto-sviluppa, si auto-corregge e si auto-migliora. L'MVP attuale è focalizzato sulla stabilizzazione del ciclo di sviluppo TDD e sull'integrazione continua (auto-merge delle PR).

## 2. Architettura del Sistema
Il sistema è un'organizzazione di 4 bot specializzati (Manager, Project, Operator, Audit) che operano tramite workflow di GitHub Actions. La struttura dei file è la seguente:
.
├── .github/
│   └── workflows/
├── src/
│   ├── bots/
│   ├── utils/
│   └── business_plan.yaml
├── scripts/
├── .gitignore
├── README.md
├── pytest.ini
└── requirements.txt


## 3. Configurazione Google Cloud (GCP)
- **Project ID:** `varcavia-office-bc6xvv`
- **Project Number:** `826570341026`
- **Service Account:** `vertex-client@varcavia-office-bc6xvv.iam.gserviceaccount.com`
- **WIF Pool:** `varcavia-github-pool`
- **WIF Provider:** `varcavia-github-provider`
- **API Abilitate:** `aiplatform.googleapis.com`, `iam.googleapis.com`, `iamcredentials.googleapis.com`

## 4. Configurazione GitHub
- **Repository:** `https://github.com/VARCAVIA-Inc/auto-dev-system`
- **Segreti Richiesti (NOMI, NON VALORI):**
  - `BOT_GITHUB_TOKEN`
  - `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USERNAME`, `EMAIL_PASSWORD`, `SENDER_EMAIL`, `RECEIVER_EMAIL`

## 5. Stato Attuale e Problema da Risolvere
- **Stato:** Il sistema è bloccato. Il `ManagerBot` delega i task per la missione TDD, ma l'`OperatorBot` fallisce.
- **Errore Attuale:** `ModuleNotFoundError: No module named 'src.hello'`. L'errore si verifica quando `pytest` viene eseguito, perché non riesce a trovare i moduli del codice sorgente presenti nella cartella `src`.
- **Obiettivo Immediato:** Risolvere il `ModuleNotFoundError` configurando correttamente `pytest`.

## 6. Contenuto dei File Chiave

### `src/bots/manager_bot.py`
```python
# import os
import yaml
import subprocess
import time
import logging
import json
from src.utils.logging_utils import setup_logging
from src.utils.git_utils import commit_and_push_changes
from src.bots.project_bot import run_project_bot

def get_repo_root():
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

def manage_pull_requests():
    logging.info("--- ManagerBot: Inizio fase di gestione Pull Request ---")
    gh_command = ['gh', 'pr', 'list', '--head', 'autodev/', '--state', 'open', '--json', 'number,headRefName,status']
    try:
        result = subprocess.run(gh_command, capture_output=True, text=True)
        if result.returncode != 0 and (result.stdout.strip() == "" or "no open pull requests found" in result.stderr):
            logging.info("Nessuna Pull Request aperta trovata per i bot.")
            return
        result.check_returncode()
        prs = json.loads(result.stdout)
        if not prs:
            logging.info("Nessuna Pull Request aperta trovata per i bot.")
            return

        logging.info(f"Trovate {len(prs)} Pull Request create dai bot.")
        for pr in prs:
            pr_number, branch_name, status = pr['number'], pr['headRefName'], pr.get('status', 'PENDING').upper()
            logging.info(f"Analizzo PR #{pr_number} dal branch '{branch_name}' con stato '{status}'.")

            if status == 'SUCCESS':
                logging.info(f"PR #{pr_number} ha superato i test. Attivo il merge automatico.")
                merge_command = ['gh', 'pr', 'merge', str(pr_number), '--auto', '--squash', '--delete-branch']
                subprocess.run(merge_command, check=True, capture_output=True, text=True)
                logging.info(f"✅ Merge per PR #{pr_number} attivato con successo.")
            elif status == 'FAILURE':
                logging.warning(f"PR #{pr_number} ha dei controlli falliti. La chiudo.")
                comment_body = "I controlli automatici sono falliti. Chiudo questa PR."
                subprocess.run(['gh', 'pr', 'comment', str(pr_number), '--body', comment_body], check=True)
                subprocess.run(['gh', 'pr', 'close', str(pr_number)], check=True)
                subprocess.run(['gh', 'repo', 'delete-branch', branch_name], check=True)
            else: # PENDING
                logging.info(f"PR #{pr_number} è in attesa dei controlli. Nessuna azione per ora.")
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        logging.error(f"Errore durante la gestione delle Pull Request: {e}", exc_info=True)

def delegate_to_operator(task_line):
    task_description = task_line.replace("- [ ]", "").strip()
    timestamp = int(time.time())
    branch_name = f"autodev/task-{timestamp}"
    commit_message = f"feat: Implementa task '{task_description[:40]}...'"
    logging.info(f"Delega del task: '{task_description}' all'OperatorBot sul branch '{branch_name}'.")
    workflow_name = '2_operator_bot.yml'
    command = ['gh', 'workflow', 'run', workflow_name, '-f', f'branch_name={branch_name}', '-f', f'task_description={task_description}', '-f', f'commit_message={commit_message}', '--ref', 'main']
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        logging.info("✅ Workflow dell'OperatorBot attivato.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Errore attivazione OperatorBot: {e.stderr}")
        return False

def main():
    setup_logging()
    logging.info("--- ManagerBot: Avviato. Inizio ciclo di supervisione. ---")
    manage_pull_requests()
    repo_root = get_repo_root()
    business_plan_path = os.path.join(repo_root, 'src', 'business_plan.yaml')
    plan_path = os.path.join(repo_root, 'development_plan.md')
    try:
        with open(business_plan_path, 'r') as file:
            business_plan = yaml.safe_load(file)
    except FileNotFoundError:
        logging.critical("business_plan.yaml non trovato. Interruzione.")
        return

    if os.path.exists(plan_path):
        logging.info("Trovato un 'development_plan.md'. Supervisione del piano in corso...")
        try:
            with open(plan_path, 'r+') as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    if line.strip().startswith("- [ ]"):
                        if delegate_to_operator(line):
                            lines[i] = line.replace("- [ ]", "- [x]", 1)
                            f.seek(0); f.writelines(lines); f.truncate()
                            commit_msg = f"chore(manager): Delegato task '{line.strip()[:40]}...'"
                            commit_and_push_changes(repo_root, commit_msg, "main")
                        return 
                logging.info("Tutti i sotto-task del piano di sviluppo sono completati.")
                for phase in business_plan.get('phases', []):
                    for task in phase.get('tasks', []):
                        if task.get('status') == 'planned':
                            task['status'] = 'completed'
                            with open(business_plan_path, 'w') as bp_file:
                                yaml.dump(business_plan, bp_file, default_flow_style=False, sort_keys=False)
                            commit_msg_bp = f"feat(manager): Completa il task '{task.get('description', '')[:50]}...'"
                            commit_and_push_changes(repo_root, commit_msg_bp, "main")
                            os.remove(plan_path)
                            commit_msg_plan = "chore(manager): Rimuove il piano di sviluppo completato"
                            commit_and_push_changes(repo_root, commit_msg_plan, "main")
                            return
        except Exception as e:
            logging.error(f"Errore durante la gestione del development_plan: {e}")
            return
    else:
        for p_idx, phase in enumerate(business_plan.get('phases', [])):
            for t_idx, task in enumerate(phase.get('tasks', [])):
                if task.get('status') == 'pending':
                    logging.info(f"Trovato task 'pending': {task.get('description')}. Attivo il ProjectBot.")
                    run_project_bot(task, t_idx, p_idx)
                    return
    logging.info("--- ManagerBot: Nessun task attivo o piano da eseguire. Ciclo completato. ---")

if __name__ == "__main__":
    main()

### `src/bots/project_bot.py`
```python
# import os
import yaml
import logging
import subprocess
import re
from src.utils.git_utils import commit_and_push_changes
from src.utils.ai_utils import get_gemini_model, generate_response, PLANNING_MODEL

def is_plan_valid(plan_text: str) -> bool:
    """Controlla se un piano di sviluppo generato è valido usando una regex severa."""
    logging.info("Validazione del piano di sviluppo generato...")
    has_tasks = False
    for line in plan_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("- [ ]"):
            has_tasks = True
            if not re.match(r'^\s*-\s*\[\s*\]\s*\[(.+?)\]', line):
                logging.error(f"Riga di task non valida trovata: '{line}'. Formato non corretto.")
                return False
    if not has_tasks:
        logging.error("Validazione fallita: il piano non contiene task azionabili ('- [ ]').")
    return has_tasks

def update_business_plan_status(task_index, phase_index, new_status):
    repo_root = os.getenv('GITHUB_WORKSPACE', os.getcwd())
    business_plan_path = os.path.join(repo_root, 'src', 'business_plan.yaml')
    try:
        with open(business_plan_path, 'r') as file:
            plan = yaml.safe_load(file)
        plan['phases'][phase_index]['tasks'][task_index]['status'] = new_status
        with open(business_plan_path, 'w') as file:
            yaml.dump(plan, file, default_flow_style=False, sort_keys=False)
        logging.info(f"Stato del task aggiornato a '{new_status}'.")
    except Exception as e:
        logging.error(f"Errore durante l'aggiornamento del Business Plan: {e}", exc_info=True)

def run_project_bot(task_details, task_index, phase_index):
    task_description = task_details.get('description', 'N/A')
    logging.info(f"--- ProjectBot: Inizio Pianificazione per '{task_description}' ---")
    try:
        gemini_model = get_gemini_model(PLANNING_MODEL)
        repo_root = os.getenv('GITHUB_WORKSPACE', os.getcwd())
        result = subprocess.run(['ls', '-R'], cwd=repo_root, capture_output=True, text=True, check=True)
        file_structure = result.stdout
    except Exception as e:
        logging.error(f"Errore nella preparazione della pianificazione: {e}")
        update_business_plan_status(task_index, phase_index, "planning_failed")
        return

    prompt = (
        f"Sei il ProjectBot (CTO). Traduci un obiettivo di business in un piano tecnico in Markdown per gli OperatorBot.\n"
        f"Struttura del progetto attuale:\n```\n{file_structure}\n```\n\n"
        f"Obiettivo di Business: '{task_description}'.\n\n"
        f"**REGOLE CRITICHE E OBBLIGATORIE PER IL PIANO:**\n"
        f"1. Il piano DEVE contenere una lista di sotto-task.\n"
        f"2. OGNI SINGOLO SOTTO-TASK DEVE iniziare con '- [ ]' seguito IMMEDIATAMENTE da un marcatore tra parentesi quadre, come '[percorso/del/file.py]' o '[shell-command]'.\n"
        f"3. Per ogni file di codice sorgente, DEVI includere un task successivo per un file di test corrispondente (es. `[tests/bots/test_mio_file.py]`).\n"
        f"4. Il comando in un task '[shell-command]' DEVE essere puro, senza virgolette inverse (backticks)."
    )

    piano_generato = generate_response(gemini_model, prompt)
    
    if not piano_generato or not is_plan_valid(piano_generato):
        logging.error("Fallimento nella generazione del piano: l'output dell'IA è vuoto o non valido.")
        update_business_plan_status(task_index, phase_index, "planning_failed")
        return

    plan_path = os.path.join(repo_root, 'development_plan.md')
    with open(plan_path, 'w') as f:
        f.write(piano_generato)
    logging.info(f"Piano di sviluppo TDD valido salvato in '{plan_path}'")

    update_business_plan_status(task_index, phase_index, "planned")
    commit_message = f"feat(project): Generato piano TDD valido per '{task_description[:45]}...'"
    commit_and_push_changes(repo_root, commit_message, "main")
    
    logging.info(f"--- ProjectBot: Pianificazione TDD completata. ---")
    
### `src/bots/operator_bot.py`
```python
# import os
import logging
import re
import subprocess
from git import Repo
from src.utils.logging_utils import setup_logging
from src.utils.ai_utils import get_gemini_model, generate_response, EXECUTION_MODEL

def run_tests():
    logging.info("Esecuzione dei test con pytest...")
    try:
        result = subprocess.run(['pytest'], capture_output=True, text=True)
        if result.returncode == 0:
            logging.info("✅ Tutti i test sono passati.")
            return True
        elif result.returncode == 5:
            logging.warning("✅ Nessun test trovato da eseguire. Considerato successo per questa fase.")
            return True
        else:
            logging.error(f"❌ Test falliti. Output:\n{result.stdout}\n{result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Errore imprevisto durante l'esecuzione dei test: {e}")
        return False

def create_pull_request(branch_name):
    try:
        logging.info(f"Creazione della Pull Request per il branch '{branch_name}'...")
        env = os.environ.copy()
        env['GH_TOKEN'] = os.getenv("GITHUB_TOKEN")
        command = f"gh pr create --base main --head \"{branch_name}\" --fill"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True, env=env)
        logging.info(f"✅ Pull Request creata: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        if "A pull request for" in e.stderr and "already exists" in e.stderr:
            logging.warning("Una Pull Request per questo branch esiste già.")
            return True
        logging.error(f"❌ Creazione Pull Request fallita: {e.stderr}")
        return False

def main():
    setup_logging()
    branch_name = os.getenv("BRANCH_NAME")
    task_description = os.getenv("TASK_DESCRIPTION")
    commit_message = os.getenv("COMMIT_MESSAGE")
    repo_path = os.getenv('GITHUB_WORKSPACE', os.getcwd())

    if not all([branch_name, task_description, commit_message]):
        logging.critical("Errore: mancano variabili d'ambiente necessarie."); exit(1)
        
    logging.info(f"--- OperatorBot: Avviato per il task: '{task_description}' ---")
    
    try:
        repo = Repo(repo_path)
        repo.git.config("user.name", "VARCAVIA Office Bot")
        repo.git.config("user.email", "bot@varcavia.com")
        
        if branch_name not in repo.heads:
            repo.create_head(branch_name).checkout()
        else:
            repo.heads[branch_name].checkout()
        logging.info(f"Spostato sul branch: {branch_name}")
        
        match = re.search(r'\[(.*?)\]', task_description)
        if not match: raise ValueError(f"Marcatore di tipo task non trovato in '{task_description}'.")
        
        task_type = match.group(1)
        action_description = task_description.replace(f'[{task_type}]', '').strip()
        
        if task_type == 'shell-command':
            logging.info(f"Eseguo comando shell: '{action_description}'")
            subprocess.run(action_description, shell=True, check=True, cwd=repo_path)
        else:
            file_path = task_type
            logging.info(f"Generazione contenuto per il file: {file_path}")
            model = get_gemini_model(EXECUTION_MODEL)
            generated_content = generate_response(model, f"Scrivi il codice/contenuto per questo task: '{action_description}'. Fornisci solo il codice puro, senza spiegazioni o markdown.")
            if generated_content is None: raise Exception("Generazione del contenuto AI fallita.")
            full_path = os.path.join(repo_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f: f.write(generated_content)
            logging.info(f"File '{file_path}' creato/aggiornato.")
        
        if not run_tests():
            raise Exception("I test unitari sono falliti. Annullamento della Pull Request.")

        repo.git.add(all=True)
        if not repo.is_dirty(untracked_files=True):
            logging.warning("Nessuna modifica rilevata. Task completato senza PR."); return
            
        repo.git.commit('-m', commit_message)
        logging.info(f"Commit creato: '{commit_message}'")
        
        remote_url = f"https://x-access-token:{os.getenv('GITHUB_TOKEN')}@github.com/{os.getenv('GITHUB_REPOSITORY')}.git"
        repo.git.push(remote_url, f'HEAD:{branch_name}', '--force')
        logging.info(f"Push del branch '{branch_name}' completato.")
        
        create_pull_request(branch_name)

    except Exception as e:
        logging.critical(f"❌ Errore critico durante l'esecuzione del task: {e}", exc_info=True); exit(1)

    logging.info(f"--- OperatorBot: Task completato. ---")

if __name__ == "__main__":
    main()

### `.github/workflows/1_manager_bot.yml`
```yaml name: 1. Manager Bot Orchestration

on:
  push:
    branches: [ main ]
    paths-ignore:
      - 'README.md'
  workflow_dispatch:
  schedule:
    - cron: '*/15 * * * *'

jobs:
  run_manager_bot:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      actions: write 
      id-token: write
    steps:
      - uses: actions/checkout@v4
        with: { token: '${{ secrets.BOT_GITHUB_TOKEN }}' }
      
      - uses: 'google-github-actions/auth@v2'
        with:
          workload_identity_provider: 'projects/826570341026/locations/global/workloadIdentityPools/varcavia-github-pool/providers/varcavia-github-provider'
          service_account: 'vertex-client@varcavia-office-bc6xvv.iam.gserviceaccount.com'

      - uses: actions/setup-python@v5
        with: { python-version: '3.9' }

      - name: Install Dependencies & Run
        env:
          GITHUB_TOKEN: ${{ secrets.BOT_GITHUB_TOKEN }}
          GCP_PROJECT: 'varcavia-office-bc6xvv'
          PYTHONPATH: ${{ github.workspace }}
        run: |
          pip install -r requirements.txt
          gh auth setup-git
          python src/bots/manager_bot.py

# name: 1. Manager Bot Orchestration

on:
  push:
    branches: [ main ]
    paths-ignore:
      - 'README.md'
  workflow_dispatch:
  schedule:
    - cron: '*/15 * * * *'

jobs:
  run_manager_bot:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      actions: write 
      id-token: write
    steps:
      - uses: actions/checkout@v4
        with: { token: '${{ secrets.BOT_GITHUB_TOKEN }}' }
      
      - uses: 'google-github-actions/auth@v2'
        with:
          workload_identity_provider: 'projects/826570341026/locations/global/workloadIdentityPools/varcavia-github-pool/providers/varcavia-github-provider'
          service_account: 'vertex-client@varcavia-office-bc6xvv.iam.gserviceaccount.com'

      - uses: actions/setup-python@v5
        with: { python-version: '3.9' }

      - name: Install Dependencies & Run
        env:
          GITHUB_TOKEN: ${{ secrets.BOT_GITHUB_TOKEN }}
          GCP_PROJECT: 'varcavia-office-bc6xvv'
          PYTHONPATH: ${{ github.workspace }}
        run: |
          pip install -r requirements.txt
          gh auth setup-git
          python src/bots/manager_bot.py

### `.github/workflows/2_operator_bot.yml`
```yaml
# name: 2. Operator Bot Task Execution

on:
  workflow_dispatch:
    inputs:
      branch_name: { required: true }
      task_description: { required: true }
      commit_message: { required: true }

jobs:
  execute_task:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
        with: { token: '${{ secrets.BOT_GITHUB_TOKEN }}' }

      - uses: 'google-github-actions/auth@v2'
        with:
          workload_identity_provider: 'projects/826570341026/locations/global/workloadIdentityPools/varcavia-github-pool/providers/varcavia-github-provider'
          service_account: 'vertex-client@varcavia-office-bc6xvv.iam.gserviceaccount.com'

      - uses: actions/setup-python@v5
        with: { python-version: '3.9' }

      - name: Install Dependencies & Run
        env:
          BRANCH_NAME: ${{ github.event.inputs.branch_name }}
          TASK_DESCRIPTION: ${{ github.event.inputs.task_description }}
          COMMIT_MESSAGE: ${{ github.event.inputs.commit_message }}
          GITHUB_TOKEN: ${{ secrets.BOT_GITHUB_TOKEN }}
          GCP_PROJECT: 'varcavia-office-bc6xvv'
          PYTHONPATH: ${{ github.workspace }}
        run: |
          pip install -r requirements.txt
          gh auth setup-git
          python src/bots/operator_bot.py

### `.github/workflows/4_validation.yml`
```yaml
# name: 4. PR Validation

on:
  pull_request:
    branches: [ main ]

jobs:
  validate-pr:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - name: Checkout PR code
        uses: actions/checkout@v4

      - name: 'Authenticate to Google Cloud'
        uses: 'google-github-actions/auth@v2'
        with:
          workload_identity_provider: 'projects/826570341026/locations/global/workloadIdentityPools/varcavia-github-pool/providers/varcavia-github-provider'
          service_account: 'vertex-client@varcavia-office-bc6xvv.iam.gserviceaccount.com'

      - name: Set up Python
        uses: actions/setup-python@v5
        with: { python-version: '3.9' }

      - name: Install Dependencies
        run: pip install -r requirements.txt

      - name: Run Unit Tests
        run: pytest