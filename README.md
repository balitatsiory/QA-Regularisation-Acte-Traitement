# QA-Regularisation-Acte-Traitement

select * from (select acte_traitement.idaffaire, count(*) as countt, max(nbacte) as nbacte from acte_traitement
join affaire on acte_traitement.idaffaire = affaire.idaffaire where idetape_v2 ='1' 
group by acte_traitement.idaffaire) as t1 where t1.countt != t1.nbacte