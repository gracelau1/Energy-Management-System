![alt_text](../pictures/ProblemStatement.png)

# Barrier to adoption
The energy auditing service offered by established EMS companies is **expensive** (as requires installation of EMS to calculate energy savings), hence there is no cheap way to obtain cost savings that EMS would offset installation cost (eg. upfront hardware cost, extra electricity cost, maintenance cost), increasing the barrier to implementing EMS.

# Price Comparison

To get a energy savings quantification, EnergyScout advisory tool for EMS could be deployed for **<1% the cost** of a normal energy audit offered by EMS companies.

| **Feature** | **Current EMS vendors** | **EnergyScout** |
| ----------- | ----------- |--|
| Hardware Cost (Per Room) | $150–$1,000 (due to full EMS installation smart relays, sensors, BMS integration) | About $15–20 per room (1ESP32s + 2IRs per room for occupancy data collection, 1 smart meter on main power line to measure total electricity building is drawing for baseline energy usage |
| Install Time | 2 hours per room + certified technician | 15–30 mins per room |
| Time taken for Energy audit completion | Energy savings quantification can **only be calculated post-install of full EMS** (Energy Savings = ((Baseline Energy Use – Post-EMS Energy Use) / Baseline Energy Use)) | Energy savings quantification **completed in a month** or less as it **does not involve installating full EMS systems** - it relies on occupancy data only |
| System Intrusion | Requires **full installation of EMS** (actuators, gateways, servers, controllers, sensors) into light/HVAC, **disruption to operations** and **changing of physical electrical infrastructure of the building** | **No disruption** to operations as **no changing** of physical electrical infrastructure |
| Scalability to 10+ Rooms | **Harder to scale** as high cost and complexity per room | **More lightweight for scaling** as 1 ESP32s + 2IRs per room |

