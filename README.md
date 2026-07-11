# Ispravljanje grešaka u tekstu na srpskom jeziku

Poređenje tri pristupa za ispravljanje pravopisnih grešaka na srpskom: rečnik + edit rastojanje, n-gram jezički model i LLM (zero-shot).
Instalacija: `pip install -r requirements.txt`, uz `GROQ_API_KEY` u `.env` za LLM korak.
Skripte se pokreću redom, `scripts/01_...py` do `scripts/07_...py`, svaka predstavlja jedan korak (priprema korpusa, generisanje test skupa, tri pristupa, evaluacija, analiza grešaka).
Rezultati (tabele, grafici, kvalitativna analiza) su u `results/`.
