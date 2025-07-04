[Click to navigate back to README](../README.md)

# Project Demo
Small-scale project carried out at home, with home as proxy for an office building. 

![Alt text](../pictures/floorplan(1).png)

### Setup:

1. Break-beam IR Sensors + ESP32 were installed at each doorway of each room in the home, which would log occupancy data throughout the day and save it to ESP32 internal memory. 
2. At the end of 24 hrs, ESP32 would connect to the cloud-hosted IoT database and upload each room's CSV to the database.
3. Database compiles all CSV files into full CSV of "employee" movement for the entire day.
4. Full CSV uploaded to EnergyScout Simulation Software

## Demo Video

[![Watch the demo](https://img.youtube.com/vi/g6c9F1xL3G0/0.jpg)](https://www.youtube.com/watch?v=g6c9F1xL3G0)

[Watch the demo on YouTube](https://www.youtube.com/watch?v=g6c9F1xL3G0)

