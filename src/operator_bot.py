import os
import openai
from git import Repo
import re
import subprocess

def get_full_repo_url():
    """Costruisce l'URL del repo con autenticazione."""
    token = os.getenv("GITHUB_TOKEN")
    user = os.getenv("GITHUB_USER")
    repo_slug = os.getenv("GITHUB_REPOSITORY")
    return f"https://{user}:{token}@github.com/{repo_slug}.git"

def generate_code_with_ai(task_description):
    """
    Genera codice o contenuto basato su un task specifico.
    """
    prompt = (
        f"Sei un bot sviluppatore. Il tuo unico obiettivo è scrivere il codice o il contenuto necessario per completare il seguente task. "
        f"NON aggiungere spiegazioni o testo introduttivo. Fornisci solo il codice/contenuto richiesto, pronto per essere scritto in un file.\n\n"
        f"Task: '{task_description}'"
    )
    
    try:
        openai.api_key = os.getenv("OPENAI_API_KEY")
        completion = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Errore durante la generazione del codice: {e}")
        return None

def main():
    branch_name = os.getenv("BRANCH_NAME")
    task_description = os.getenv("TASK_DESCRIPTION")
    commit_message = os.getenv("COMMIT_MESSAGE")
    repo_path = os.getcwd()

    if not all([branch_name, task_description, commit_message]):
        print("Errore: mancano delle variabili d'ambiente necessarie.")
        exit(1)

    print(f"Operator_Bot avviato sul branch '{branch_name}' per il task: '{task_description}'")

    try:
        match = re.search(r'\[(.*?)\]', task_description)
        if not match:
            raise ValueError("Percorso del file non trovato nella descrizione del task. Il formato deve essere '[percorso/del/file.ext] Descrizione'.")
        
        file_path = match.group(1)
        print(f"File target identificato: {file_path}")

        repo = Repo(repo_path)
        repo.git.config("user.name", "AutoDevSystem Bot")
        repo.git.config("user.email", "auto-dev-system@varcavia.com")
        
        new_branch = repo.create_head(branch_name)
        new_branch.checkout()
        print(f"Creato e spostato sul nuovo branch: {branch_name}")

        generated_content = generate_code_with_ai(task_description)
        if generated_content is None:
            raise Exception("La generazione del contenuto è fallita.")
            
        if generated_content.strip().startswith("```"):
            generated_content = '\n'.join(generated_content.strip().split('\n')[1:-1])

        full_path = os.path.join(repo_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(generated_content)
        print(f"File '{file_path}' creato/aggiornato.")

        repo.git.add(full_path)
        repo.git.commit('-m', commit_message)
        print(f"Commit creato con messaggio: '{commit_message}'")
        
        repo_url_auth = get_full_repo_url()
        repo.git.push(repo_url_auth, branch_name)
        print(f"Push del branch '{branch_name}' completato.")
        
        pr_title = commit_message
        pr_body = f"Pull Request automatica per completare il task:\n`{task_description}`"
        
        gh_command = f'gh pr create --title "{pr_title}" --body "{pr_body}" --base main --head {branch_name}'
        result = subprocess.run(gh_command, shell=True, capture_output=True, text=True, env=os.environ)
        
        if result.returncode == 0:
            print(f"Pull Request creata con successo: {result.stdout.strip()}")
        else:
            raise Exception(f"Creazione Pull Request fallita: {result.stderr}")

    except Exception as e:
        print(f"Un errore è occorso durante l'esecuzione del task: {e}")
        exit(1)

if __name__ == "__main__":
    main()