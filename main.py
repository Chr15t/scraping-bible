import requests
from bs4 import BeautifulSoup
import pandas as pd
import uvicorn
import os
from urllib.parse import unquote
from tqdm import tqdm
import wget
import threading


from fastapi import FastAPI

app = FastAPI()

url_liben = "https://libgen.is/search.php?req="

plus_url = "lg_topic=libgen&open=0&view=simple&res=25&phrase=1&column=def"


base_url = "http://library.lol/"

list_downloaded_library = []

list_download_error = []




@app.get("/")
def read_root():
    return {"Hello": "World"}
# Liste des pages à scraper

def start_scraper():
  print("\n----------------------------------------------------------------")
  # print("Starting scraper.")
  df_fr = pd.read_csv('output_all_fr.csv', header=None)
  df_header = df_fr
  for index, row in df_header.iterrows():
    print(f"-----> {row[0]}")
    url_to_download = f"{url_liben}{row[0]}&{plus_url}"
    response = requests.get(url_to_download)
    if response.status_code == 200:
      # Parser le contenu de la page avec Beautiful Soup
      soup = BeautifulSoup(response.content, 'html.parser')
      # Trouver tous les tableaux sur la page
      tables = soup.find_all('table')
      tables_focus = tables[2]
      all_tr = tables_focus.find_all('tr')
      # print(f"Nbr of elem => {len(all_tr)-1}")
      if len(all_tr) == 1:
        print(f"############No match found for {row}")
        list_download_error.append({
                    'title': row[0],
                    'links': "NONE",
                    'size': "NONE",
                    'language': "NONE",
                })
        continue
      iteration = 0
      nbr_downloaded = 0
      
      for row_tr in all_tr:
        if iteration > 0:
          tds = row_tr.find_all('td')
          
          # print(f"{row_tr.text}")
          links = tds[2]
          taille = tds[7]
          lang = tds[6]
          # print(f"elem at 3 elements => {links}")
          a_tag = links.find('a')
          if a_tag and lang.text == 'English' or a_tag and lang.text == 'French':
            # Extraire l'URL du lien contenu dans l'attribut 'href' de <a>
            link_downloading = f"{base_url}{a_tag.get('href')}".replace("book/index.php?md5=", "main/")

            
            response_download = requests.get(link_downloading)
            soup_downloaded = BeautifulSoup(response_download.content, 'html.parser')
            element_to_download = soup_downloaded.find(id='download')
            if element_to_download:
              # Extraire le lien du fichier à télécharger
              # all_ul = element_to_download.find_all('ul')
              # all_li = element_to_download.find_all('li')



              all_h2 = element_to_download.find_all('h2')
              first_link = all_h2[0].find('a')
              link_library_to_download = first_link.get('href')
              try:
                filename = unquote(link_library_to_download.split('/')[-1]) 
                save_path = f"french/{filename}"
                if os.path.exists(save_path):
                    continue
                # Download file using wget
                wget.download(link_library_to_download, out=save_path)
                # with requests.get(link_library_to_download, stream=True) as response_download:
                #   response_download.raise_for_status()
                #   total_size = int(response_download.headers.get('content-length', 0))

                #   with open(save_path, 'wb') as file_down:
                #       for chunk in tqdm(response_download.iter_content(chunk_size=8192), total=total_size, unit='B', unit_scale=True):
                #           if chunk:
                #               file_down.write(chunk)
                print(f"-Downloaded \"{links.text}\"\t-laguage=\"{lang.text}\" \t-taille: \"{taille.text}\"\t-link: \"{link_library_to_download}\"")
                list_downloaded_library.append({
                      'title': row[0],
                      'links': link_library_to_download,
                      'size': taille.text,
                      'language': lang.text,
                  })
                nbr_downloaded = nbr_downloaded + 1
              except Exception as e:
                print(f"error {e}")
                print(f"Error downloading {link_library_to_download}")
                list_download_error.append({
                    'title': row[0],
                    'links': link_library_to_download,
                    'size': taille.text,
                    'language': lang.text,
                })


            

        iteration = iteration + 1
      print(f"downloaded {nbr_downloaded}")
  df_downloaded = pd.DataFrame(list_downloaded_library)

  df_downloaded_error = pd.DataFrame(list_download_error)


  excel_filename = 'french_library_data.xlsx'
  df_downloaded.to_excel(excel_filename, index=False)

  df_downloaded_error.to_csv('french_error_library.csv')

        
  print("----------------------------------------------------------------\n")

start_scraper()


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=False)
