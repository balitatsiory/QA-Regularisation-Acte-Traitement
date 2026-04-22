from datetime import date
import sys
import json
import re
import config as cfg

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extras import execute_values

from flask import Flask, jsonify, request

app = Flask(__name__)

CHEMIN_PREPARATION = "/opt/....."
line_files_FAHATERAHANA=[]
line_files_SORATRA_ANTSISINY = []

def get_db():
    # 1. Établir la connexion
    conn = psycopg2.connect(**cfg.DB_CONFIG, cursor_factory=RealDictCursor)
   
    # 2. Configurer l'encodage sur l'objet connexion
    conn.set_client_encoding('UTF8')
   
    # 3. Retourner la connexion
    return conn

def getMention():
   fichiersMentions = []
   i=0
   # with open(CHEMIN_PREPARATION + "/SORATRA_ANTSISINY.TXT", "r",encoding="utf-8") as file:
   with open("../test-data/SORATRA_ANTSISINY.TXT", "r",encoding="utf-8") as file:
      line_files_SORATRA_ANTSISINY = file.readlines()
      for line in line_files_SORATRA_ANTSISINY:
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
      line_files_FAHATERAHANA=file.readlines()
      for line in line_files_FAHATERAHANA:
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
               manquants.append({"nomfichier": fichier_image[0], "index_ligne_fahaterahana": i})
         i+=1
   print(f"fichiersFAHATERAHANA :{len(fichiersFAHATERAHANA)}")
   print(f"manquants :{len(manquants)}")
   return manquants


# # print(len(manquants))

def returnidMentionsidActeTraitement(manquants):
   insertMentions = []
   insertActeTraitement = []
   for index,m in enumerate(manquants):
      for item in getMention():
         #Verifier si le nom du fichier mentionné dans SORATRA_ANTSISINY.TXT correspond à un nom de fichier dans FAHATERAHANA.TXT
         if m["nomfichier"] == item[0]:
            #insertMentions.append(item)
            insertMentions.append({"nomfichier": item[0], "index_ligne_soratra": item[1], "index_manquant": index })
      insertActeTraitement.append(m)
   return {
      "insertMentions": insertMentions,
      "insertActeTraitement": insertActeTraitement
   }

def insertTablesValues(conn,cur,list_insertion,idaffaire):
   try:
      path_dossier_affaire = cur.execute(f"select pathdossier from affaire where idaffaire = '{idaffaire}'")
      idActes=insertActes(cur,list_insertion["insertActeTraitement"],idaffaire)
      insertActeTraitement=funct_insertActeTraitement(cur,list_insertion["insertActeTraitement"],idaffaire,idActes,path_dossier_affaire)
      insertMentions(cur,list_insertion["insertMentions"],insertActeTraitement,idaffaire)
      conn.commit()
   except Exception as e:
      conn.rollback()
      print("❌ Erreur :", e)
   finally:
      cur.close()
      conn.close()
      
   #item tableau miasa satry tableau txt no ampidirina anaty table


   
def insertActes(cur,insertActeTraitement,idaffaire):
   # cur.execute("""
   #      INSERT INTO acte(idaffaire,code,idetape,isrejected)
   #      SELECT unnest(%s::text[])
   #      RETURNING id, nom
   #  """, (insertActeTraitement,))
   
   values = [(idaffaire, "NA", "2", False) for a in insertActeTraitement]

   execute_values(
      cur,
      """
      INSERT INTO acte(idaffaire, code, idetape, isrejected)
      VALUES %s
      RETURNING id
      """,
      values
   )
   rows = cur.fetchall()
   print(f"insertActes : {len(rows)} : [{[row['id']+',' for row in rows]}]")
   return rows



def funct_insertActeTraitement(cur,insertActeTraitement,idaffaire,idActes,path_dossier_affaire):
   # idetape_v2 = 1
   values = []
   for i, element in enumerate(insertActeTraitement):
      row = get_values_row_by_index(insertActeTraitement[i][1],line_files_FAHATERAHANA)
      rowsplit=row.split(";")
      imagesplit=row.split("_")
      values.append((
         idActes[i]['id'], # idacte
         None, # idacte_source
         "1", # idetape_v2
         "1", # idemploye_traite
         None, # idemploye_encours
         2, # id_status
         str(idaffaire), # idaffaire
         row, # datasource
         None, # debut_traitement
         date(), # fin_traitement
         1, # numero_duplication
         rowsplit[1], # num_acte
         rowsplit[0], # annee_acte
         True, # auto_insert
         1, # version_actuel
         "NA", # type_acte
         "Recital", # nom_editeur
         "V2", # version_editeur
         path_dossier_affaire, # pathdossier
         str(rowsplit[0]) + ";"*74 + str(';'.join(rowsplit[74:])) , # datasource_source
         element[0], # nom_tif
         False, # exported
         1, # version_acte
         1, # status_acte
         "MONTEST", # commentaire
         element[0], # image_filename
         imagesplit[0], # region
         imagesplit[1], # district
         imagesplit[2], # commune
         str(rowsplit[0]), # annee
         imagesplit[4], # tome
         imagesplit[5], # registre
         str(rowsplit[1]), # numero_acte
         str(rowsplit[2]), # sous_type_acte
         None  # livraison 
      ))
   execute_values(
      cur,
      """
      INSERT INTO acte_traitement(
      idacte
      ,idacte_source
      ,idetape_v2
      ,idemploye_traite
      ,idemploye_encours
      ,id_status
      ,idaffaire
      ,datasource
      ,debut_traitement
      ,fin_traitement
      ,numero_duplication
      ,num_acte
      ,annee_acte
      ,auto_insert
      ,version_actuel
      ,type_acte
      ,nom_editeur
      ,version_editeur
      ,pathdossier
      ,datasource_source
      ,nom_tif
      ,exported
      ,version_acte
      ,status_acte
      ,commentaire
      ,image_filename
      ,region
      ,district
      ,commune
      ,annee
      ,tome
      ,registre
      ,numero_acte
      ,sous_type_acte
      ,livraison)
      VALUES %s
      RETURNING idacte_traitement
      """,
      values
   )
   rows_idacte_traitementidetape_v2_1 = cur.fetchall()
   
   
   
   # idetape_v2 = 2
   values = []
   for i, element in enumerate(insertActeTraitement):
      row = get_values_row_by_index(insertActeTraitement[i][1],line_files_FAHATERAHANA)
      rowsplit=row.split(";")
      imagesplit=row.split("_")
      values.append((
         idActes[i]['id'], # idacte
         rows_idacte_traitementidetape_v2_1[i][0], # idacte_source
         "2", # idetape_v2
         "1", # idemploye_traite
         None, # idemploye_encours
         2, # id_status
         str(idaffaire), # idaffaire
         row, # datasource
         None, # debut_traitement
         date(), # fin_traitement
         1, # numero_duplication
         rowsplit[1], # num_acte
         rowsplit[0], # annee_acte
         True, # auto_insert
         1, # version_actuel
         "NA", # type_acte
         "Recital", # nom_editeur
         "V2", # version_editeur
         path_dossier_affaire, # pathdossier
         str(rowsplit[0]) + ";"*74 + str(';'.join(rowsplit[74:])) , # datasource_source
         element[0], # nom_tif
         False, # exported
         1, # version_acte
         1, # status_acte
         "MONTEST", # commentaire
         element[0], # image_filename
         imagesplit[0], # region
         imagesplit[1], # district
         imagesplit[2], # commune
         str(rowsplit[0]), # annee
         imagesplit[4], # tome
         imagesplit[5], # registre
         str(rowsplit[1]), # numero_acte
         str(rowsplit[2]), # sous_type_acte
         None  # livraison 
      ))
   execute_values(
      cur,
      """
      INSERT INTO acte_traitement(
      idacte
      ,idacte_source
      ,idetape_v2
      ,idemploye_traite
      ,idemploye_encours
      ,id_status
      ,idaffaire
      ,datasource
      ,debut_traitement
      ,fin_traitement
      ,numero_duplication
      ,num_acte
      ,annee_acte
      ,auto_insert
      ,version_actuel
      ,type_acte
      ,nom_editeur
      ,version_editeur
      ,pathdossier
      ,datasource_source
      ,nom_tif
      ,exported
      ,version_acte
      ,status_acte
      ,commentaire
      ,image_filename
      ,region
      ,district
      ,commune
      ,annee
      ,tome
      ,registre
      ,numero_acte
      ,sous_type_acte
      ,livraison)
      VALUES %s
      RETURNING rows_idacte_traitement
      """,
      values
   )
   rows_idacte_traitementidetape_v2_2 = cur.fetchall()
   
   insertActeTraitement=add_idacte_traitement_to_insertActeTraitement_etape12(insertActeTraitement, rows_idacte_traitementidetape_v2_1, rows_idacte_traitementidetape_v2_2)
   
   
   return insertActeTraitement

   
def insertMentions(cur,insertMentions,insertActeTraitement,idaffaire):
   # idetape 1 
   values = []
   for i, element in enumerate(insertMentions):
      row = get_values_row_by_index(insertMentions[i]["index_ligne_soratra"],line_files_SORATRA_ANTSISINY)
      values.append((
      insertActeTraitement[insertMentions[i]["index_manquant"]]["idacte_traitement_etape1"],   #idacte_datasource
      row,   #datasource
      False,   #isrejected
      None,   #num_mention
      1, #idetape
      idaffaire, #idaffaire
      True #auto_insert
      ))

   execute_values(
      cur,
      """
      INSERT INTO mention_datasource_v2(
         idacte_datasource,datasource,isrejected,num_mention,idetape,idaffaire,auto_insert
      )
      VALUES %s
      """,
      values
   )
   
      # idetape 1 
   values = []
   for i, element in enumerate(insertMentions):
      row = get_values_row_by_index(insertMentions[i]["index_ligne_soratra"],line_files_SORATRA_ANTSISINY)
      values.append((
      insertActeTraitement[insertMentions[i]["index_manquant"]]["idacte_traitement_etape2"],   #idacte_datasource
      row,   #datasource
      False,   #isrejected
      None,   #num_mention
      2, #idetape
      idaffaire, #idaffaire
      True #auto_insert
      ))

   execute_values(
      cur,
      """
      INSERT INTO mention_datasource_v2(
         idacte_datasource,datasource,isrejected,num_mention,idetape,idaffaire,auto_insert
      )
      VALUES %s
      """,
      values
   )

   
      # idetape 1 
   values = []
   row = get_values_row_by_index(insertActeTraitement[i][1],line_files_SORATRA_ANTSISINY)
   for i, element in enumerate(insertMentions):
      values.append((
         #idacte_datasource
      row,   #datasource
      False,   #isrejected
      None,   #num_mention
      2, #idetape
      idaffaire, #idaffaire
      True #auto_insert
      ))

   execute_values(
      cur,
      """
      INSERT INTO acte(
         idacte_datasource,datasource,isrejected,num_mention,idetape,idaffaire,auto_insert
      )
      VALUES %s
      RETURNING id
      """,
      values
   )


def get_values_row_by_index(index, table):
    # On vérifie si l'index existe pour éviter un crash
    if index < len(table):
        return table[index].strip() # .strip() enlève les retours à la ligne (\n)
    else:
        raise ValueError("Index hors limites")

def add_idacte_traitement_to_insertActeTraitement_etape12(insertActeTraitement, rows_idacte_traitementidetape_v2_1,rows_idacte_traitementidetape_v2_2):
   for i, element in enumerate(insertActeTraitement):
      element["idacte_traitement_etape1"] = rows_idacte_traitementidetape_v2_1[i][0]
      element["idacte_traitement_etape2"] = rows_idacte_traitementidetape_v2_2[i][0]
   return insertActeTraitement

@app.route('/api', methods=['POST'])
def read_item():
   idaffaire = request.form['idaffaire']
   print(f"Received idaffaire: {idaffaire}")
   with get_db() as conn:
      conn.autocommit = False
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
         list_insertion=returnidMentionsidActeTraitement(manquants)
         # insertTablesValues(conn, cur, list_insertion, idaffaire)
         
         # TRANSACTION INSERT MENTION & ACTE TRAITEMENT idetape_v2 1 & 2 & 3
         #close
         
   return {"res": list_insertion}

@app.route('/api/greet', methods=['GET'])
def greet():
   print("Received request for /api/greet")
   return jsonify({"message": "Hello from Flask API!"})

if __name__ == '__main__':
   print("Starting Flask API on port 5000...")
   app.run(port=5000)