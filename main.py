from database import setup_database, salva_dati
from scraper import ottieni_link_alimenti, analizza_pagina_alimento
import time

# INSERISCI QUI L'URL DELLA PAGINA CHE CONTIENE L'ELENCO
URL_ELENCO = "https://www.alimentinutrizione.it/tabelle-nutrizionali/ricerca-per-ordine-alfabetico"

def main():
    # 1. Inizializza DB
    print("Inizializzazione database...")
    conn = setup_database()

    # 2. Ottieni tutti gli URL con Selenium
    links = ottieni_link_alimenti(URL_ELENCO)

    if not links:
        print("Nessun link trovato. Controlla il selettore CSS o l'URL.")
        return

    # 3. Itera sui link ed estrai/salva i dati con BeautifulSoup
    print("\nInizio scraping delle singole pagine...\n" + "-"*40)

    for indice, url_alimento in enumerate(links, start=1):
        try:
            print(f"[{indice}/{len(links)}] Analisi in corso: {url_alimento}")

            anagrafica, valori = analizza_pagina_alimento(url_alimento)

            if anagrafica['codice_alimento']:
                salva_dati(conn, anagrafica, valori)
                print(f"   --> Salvato: {anagrafica['nome']} ({len(valori)} nutrienti)")
            else:
                print("   --> SKIPPATO: Nessun codice alimento trovato.")

        except Exception as e:
            print(f"   --> ERRORE elaborando {url_alimento}: {e}")

        # Una piccola pausa per non bombardare il server di richieste (buona pratica)
        time.sleep(0.5)

    conn.close()
    print("\nOperazione completata con successo! Dati salvati in 'nutrizione.db'")

if __name__ == "__main__":
    main()