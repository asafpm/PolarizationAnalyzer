This repository contains the code for a polarization analyzer.

Files:

- PolarisationAnalyser.py
Main application file

- wireframe.py
Required by PolarisationAnalyser.py

- firmware/simulator
Contains an arduino sketch that simulates reading the photodiode data and sends it to the computer via USB. This sketch is used for debugging purposes.

- firmware/real_firmware
This is the firmware that should be installed in an arduino to actually use it as a polarization analyzer.

- samples/*
Random files used for learning during development.
