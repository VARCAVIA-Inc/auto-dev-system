import os
import logging
import re
from typing import List, Dict, Optional

def get_plan_path() -> str:
    """Restituisce il percorso assoluto del piano di sviluppo."""
    repo_root = os.getenv('GITHUB_WORKSPACE', os.getcwd())
    return os.path.join(repo_root, 'development_plan.md')

def parse_plan() -> Optional[List[Dict]]:
    """
    Legge il development_plan.md e lo trasforma in una lista strutturata di task.
    Ogni task è un dizionario con 'line_index', 'status', e 'description'.
    """
    plan_path = get_plan_path()
    if not os.path.exists(plan_path):
        return None

    tasks = []
    with open(plan_path, 'r') as f:
        for i, line in enumerate(f.readlines()):
            line = line.strip()
            if not line.startswith("- ["):
                continue

            # Estrae lo stato (es. ' ', 'x', 'F', 'P') e la descrizione
            match = re.match(r'^\s*-\s*\[(.)\]\s*(.*)', line)
            if match:
                status_char = match.group(1)
                description = match.group(2).strip()

                status_map = {' ': 'PENDING', 'x': 'DONE', 'F': 'FAILED', 'P': 'IN_PROGRESS'}

                tasks.append({
                    "line_index": i,
                    "description": description,
                    "status": status_map.get(status_char, 'UNKNOWN')
                })
    return tasks

def update_task_status(line_index: int, new_status: str):
    """
    Aggiorna lo stato di un singolo task nel development_plan.md.
    """
    plan_path = get_plan_path()
    status_map = {'PENDING': ' ', 'DONE': 'x', 'FAILED': 'F', 'IN_PROGRESS': 'P'}

    if new_status not in status_map:
        logging.error(f"Stato '{new_status}' non valido.")
        return

    try:
        with open(plan_path, 'r') as f:
            lines = f.readlines()

        line = lines[line_index].strip()

        # Sostituisce il carattere dello stato mantenendo il resto della riga
        updated_line = re.sub(r'\[.\]', f'[{status_map[new_status]}]', line, 1)
        lines[line_index] = updated_line + '\n'

        with open(plan_path, 'w') as f:
            f.writelines(lines)
        logging.info(f"Task alla linea {line_index} aggiornato a '{new_status}'.")

    except (IOError, IndexError) as e:
        logging.error(f"Errore durante l'aggiornamento dello stato del task: {e}", exc_info=True)

def find_next_task() -> Optional[Dict]:
    """Trova il prossimo task PENDING o FAILED da eseguire."""
    tasks = parse_plan()
    if not tasks:
        return None

    # Priorità ai task falliti da ritentare (in futuro aggiungeremo un contatore di retry)
    for task in tasks:
        if task['status'] == 'FAILED':
            return task

    # Altrimenti, il primo task in attesa
    for task in tasks:
        if task['status'] == 'PENDING':
            return task

    return None # Nessun task da eseguire