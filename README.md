# RocoCup_Soccer_P6
This project was created as a bachelors project at Aalborg University. Alongside the program a paper was created and can found in this project.
The project set out to showcase real time strategy generation using UPPAAL Stratego for a highly dynamic environment like robocup.

# Setup

The system should work out of the box as long as all dependencies are installed and the system runs a compatible Linux System (Ubuntu 18.04).
- Find robocup files here https://github.com/rcsoccersim

The program opens the robocup server as a command line program.
It is therefor important, that the robocup server and monitor are installed as command line programs.
The robocup files should include a script for doing this in Linux.

Please note, that using many strategies with full teams is fairly resource intensive.
We have during tested experienced issues with CPU's with less than 8 threads.
We assume this to be an issue with scheduling delays and timing.

# Running the program

The default setup is not using any Uppaal Strategies. It contains 2 teams of 11 players each.

Strategies and other constants can be configured in the configurations.py files.

Number of players and run mode can be configured in the constants in the main.py file.

There are two preconfigured run configurations.
- Run with Tests - Runs all tests and then main
- Run without Tests - Simply runs main program regardless of test results

# Specifications we used for testing
The system is tested to work with Linux 18.04 running on Intel x86-64bit architecture. The Uppaal files are compiled for Linux, but the rest of the program should function on Mac and Windows as well, as long as the system has robocup installed.

Versions used:
- OS: Ubuntu 18.04
- Soccer server: 16.0
- Soccer monitor: 16.0
- Uppaal Stratego: 4.1.20-6
- Python version 3.7

Specifications of primary test system:
- Core-i7 9750H - 2.6Ghz to 4.5Ghz
- 8GB 2666mhz ram
- NVMe SSD Storage
- Amd Radeon Pro 5500m 8GB

# Contributors
Michele Albano (Supervisor) - mialb@cs.aau.dk

Philip Irming Holler - philipholler94@gmail.com

Hannah Marie Krøldrup Lockey - hannah97@live.dk

Magnus Kirkegaard Jensen - magnje17@student.aau.dk

# Other resources
- robocup: https://www.robocup.org
- Robocup resources: https://github.com/rcsoccersim
- Uppaal: http://www.uppaal.org 

# License
MIT License

Copyright (c) 2020 Aalborg University

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
