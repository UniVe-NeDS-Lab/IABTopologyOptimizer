# IAB Topology Optimizer

This repository contains the code for the rApp developed during the [OR²AN²G](https://or2an2g.dais.unive.it/) project to orchestrate Integrated Access and Backhaul (IAB) topologies.
The rApp code itself is in the `rapp` subfolder togheter with a Dockerfile used to build the standalone app.

It's also possible to run the rApp together with [NONRTRIC](https://docs.o-ran-sc.org/projects/o-ran-sc-nonrtric/en/latest/overview.html) by running the docker-compose file available at the root of the project.

The rApp depends on the O1 messages we defined and implemented for OpenAirInterface, available in [this](https://github.com/UniVe-NeDS-Lab/openairinterface5g/tree/o1_reporting) repository.
