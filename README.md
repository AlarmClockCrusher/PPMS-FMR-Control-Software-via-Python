# PPMS-FMR-Control-Software-via-Python
This a python implementation of controlling software that performs ferromagnetic resonance in Quantum Design (QD) Physical Property Measurement System (PPMS)

# Run PPMS_FMR.py to start the control software
The sample should be mounted on a coplanar waveguide (CPW) or stripline and installed on a **PPMS FMR probe (designed by QD)**. Electronics should be connected via GPIB-USB converter to the computer this program runs on, while the PPMS should be connected to the same computer via LAN. **Configure your computer so it can ping the PPMS computer.**

The electronics include an AC current source (Keithley 6221 by default), microwave source (Agilent N5183 by default) and a lock-in amplifier (Stanford SR830 by default). The AC current source drives a small modulating magnetic field provided by coils around the mounted sample, and the lock-in amplifier catches the change of microwave absorption (dependent on magnetic field). The resultant spectrum is a field derivative of the real peak lineshape, as shown below:

![LSC604_2K_8p0GHz_0dBm_20p0mA](https://user-images.githubusercontent.com/61217720/205196558-a4cf971c-d596-4e2f-ba1f-da2cfc237303.png)

The blue and red data points are from the two quadratures of the detected voltage.

### Packages needed: numpy, matplotlib, pymeasure, pandas, pyvisa, scipy, wxPython, pythonnet.
### The pythonnet package will likely require pythonnet 2.x version, instead of 3.x.
These packages can be readily installed via "pip install xxx" method.

## Using this software
Enter folder name and path in "Sample ID" and "Folder" text boxes in order to specify where the data will be saved. The .csv date file names will start with the sample id and also contain information of the measurement, e.g, LSC604_2K_8p0GHz_0dBm_20p0mA.csv means the measurement is done at 2K temperature, with driving microwave at 8GHz frequency, 0dBm power and 20mA modulation current.

**The PPMS and electronics must be connected before operation.** Click "Connect GPIB Conn" button on the left to connect. The addresses of the three electronics can be edited. Successful connection will change the status tags below them.

![PPMS_FMR_ScreenShot](https://user-images.githubusercontent.com/61217720/205196599-6e787998-8c68-48dc-afbb-4355e726d6b4.png)

Upon successful connection, labels on the right will start updating real-time status, such as temperature/field/lock-in reading. You can use text boxes and buttons to set key parameters of the PPMS, electronics.

# This program allows series of measurements at different frequencies and temperatures.
"Freq(GHz):Field(G) pairs(Seperate with ',')" text box reads in pairs of driving microwave frequency and resonance field positions. For example, "10: 2400, 20: 6000" will do an FMR scan centered at 2400G with 10GHz microwave and another FMR scan centered at 6000G with 20GHz microwave".

"Initial linewidth(G)" text box is your estimate of the linewidth at 2400G and 10GHz; "Final linewidth(G)" text box is your estimate of the linewidth at 6000G and 20GHz. Scan ranges will be 7x the estimated linewidth. "10: 2400, 15: 4500, 20: 6000", 10G Initial linewidth and 20G Final linewidth will yield scans of 2365-2435G at 10GHz, 4447.5-4552.5G at 15GHz (assuming linear frequency dependence of linewidth) and 5930-6070G at 20GHz.

"Temps(K):Shift(G) (Seperate with ',')" text box reads in pairs of measurement temperature and field shift. For example, "150: 0, 300: 15" will do two series of FMR scans. The first series will be done at 150K, with the scans being "10GHz: 2400G, 20GHz: 6000G". The second series will then be done at 300K, with scans being "10GHz: 2400G+15G, 20GHz: 6000G+15G".

# Click "Start" button to begin measurement.
Once cliked, it will turn in "Abort", so you can click again if you would like to stop all ongoing and upcoming scans ( current ongoing scan will still be saved). Click the "Skip remaining Fields" in order to stop the current scan early ( all following scans will continue).

6221 Setup.txt and CommandsforInstruments.docx are manuals for how to set up AC current source 6221 and common GPIB commands for the instruments.

QDInstrument.dll holds all necessary functions to interface with the PPMS. This file can be downloaded from the Quantum Design official website. **Make sure its version is no older than 2022's versions, as older dll file's syntax is "QDInstrumentBase.QDInstrumentType.PPMS", instead of "QDInstrumentBase.QDInstrumentType.DynaCool".**

## Make sure QDInstrument.dll file is unblocked in the Properties ( right click to open).
