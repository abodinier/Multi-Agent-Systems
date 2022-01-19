prosodyctl start

for i in {0..50};
    do prosodyctl register ship-$i localhost password-ship-$i;
done
for i in {0..50};
    do prosodyctl register planet-$i localhost password-planet-$i;
done