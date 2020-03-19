# Phone Animation

Phone animation is a set of python files which can be used to read data from "Sensorstream IMU + GPS" https://play.google.com/store/apps/details?id=de.lorenz_fenster.sensorstreamgps&hl=en_US . It reads in data and renders a 3D model of the phone's orientation.

## Usage

Download "Sensorstream IMU + GPS" from google play.
Type in your computer's \bm{local} ip address (can be found with 'ipconfig') into the Target IP Adress
Keep the Target Port at 5555
Select UDP Stream
Ensure the sensors selected are "Accelerometer", "Gyroscope", "Magnetic Field" and "Orientation"

Run run.py in the terminal
