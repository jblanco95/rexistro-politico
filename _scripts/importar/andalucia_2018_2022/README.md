# Parlamento de Andalucía 2018 e 2022

Importación das candidaturas, resultados e electos desde o BOJA:

- 2018: candidaturas proclamadas (BOJA núm. 214, 06/11/2018) e resultados e electos (BOJA núm. 248, 26/12/2018).
- 2022: candidaturas proclamadas (BOJA extraordinario núm. 19, 24/05/2022) e resultados e electos (BOJA núm. 132, 12/07/2022).

Pasos:

1. Pasar cada PDF a texto con `pdftotext -layout` e deixar os `.txt` neste cartafol cos nomes que figuran en `FILES` (`build_and.py`).
2. `python3 integrate.py SRC_DIR DST_DIR`: le `data.json` + partes de `SRC_DIR`, engade os rexistros `C` e as táboas `ar` e escribe o resultado en `DST_DIR`.

Comprobacións que fai: a suma dos votos de cada provincia coincide cos votos a candidaturas, os escanos suman os da provincia, as listas con votos coinciden coas proclamadas e os electos coinciden co BOJA. Os casos especiais (renuncias antes da proclamación, erratas de nome e nomes escritos de forma distinta en 2018 e 2022) están en `integrate.py` (`FIX`, `RENUN`, `ELX`, `NAMEFIX`).
