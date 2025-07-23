```markdown
# Piano di Sviluppo Tecnico

**Obiettivo di Business:** Crea un file hello.py che stampa Hello World e un test per verificarlo.

Ecco la lista dei task per raggiungere questo obiettivo:

- [ ] [src/hello.py] Crea un nuovo file che definisce una funzione `get_greeting()` che restituisce la stringa "Hello World!" e, all'interno di un blocco `if __name__ == "__main__":`, stampa il risultato della chiamata a questa funzione.
- [ ] [shell-command] mkdir -p tests
- [ ] [tests/__init__.py] Crea un file vuoto per contrassegnare la directory `tests` come un pacchetto Python.
- [ ] [tests/test_hello.py] Crea un file di test che importa la funzione `get_greeting` da `src.hello`. Aggiungi un test `test_get_greeting` che verifica che la funzione restituisca correttamente la stringa "Hello World!".
- [ ] [requirements.txt] Assicurati che `pytest` sia presente nel file. Se non c'è, aggiungilo.
- [ ] [shell-command] python3 -m pytest tests/test_hello.py
```