# src/operator_bot.py
import os
import google.generativeai as genai
from git import Repo
import re
import subprocess

# MODIFICA: Configurazione globale di Gemini per performance e timeout
try:
    genai.configure(
        transport="grpc",
        request_timeout=120
    )
    print("Gemini client configured for gRPC with 120s timeout.")
except Exception as e:
    print(f"Could not configure Gemini client: {e}")


def get_full_repo_url():
    token = os.getenv("GITHUB_TOKEN")
    user = os.getenv("GITHUB_USER")
    repo_slug = os.getenv("GITHUB_REPOSITORY")
    return f"https://{user}:{token}@github.com/{repo_slug}.git"

def generate_code_with_ai(task_description):
    prompt = (
        f"Sei un bot sviluppatore. Il tuo unico obiettivo è scrivere il codice o il contenuto necessario per completare il seguente task. "
        f"NON aggiungere spiegazioni o testo introduttivo. Fornisci solo il codice/contenuto richiesto, pronto per essere scritto in un file.\n\n"
        f"Task: '{task_description}'"
    )
    try:
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        # La configurazione globale del timeout viene usata automaticamente
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip()
        if cleaned_response.startswith("```") and cleaned_response.endswith("```"):
             cleaned_response = '\n'.join(cleaned_response.split('\n')[1:-1])
        return cleaned_response
    except Exception as e:
        print(f"Errore durante la generazione del codice con Gemini: {e}")
        return None

def main():
    branch_name = os.getenv("BRANCH_NAME")
    task_description = os.getenv("TASK_DESCRIPTION")
    commit_message = os.getenv("COMMIT_MESSAGE")
    repo_path = os.getcwd()

    if not all([branch_name, task_description, commit_message]):
        print("Errore: mancano delle variabili d'ambiente necessarie."); exit(1)
        
    print(f"Operator_Bot (Gemini) avviato sul branch '{branch_name}' per il task: '{task_description}'")
    
    try:
        repo = Repo(repo_path)
        repo.git.config("user.name", "AutoDevSystem Bot")
        repo.git.config("user.email", "auto-dev-system@varcavia.com")
        
        new_branch = repo.create_head(branch_name)
        new_branch.checkout()
        print(f"Creato e spostato sul nuovo branch: {branch_name}")
        
        match = re.search(r'\[(.*?)\]', task_description)
        if not match: raise ValueError("Marcatore di tipo task non trovato.")
        
        task_type = match.group(1)
        action_description = task_description.replace(f'[{task_type}]', '').strip()
        
        if task_type == 'shell-command':
            print(f"Eseguo comando shell: '{action_description}'")
            subprocess.run(action_description, shell=True, check=True)
            repo.git.add(all=True)
        else:
            file_path = task_type
            print(f"File target identificato: {file_path}")
            
            generated_content = generate_code_with_ai(task_description)
            if generated_content is None: raise Exception("La generazione del contenuto AI è fallita.")
            
            full_path = os.path.join(repo_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w') as f: f.write(generated_content)
                
            print(f"File '{file_path}' creato/aggiornato.")
            repo.git.add(full_path)
        
        if not repo.index.diff("HEAD"):
            print("Nessuna modifica rilevata. Task completato senza PR."); return
            
        repo.git.commit('-m', commit_message)
        print(f"Commit creato con messaggio: '{commit_message}'")
        
        repo_url_auth = get_full_repo_url()
        repo.git.push(repo_url_auth, branch_name)
        print(f"Push del branch '{branch_name}' completato.")
        
        pr_title = commit_message
        pr_body = f"Pull Request automatica per completare il task:\n`{task_description}`"
        
        env = os.environ.copy()
        env['GH_TOKEN'] = os.getenv("GITHUB_TOKEN")
        env['PR_TITLE'] = pr_title
        env['PR_BODY'] = pr_body
        
        gh_command = 'gh pr create --title "$PR_TITLE" --body "$PR_BODY" --base main --head "$BRANCH_NAME"'
        
        result = subprocess.run(gh_command, shell=True, capture_output=True, text=True, env=env)
        if result.returncode == 0:
            print(f"Pull Request creata con successo: {result.stdout.strip()}")
        else:
            print(f"Output del comando gh: {result.stdout}")
            print(f"Errore del comando gh: {result.stderr}")
            raise Exception(f"Creazione Pull Request fallita.")
            
    except Exception as e:
        print(f"Un errore è occorso durante l'esecuzione del task: {e}"); exit(1)

if __name__ == "__main__":
    main()