i_believe(0).
anis(0).
blardone(0).
!start.

+!start: i_believe(X) <-
    Y = X +5;
    .print(Y).
