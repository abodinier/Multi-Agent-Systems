anis(0).
bardane(0).
resources_available.

!start.

+!start <-
    // On initialise
    +iterations(0); // On initialise le nombre d'itérations
    .initialisation_beliefs; // On initialise les croyances des agents pour chaque région
    !get_resources.

//////////////////////////////////////////////////////////////////////////////////////////
// Phase préliminaire : Implémentation du plan d'envoi des messages
+!new_values_r(I, MEAN_ANIS, MEAN_BARDANE, NUMBER_OF_VISITS) <-
    .print("Region", I, " has been visited", NUMBER_OF_VISITS, "times : Mean of anis = ", MEAN_ANIS, ", Mean of bardane:", MEAN_BARDANE).
//////////////////////////////////////////////////////////////////////////////////////////

+!get_resources: resources_available <-

    ?iterations(ITERATION);
   
//////////////////////////////////////////////////////////////////////////////////////////
    // Phase 1 : la récolte
    // On récupère la quantité des ressources
    ?anis(CURRENT_ANIS);
    ?bardane(CURRENT_BARDANE);
    
    // On regarde l'autre intention afin de déterminer la meilleure région
    ?find_best_region(ITERATION, I, MEAN_ANIS, MEAN_BARDANE, NUMBER_OF_VISITS);
    .action_region(I);
    
    // On récolte les ressources
    ?anis(NEW_ANIS);
    ?bardane(NEW_BARDANE);
//////////////////////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////////////////////    
    // Phase 2 : mise à jour de la croyance
    // Si les valeurs sont nulles, on met la valeur moyenne de la ressource à 0. Sinon, on effectue la moyenne entre la croyance précédente et ce qu'on vient de récolter
    
    if (CURRENT_ANIS == NEW_ANIS){ // Pour l'anis
        NEW_MEAN_ANIS = 0;       
        } 
    else {
        NEW_MEAN_ANIS = (MEAN_ANIS + NEW_ANIS - CURRENT_ANIS)/2.0 ; 
        };
    
    if (CURRENT_BARDANE == NEW_BARDANE){ // Pour la bardane
        NEW_MEAN_BARDANE = 0;     
        }
    else {
        NEW_MEAN_BARDANE = (MEAN_BARDANE + NEW_BARDANE - CURRENT_BARDANE)/2.0 ;
        };
    
    // On effectue les mises à jour des croyances des agents
    -values_r(I, _, _, _);
    +values_r(I, NEW_MEAN_ANIS, NEW_MEAN_BARDANE, NUMBER_OF_VISITS+1);

    // Si on a visité la région une ou plusieurs dizaines de fois, alors on diffuse la nouvelle croyance à tous les autres agents
    if ((NUMBER_OF_VISITS+1) mod 10 == 0){
        .broadcast(achieve, new_values_r(I, NEW_MEAN_ANIS, NEW_MEAN_BARDANE, NUMBER_OF_VISITS+1));
        };
        
    // On incrémente le nombre d'itérations
    -iterations(_);
    +iterations(ITERATION + 1);

    // On regarde les régions dont les ressources ne sont pas de moyenne nulle et on met à jour l'intention en conséquence
    .count(values_r(_, 0, 0, _), NUMBER_OF_NULL_MEANS);
    if (NUMBER_OF_NULL_MEANS == 10) {
        -resources_available;
    };
    
    if(resources_available) {
        !get_resources;
    }
    else {
        !see_output;
    }.
//////////////////////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////////////////////    
// Implémentation du plan test

+?find_best_region(ITERATION, I, MEAN_ANIS, MEAN_BARDANE, NUMBER_OF_VISITS)<-
    
    // On réinitialise la valeur de la meilleure région trouvée
    -best_ucb(_);
    +best_ucb(0);
    
    // On itère sur les croyances afin de déterminer la meilleure région
    for(values_r(I, MEAN_ANIS, MEAN_BARDANE, NUMBER_OF_VISITS)){
        .min([MEAN_ANIS, MEAN_BARDANE], MINIMUM_RESOURCES);
        .ucb(MINIMUM_RESOURCES, NUMBER_OF_VISITS, ITERATION, CURRENT_UCB);
        
        ?best_ucb(BEST_UCB);
        
        // Si on trouve une région avec un meilleur ucb que la meilleure région que l'on a, alors on met à jour cette meilleure région par celle que l'on vient de trouver
        if (BEST_UCB <= CURRENT_UCB) {
            -best_ucb(_);
            +best_ucb(CURRENT_UCB);
            -current_region(_, _, _, _);
            +current_region(I, MEAN_ANIS, MEAN_BARDANE, NUMBER_OF_VISITS);
            };
        };
    ?current_region(I, MEAN_ANIS, MEAN_BARDANE, NUMBER_OF_VISITS).
//////////////////////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////////////////////
// Implémentation du plan affichant les quantités en anis et bardane récoltés lorsque l'on arrive à épuisement des ressources

+!see_output: not resources_available <- 
    ?anis(CURRENT_ANIS);
    ?bardane(CURRENT_BARDANE);
    ?iterations(ITERATION);
    .print("Anis : ", CURRENT_ANIS, ", Bardane : ", CURRENT_BARDANE, ", Nombre d'iterations atteint : ", ITERATION).
//////////////////////////////////////////////////////////////////////////////////////////
