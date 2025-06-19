# 580_Project_Src

This project aims to simulate commute-related challenges of Autistic people and tries to mitigate the effects of these challenges on wealth distribution by employing alternative workplace policies. Inspired by Aguilera et al. [1], this project is based on "Needs-Based Model" originally introduced by Dignum et al. [2]. 


> [!IMPORTANT]  
> Needs-based model implemented here have important amendments that affect the simulation outcomes.
> Please see the report for detailed discussions of the results.


## Guidelines
To run the simulation and obtain the plots given in the study, simply run:
```
python commute_simulation.py
```
There are also some simulation paratemers to be set alternatively.

```
usage: commute_simulation.py [-h] [-rw] [-p POLICY]

options:
  -h, --help            show this help message and exit
  -rw, --randomize-walk
                        Allow agents to walk in randomize path lengths instead of the shortest path.
  -p, --policy POLICY   Choose workplace policy (available options: 'fixed', 'free', 'flex'). If None, run simulations for all available policies. Default: None
```

In default setting, if an agent chooses to "walk", manhattan distance is given to estimate, and the A* shortest path is given to the agent to actualize the action. If the option ``-rw`` is enabled, agent estimates and walks random path lengths. See also ``config.yaml`` to specify available house and workplace coordinates in the simulation. Simulation script assigns random house and workplaces to the agents from the available options provided in the configuration file.

## References
[1] A. Aguilera, N. Montes, G. Curto, C. Sierra, and N. Osman, “Can poverty be reduced by acting on discrimination? an agent-based model for policy making,” in Proceedings of the 23rd International Conference on Autonomous Agents and Multiagent Systems, ser. AAMAS’24. Richland, SC: International Foundation for Autonomous Agents and Multiagent Systems, 2024, p. 22–30

[2] F. Dignum, V. Dignum, P. Davidsson, A. Ghorbani, M. van der Hurk, M. Jensen, C. Kammler, F. Lorig, L. G. Ludescher, A. Melchior et al., “Analysing the combined health, social and economic impacts of the corovanvirus pandemic using agent-based social simulation,” Minds and Machines, vol. 30, pp. 177–194, 2020.