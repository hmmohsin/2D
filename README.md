# 2D Online standalone code
## Components
2D Online has 3 components: i) Contoller, ii) Agent, and iii) Application Interface. 
### - Controller

Controller is the key components that receives flow size information and per class load information from the agents, running on 
the end hosts, to compute new per class thresholds and class rates. These class rates and thresholds forms a 2D class policy that
is dispatched to the agents.


**Controller Architectire**

Controller is composed of two key components: i) Measurements and Enforcement Module (ME), ii) Compute Engine (CE). The ME module
is responsible for collecting flow size and class load information from the *agents*. It is also responsible for dispatching
the scheduling policy to the *agents*. The CE module performs the required computation to craft new scheduling policy. For that, it 
runs the *Threshold Computation* and *Rate Computation* algorithms on the data provided to it by the controller application running 
atop.



### - Agent

2D agents are data relaying points running on the end hosts and on network nodes. For now, the agents only work on end hosts. Agents
collect flow size information, and per class load information from the applications running on end hosts and relay that information
to the controller.

Agents are also responsible for collecting new policy information from the controller and enforce that policy to the end hosts. Agent
also passes per class threshold information to the user application for class queuing.

### - Controller Application
