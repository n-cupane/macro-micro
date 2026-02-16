import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def ottieni_link_alimenti(url_lista):
    """Usa Selenium per caricare la pagina principale ed estrarre tutti gli href."""
    print(f"Avvio Chrome in background per estrarre i link da: {url_lista}")

    options = webdriver.ChromeOptions()
    options.add_argument('--headless') # Esegue Chrome senza aprire la finestra
    options.add_argument('--log-level=3') # Nasconde i log noiosi di Chrome

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    links = []

    try:
        driver.get(url_lista)
        wait = WebDriverWait(driver, 10)

        # JS Path modificato per prendere tutti gli elementi della lista
        css_selector = "#listTwo > li > div > a"
        elementi = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector)))

        for el in elementi:
            href = el.get_attribute("href")
            if href:
                links.append(href)

    finally:
        driver.quit()

    print(f"Trovati {len(links)} link.")
    return links

def analizza_pagina_alimento(url_alimento):
    """Usa Requests e BeautifulSoup per estrarre i dati dalla singola pagina."""
    response = requests.get(url_alimento)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 1. Estrazione Nome
    titolo_el = soup.find('h1', class_='article-title')
    nome_alimento = titolo_el.text.strip() if titolo_el else "Sconosciuto"

    # Strutture dati da ritornare
    anagrafica = {
        'codice_alimento': '', 'nome': nome_alimento, 'categoria': '',
        'nome_scientifico': '', 'english_name': '', 'parte_edibile': '', 'porzione': ''
    }
    valori = []

    # 2. Estrazione Anagrafica (Tabella in alto)
    tabella_top = soup.find('table', class_='toptable')
    if tabella_top:
        for row in tabella_top.find_all('tr'):
            tds = row.find_all('td')
            if len(tds) == 2:
                chiave = tds[0].text.strip()
                valore = tds[1].text.strip()

                # Mappiamo le chiavi del sito con le chiavi del nostro dizionario
                if chiave == 'Codice Alimento': anagrafica['codice_alimento'] = valore
                elif chiave == 'Categoria': anagrafica['categoria'] = valore
                elif chiave == 'Nome Scientifico': anagrafica['nome_scientifico'] = valore
                elif chiave == 'English Name': anagrafica['english_name'] = valore
                elif chiave == 'Parte Edibile': anagrafica['parte_edibile'] = valore
                elif chiave == 'Porzione': anagrafica['porzione'] = valore

    # Se non c'è un codice alimento, non possiamo salvare i dati nutrizionali
    if not anagrafica['codice_alimento']:
        return anagrafica, valori

    # 3. Estrazione Valori Nutrizionali (Tabella grande in basso)
    tabella_main = soup.find('table', class_='tblmain')
    if tabella_main:
        macrocategoria_corrente = "Generico"

        for row in tabella_main.find('tbody').find_all('tr'):
            classi_str = " ".join(row.get('class', []))

            # Identifica l'intestazione della macrocategoria (es: MACRO NUTRIENTI, VITAMINE)
            if 'title' in classi_str:
                macrocategoria_corrente = row.text.replace("Vedi tutti i campi", "").strip()

            # Identifica le righe con i valori veri e propri
            elif 'corpo' in classi_str:
                tds = row.find_all('td')
                if len(tds) >= 6:
                    valori.append({
                        'macrocategoria': macrocategoria_corrente,
                        'nutriente': tds[0].text.strip(),
                        'unita_misura': tds[1].text.strip(),
                        'valore_100g': tds[2].text.strip().replace('\xa0', ''), # Rimuove spazi vuoti strani
                        'valore_porzione': tds[5].text.strip()
                    })

    return anagrafica, valori