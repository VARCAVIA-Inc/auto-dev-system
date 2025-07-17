## Piano di Sviluppo Tecnico: Creazione README.md in /docs

**Obiettivo:** Creare un file README.md nella cartella 'docs' contenente il titolo '# System Test' e il testo 'Hello, VARCAVIA-Office! The autonomous cycle is working.'.

**Prerequisiti:** Nessuno. Si assume che il progetto esista già con la struttura descritta.

**Task:**

- [ ] [shell-command] `mkdir docs` (Creazione della cartella 'docs' se non esiste)
- [ ] [docs/README.md] Creare il file README.md all'interno della cartella 'docs'.
- [ ] [docs/README.md] Aggiungere il titolo '# System Test' al file README.md.
- [ ] [docs/README.md] Aggiungere il testo 'Hello, VARCAVIA-Office! The autonomous cycle is working.' al file README.md, sotto il titolo.


**Verifica:**

- [ ] [shell-command] `cat docs/README.md` per verificare il contenuto del file.  Il risultato atteso è:

```
# System Test
Hello, VARCAVIA-Office! The autonomous cycle is working.
```

**Note:**

* Il comando `mkdir docs` include l'opzione  implicita di non generare errori se la directory esiste già, rispettando la regola fondamentale di non creare file o cartelle esistenti.


**Possibili Problemi e Soluzioni:**

* **Permessi insufficienti:** Se si verificano problemi di permessi durante la creazione della cartella o del file, utilizzare `sudo mkdir docs` e `sudo touch docs/README.md` (se necessario, seguito da `sudo chmod 644 docs/README.md` per impostare i permessi di lettura/scrittura per l'utente e solo lettura per gli altri).


**Considerazioni Aggiuntive:**

* Questo piano presuppone l'utilizzo di un sistema operativo basato su Unix (Linux, macOS).  Se si utilizza Windows, i comandi `mkdir` e `cat` possono essere sostituiti rispettivamente con `mkdir` e `type`.


Questo piano dettagliato fornisce una guida passo-passo per raggiungere l'obiettivo, rispettando le regole fondamentali e anticipando potenziali problemi.
