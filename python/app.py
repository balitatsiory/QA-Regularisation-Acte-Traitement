import sys
import json
import re
import config as cfg

import psycopg2
from psycopg2.extras import RealDictCursor

from flask import Flask, jsonify, request

app = Flask(__name__)

CHEMIN_PREPARATION = "/opt/....."

def get_db():
    # 1. Établir la connexion
    conn = psycopg2.connect(**cfg.DB_CONFIG, cursor_factory=RealDictCursor)
   
    # 2. Configurer l'encodage sur l'objet connexion
    conn.set_client_encoding('UTF8')
   
    # 3. Retourner la connexion
    return conn

# lire JSON depuis stdin
# input_data = json.load(sys.stdin)

# acte_traitement = input_data["acte_traitement"]

def getMention():
   fichiersMentions = []
   i=0
   # with open(CHEMIN_PREPARATION + "/SORATRA_ANTSISINY.TXT", "r",encoding="utf-8") as file:
   with open("../test-data/SORATRA_ANTSISINY.TXT", "r",encoding="utf-8") as file:
      for line in file:
         ligne=line.strip()
         m = re.findall(r'\b[\w\-]+\.tif\b', ligne)
         if m == [] or m == None:
            i+=1
            continue
         fichiersMentions.append([m[0], i])
         i+=1
   return fichiersMentions
# print(len(acte_traitement))


def getManquant(acte_traitement):
   fichiersFAHATERAHANA = []
   manquants = []
   i=0
   with open("../test-data/FAHATERAHANA.TXT", "r",encoding="utf-8") as file:
   # with open(CHEMIN_PREPARATION + "/FAHATERAHANA.TXT", "r",encoding="utf-8") as file:
      for line in file:
         ligne=line.strip()
         fichier_image=re.findall(r'\b[\w\-]+\.tif\b', ligne)
         fichier_image=list(set(fichier_image))
         # print(fichier_image)
         if fichier_image == None or fichier_image == []:
            i+=1
            continue
         if fichier_image not in fichiersFAHATERAHANA:
            fichiersFAHATERAHANA.extend(fichier_image)
            if fichier_image[0] not in acte_traitement:
               manquants.append([fichier_image[0] , i])
         i+=1
   print(f"fichiersFAHATERAHANA :{len(fichiersFAHATERAHANA)}")
   print(f"manquants :{len(manquants)}")
   return manquants


# # print(len(manquants))

def returnMentions(manquants):
   insertMentions = []
   insertActeTraitement = []
   for m in manquants:
      for item in getMention():
         if m[0] == item[0]:
            insertMentions.append(item)
      insertActeTraitement.append(m)
   return {
      "insertMentions": insertMentions,
      "insertActeTraitement": insertActeTraitement
   }
# print(len(insertMentions))


# # print(len(insertActeTraitement))
# # insertActeTraitement

# result = {
#    "insertMentions": insertMentions,
#    "insertActeTraitement": insertActeTraitement
# }

# # renvoyer JSON
# print(json.dumps(result))

@app.route('/api/greet', methods=['GET'])
def greet():
   print("Received request for /api/greet")
   return jsonify({"message": "Hello from Flask API!"})


@app.route('/api', methods=['POST'])
def read_item():
   idaffaire = request.form['idaffaire']
   print(f"Received idaffaire: {idaffaire}")
   with get_db() as conn:
      with conn.cursor() as cur:
         cur.execute(f"select datasource from acte_traitement where idaffaire = '{idaffaire}'")
         acte_traitements = cur.fetchall()
         acte_traitements_tab = []
         for i in acte_traitements:
            # print(f"Processing datasource: {i}")
            val = i["datasource"]
            if val is not None:
               found_files = re.findall(r'\b[\w\-]+\.tif\b', val)
               acte_traitements_tab.extend(found_files)
         manquants = getManquant(acte_traitements_tab)
         res=returnMentions(manquants)
         
         # TRANSACTION INSERT MENTION & ACTE TRAITEMENT idetape_v2 1 & 2 & 3
         #close
         
   return {"res": res}

if __name__ == '__main__':
   print("Starting Flask API on port 5000...")
   app.run(port=5000)