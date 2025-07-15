import os
import openai
from git import Repo

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
        f"NON aggiungere spiegazioni, commenti extra, o testo introduttivo. Fornisci solo il codice/contenuto richiesto.\n\n"
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
    # 1. Recupera le istruzioni dall'ambiente
    branch_name = os.getenv("BRANCH_NAME")
    task_description = os.getenv("TASK_DESCRIPTION")
    commit_message = os.getenv("COMMIT_MESSAGE")
    repo_path = os.getcwd()

    if not all([branch_name, task_description, commit_message]):
        print("Errore: mancano delle variabili d'ambiente necessarie.")
        return

    print(f"Operator_Bot avviato sul branch '{branch_name}' per il task: '{task_description}'")

    # 2. Prepara il repository e crea un nuovo branch
    repo = Repo(repo_path)
    repo.git.config("user.name", "AutoDevSystem Bot")
    repo.git.config("user.email", "auto-dev-system@varcavia.com")
    
    new_branch = repo.create_head(branch_name)
    new_branch.checkout()
    print(f"Creato e spostato sul nuovo branch: {branch_name}")

    # 3. Genera il codice/contenuto via AI
    # Per estrarre il nome del file dal task, usiamo un approccio semplice per ora
    # Esempio task: "Creare il file src/calculator.py con una funzione add"
    try:
        # Estrai il percorso del file dal task (logica da migliorare in futuro)
        file_path = [word for word in task_description.split() if '.py' in word or '.md' in word or '.txt' in word][0]
        generated_content = generate_code_with_ai(task_description)
    
        if not generated_content:
            raise Exception("La generazione del contenuto è fallita.")

        # 4. Scrivi il file e committa
        full_path = os.path.join(repo_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(generated_content)
        print(f"File '{file_path}' creato/aggiornato.")

        repo.git.add(full_path)
        repo.git.commit('-m', commit_message)
        print(f"Commit creato con messaggio: '{commit_message}'")
        
        # 5. Push del nuovo branch
        repo_url_auth = get_full_repo_url()
        repo.git.push(repo_url_auth, branch_name)
        print(f"Push del branch '{branch_name}' completato.")

        # 6. Crea la Pull Request usando l'API di GitHub (via gh CLI)
        pr_title = commit_message
        pr_body = f"Pull Request automatica per completare il task:\n`{task_description}`"
        
        # Usiamo os.system per chiamare la GitHub CLI, già autenticata dal token
        gh_command = f'gh pr create --title "{pr_title}" --body "{pr_body}" --base main --head {branch_name}'
        os.system(gh_command)
        print(f"Pull Request per il branch '{branch_name}' creata con successo.")

    except Exception as e:
        print(f"Un errore è occorso durante l'esecuzione del task: {e}")
        # In futuro, qui si potrebbe notificare il Project_Bot del fallimento

if __name__ == "__main__":
    main()
