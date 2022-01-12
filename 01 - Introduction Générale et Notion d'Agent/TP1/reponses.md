## Question 1
Stratégie :
- Dans la méthode step, si l'agent est un lycanthrope, alors à chaque tour il cherche à attaquer.
- On regarde la liste des agents à portée de 40 : on stocke les agents dans une liste, on fait bien attention de stocker l'id de ces voisins car il ser utilisé pour les retrouer dans la liste des agents du modèle.
- On en choisi un au hasard si cette liste de voisins à portée est non vide.
- Une fois la cible choisie, on va chercher l'instance de cet agent dans le modèle en utilisant son id unique, puis on modifie l'attribut de cet agent.

C'est compatible avec la notion d'agent, en particulier :
- les agents peuvent interragir entre eux (le lycanthrope agit sur sa victime en modifiant ses attributs).
- les agents peuvent évoluer (attribut interne de l'agent mordu qui devient lycanthrope).
- les agents sont compétitifs (intérêts personnels, mordre les autres pour les lycanthropes).

## Question 2

## Question 3

## Question 4

## Question 5

## Question 6

## Question 7

## Question bonus

