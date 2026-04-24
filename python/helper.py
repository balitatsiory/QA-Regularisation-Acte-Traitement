import os
import re
import psycopg2
from psycopg2.extras import RealDictCursor
import config as cfg
from psycopg2.extras import execute_values
from datetime import date, datetime

class Traitement:

   def __init__(self):
        self.line_files_FAHATERAHANA=[]
        self.line_files_SORATRA_ANTSISINY = []
        self.path_dossier_affaire = ""
        self.mentions = []
        
   def getManquant(self,acte_traitement):
      fichiersFAHATERAHANA = []
      manquants = []
      i=0
      
      # chemin = "../test-data/FAHATERAHANA.TXT"
      chemin = self.path_dossier_affaire.replace('//', '/') + "/depot/FAHATERAHANA.TXT"

      
      if not os.path.exists(chemin):
        raise FileNotFoundError(f"Fichier introuvable : {os.path.abspath(chemin)}")
      
      with open(chemin, "r",encoding="utf-8") as file:
         self.line_files_FAHATERAHANA=file.readlines()
         for line in self.line_files_FAHATERAHANA:   
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
                  manquants.append({"nom_image":fichier_image[0] ,"index_fichier": i})
            i+=1
      print(f"fichiersFAHATERAHANA :{len(fichiersFAHATERAHANA)}")
      print(f"manquants :{len(manquants)}")
      return manquants

   def getMention(self):
      fichiersMentions = []
      i=0
      
      # chemin = "../test-data/SORATRA_ANTSISINY.TXT"
      chemin = self.path_dossier_affaire.replace('//', '/') + "/depot/SORATRA_ANTSISINY.TXT"

      if not os.path.exists(chemin):
         raise FileNotFoundError(f"Fichier introuvable : {os.path.abspath(chemin)}")

      with open(chemin, "r", encoding="utf-8") as file:
         self.line_files_SORATRA_ANTSISINY = file.readlines()
         for line in self.line_files_SORATRA_ANTSISINY:
            ligne=line.strip()
            m = re.findall(r'\b[\w\-]+\.tif\b', ligne)
            if m == [] or m == None:
               i+=1
               continue
            fichiersMentions.append({"nom_image":m[0], "index_fichier": i})
            i+=1
      return fichiersMentions
   
   def traitementIdAffaire(self,idaffaire):
      with cfg.get_db() as conn:
         try:
               conn.autocommit = False
               with conn.cursor() as cur:

                  cur.execute(f"SELECT pathdossier FROM affaire WHERE idaffaire = %s", (idaffaire,))
                  row = cur.fetchone()
                  self.path_dossier_affaire = row["pathdossier"] if row else None
                  
                  cur.execute("SELECT datasource FROM acte_traitement WHERE idaffaire = %s", (idaffaire,))
                  acte_traitements = cur.fetchall()
                  acte_traitements_tab = []
                  for i in acte_traitements:
                     val = i["datasource"]
                     if val is not None:
                        found_files = re.findall(r'\b[\w\-]+\.tif\b', val)
                        acte_traitements_tab.extend(found_files)
                  manquants = self.getManquant(acte_traitements_tab)
                  self.mentions = self.getMention()
                  values=self.insertActes(cur,manquants,idaffaire)
                  
                  conn.commit()  # Annule les changements pour éviter de modifier la base de données pendant les tests
                  
                  return values
         except Exception as e:
            print('An exception occurred rollback')
            conn.rollback()  # Annule les changements en cas d'erreur
            raise e
         



   def insertActes(self,cur,manquants,idaffaire):
      values = []
      for manquant in manquants:
         execute_values(cur, """INSERT INTO acte(idaffaire, code, idetape, isrejected)
            VALUES %s RETURNING idacte""",
            [(idaffaire, 'NA', 2, False)]
         )
         rows = cur.fetchall()
         idacte = rows[0]['idacte']
         idactetraitement1=self.funct_insertActeTraitement(cur,manquant["nom_image"],manquant["index_fichier"],idaffaire, None,idacte,1)
         idactetraitement2=self.funct_insertActeTraitement(cur,manquant["nom_image"],manquant["index_fichier"],idaffaire, idactetraitement1,idacte,2)
         mention=self.searchMentions(manquant["nom_image"])
         idmention_datasource_v2 = None
         if mention != None:
            idmention_datasource_v2=self.insertMention(cur,idactetraitement1,idactetraitement2,idaffaire,mention)
         values.append({"idacte":idacte ,"idactetraitement1":idactetraitement1,
                        "idactetraitement2":idactetraitement2,
                        "idmention_datasource_v2":idmention_datasource_v2 ,
                        "nom_tif":manquant["nom_image"]
                        } ) 
      return values
         
   def funct_insertActeTraitement(self,cur, nom_image,index_fichier,idaffaire,idActeTraitement1, idacte,idetape_v2):
      values = self.generateValuesInsertActeTraitement(idacte,idActeTraitement1,idetape_v2,idaffaire,nom_image,index_fichier,self.path_dossier_affaire)
      execute_values(cur,"""
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
      """,values)
      rows_idacte_traitementidetape_v2 = cur.fetchall()
      return rows_idacte_traitementidetape_v2[0]["idacte_traitement"]

   def generateValuesInsertActeTraitement(self,idacte,idActeTraitement1,idetape_v2,idaffaire,nom_tif,index_fichier,path_dossier_affaire):
      row = self.get_values_row_by_index(index_fichier,self.line_files_FAHATERAHANA)
      # print("row:",row)
      rowsplit=row.split(";")
      imagesplit=nom_tif.split("_")
      return [(
            idacte, # idacte
            idActeTraitement1, # idacte_source
            str(idetape_v2), # idetape_v2
            "1", # idemploye_traite
            None, # idemploye_encours
            2, # id_status
            str(idaffaire), # idaffaire
            row, # datasource
            None, # debut_traitement
            datetime.now(), # fin_traitement
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
            # nom_tif, # nom_tif
            False, # exported
            1, # version_acte
            1, # status_acte
            "Ajout manquant", # commentaire
            nom_tif, # image_filename
            imagesplit[0], # region
            imagesplit[1], # district
            imagesplit[2], # commune
            imagesplit[3] if str(rowsplit[0]) == "" else str(rowsplit[0]), # annee
            imagesplit[4], # tome
            imagesplit[5], # registre
            self.extract_numero_acte_by_nomtif(nom_tif) if len(str(rowsplit[1])) == 0 or rowsplit[1] == None else str(rowsplit[1]), # numero_acte
            "AUTRES" if len(str(rowsplit[2])) == 0 or rowsplit[2] == None else str(rowsplit[2]), # sous_type_acte
            None  # livraison 
      )]

   def searchMentions(self, nom_image_manquant):
      for mention in self.mentions:
         if mention["nom_image"] == nom_image_manquant:
            return mention
      return None
   
   def insertMention(self, cur, idactetraitement1, idactetraitement2, idaffaire,mention):
      row = self.get_values_row_by_index(mention["index_fichier"],self.line_files_SORATRA_ANTSISINY)
      values = [
         (idactetraitement1,row,False,"Ajout manquant",1,idaffaire,True),
         (idactetraitement2,row,False,"Ajout manquant",1,idaffaire,True),
      ]
      execute_values(
      cur,
      """
      INSERT INTO mention_datasource_v2(
         idacte_datasource,datasource,isrejected,num_mention,idetape,idaffaire,auto_insert
      )
      VALUES %s
      RETURNING idmention_datasource
      """,
      values
   )
      idmention_datasource_v2 = cur.fetchall()
      return idmention_datasource_v2
   
   def extract_numero_acte_by_nomtif(self,nomtif: str) -> str:
    # On cherche la séquence d'alphanumériques avant le dernier tiret suivi de chiffres
    match = re.search(r'_([0-9A-Za-z]+)-\d+\.tif$', nomtif)
    if match:
        value = match.group(1)
        return value
        # if value.isdigit():
        #     return str(int(value))  # supprime les zéros initiaux
        # else:
        #     return re.sub(r'^0+', '', value)  # supprime les zéros initiaux si alphanumérique
    return None

   def get_values_row_by_index(self,index, table):
      # On vérifie si l'index existe pour éviter un crash
      if index < len(table):
         return table[index].strip() # .strip() enlève les retours à la ligne (\n)
      else:
         raise ValueError("Index hors limites")