
Database
========

Les données sont stockées dans un fichier sqlite.

Pour des raisons de simplicité, ce qui est directement récupéré brut
du web pourra être stocké dans la table "apparts", dont l'identifiant
est une clé primaire.

Les autres données, comme les calculs d'€/m², ou le téléphone décodé,
pourront être stocké, mais ailleurs, par exemple dans une table
séparée.
Cela est nécessaire pour éviter de changer la table "apparts" à chaque
fois qu'on veut rajouter des données.
