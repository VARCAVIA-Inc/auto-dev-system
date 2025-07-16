## Piano di Sviluppo Calcolatrice Base in Python

**Fase 1: Setup del progetto**

- [ ] [shell-command] mkdir calcolatrice
- [ ] [shell-command] cd calcolatrice
- [ ] [shell-command] touch README.md
- [ ] [README.md] Aggiungere titolo e breve descrizione del progetto al README.
- [ ] [shell-command] mkdir src
- [ ] [shell-command] mkdir tests


**Fase 2: Implementazione della logica della calcolatrice**

- [ ] [src/calculator.py] Creare il file calculator.py
- [ ] [src/calculator.py] Definire la classe `Calculator`.
- [ ] [src/calculator.py] Implementare il metodo `add(self, x, y)` per l'addizione.
- [ ] [src/calculator.py] Implementare il metodo `subtract(self, x, y)` per la sottrazione.
- [ ] [src/calculator.py] Implementare il metodo `multiply(self, x, y)` per la moltiplicazione.
- [ ] [src/calculator.py] Implementare il metodo `divide(self, x, y)` per la divisione.
- [ ] [src/calculator.py] Gestire l'eccezione `ZeroDivisionError` nel metodo `divide`.


**Fase 3: Creazione dell'interfaccia utente (CLI)**

- [ ] [src/main.py] Creare il file main.py
- [ ] [src/main.py] Importare la classe `Calculator` da `calculator.py`.
- [ ] [src/main.py] Creare un ciclo `while` per l'interazione continua con l'utente.
- [ ] [src/main.py] Visualizzare un menu con le opzioni disponibili (addizione, sottrazione, moltiplicazione, divisione, uscita).
- [ ] [src/main.py] Ottenere l'input dell'utente per l'operazione desiderata.
- [ ] [src/main.py] Ottenere l'input dell'utente per i due numeri.
- [ ] [src/main.py] Chiamare il metodo corrispondente della classe `Calculator` in base all'input dell'utente.
- [ ] [src/main.py] Visualizzare il risultato dell'operazione.
- [ ] [src/main.py] Gestire input non validi (es. caratteri non numerici, opzioni di menu inesistenti).


**Fase 4: Testing**

- [ ] [tests/test_calculator.py] Creare il file test_calculator.py.
- [ ] [tests/test_calculator.py] Importare la classe `Calculator` e `unittest`.
- [ ] [tests/test_calculator.py] Creare una classe di test che eredita da `unittest.TestCase`.
- [ ] [tests/test_calculator.py] Scrivere test unitari per ogni metodo della classe `Calculator` (add, subtract, multiply, divide).
- [ ] [tests/test_calculator.py] Includere test per la gestione dell'eccezione `ZeroDivisionError`.
- [ ] [shell-command] Eseguire i test con `python -m unittest discover tests`.

**Fase 5: Documentazione**

- [ ] [README.md] Aggiungere istruzioni per l'esecuzione del programma.
- [ ] [README.md] Aggiungere esempi di utilizzo.
- [ ] [src/calculator.py] Aggiungere docstring per la classe e i metodi.
- [ ] [src/main.py] Aggiungere docstring alle funzioni principali.


**Fase 6: Rifiniture (opzionale)**

- [ ] [src/main.py]  Migliorare l'interfaccia utente (es. gestione degli errori più user-friendly).
- [ ] [src/calculator.py] Aggiungere funzionalità extra (es. operazioni più avanzate, memoria).
- [ ] [README.md]  Aggiungere informazioni sulla licenza.
