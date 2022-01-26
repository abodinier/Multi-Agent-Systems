# Conseils :

## Si on a une erreur 48 : port déjà utilisé :
* Il faut trouver le port en question qu'on veut libérer : `lsof | grep TCP` et là o trouve facilement le PID puisque l'utilisateur est python.
* On tue le process avec `kill <PID>`