#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Module containing a class to interface with a Quantum Dynamics PPMS DynaCool"""

# requires Python for .NET, can be installed with 'pip install pythonnet'
import platform, clr, subprocess

"""Connect to the ppms in order to control the field and temperature"""
try: clr.AddReference('QDInstrument')
except Exception as e:
	print("Exception found:", e)
	if clr.FindAssembly('QDInstrument') is None: print('Could not find QDInstrument.dll')
	else:
		print('Found QDInstrument.dll at {}'.format(clr.FindAssembly('QDInstrument')))
		print('Try right-clicking the .dll, selecting "Properties", and then clicking "Unblock"')
		# import the C# classes for interfacing with the PPMS
		#The dll file must be unblocked in the dll file's properties
		
# import the C# classes for interfacing with the PPMS
#The dll file must be unblocked in the dll file's properties
"""	The control of PPMS field/temperature is given by the manufacturer Quantum Design. 
	They provide Labview packages to interface with the PPMS, and such packages are also 
	included in QDInstrument.dll in the folder with python codes. Each python code loads the dll
	and REGISTERS it as QuantumDesign library and import it
"""
from QuantumDesign.QDInstrument import *

QDI_PPMS_TYPE = QDInstrumentBase.QDInstrumentType.DynaCool
#QDI_FIELD_APPROACH = QDInstrumentBase.FieldApproach.NoOvershoot
QDI_FIELD_APPROACH = QDInstrumentBase.FieldApproach.Linear
QDI_FIELD_MODE = QDInstrumentBase.FieldMode.Persistent
QDI_FIELD_MODE_driven = QDInstrumentBase.FieldMode.Driven

DEFAULT_PORT = 11000
QDI_FIELD_STATUS = ['MagnetUnknown', 'StablePersistent', 'StableDriven',
					'WarmingSwitch', 'CoolingSwitch',
					'Iterating', 'Charging', 'Discharging',
					'CurrentError',
					'Unused9', 'Unused10', 'Unused11', 'Unused12', 'Unused13', 'Unused14',
					'MagnetFailure']
QDI_TEMP_STATUS = ['TemperatureUnknown',
					'Stable', 'Tracking',
					'Unused3', 'Unused4',
					'Near', 'Chasing', 'Filling',
					'Unused8', 'Unused9',
					'Standby',
					'Unused11', 'Unused12',
					'Disabled', 'ImpedanceNotFunction', 'TempFailure']
					
PPMS_ComputerIPAddress = "192.168.0.7"
class Dynacool:
	"""Thin wrapper around the QuantumDesign.QDInstrument.QDInstrumentBase class"""
	def __init__(self, ip_address):
		self.qdi_instrument = QDInstrumentFactory.GetQDInstrument(QDI_PPMS_TYPE, True, ip_address, DEFAULT_PORT)
		
	def getTemperature(self): #Returns (0, 174.2364, 10)
		"""Return the current temperature, in Kelvin."""
		return self.qdi_instrument.GetTemperature(0,0)
		
	def setTemperature(self, temp, rate=20):
		"""Set temperature. Keyword arguments: temp(Kelvin), rate(K/min)"""
		return self.qdi_instrument.SetTemperature(temp, rate, 0)
		
	def waitForTemperature(self, delay=5, timeout=5400):
		"""Pause execution until the PPMS reaches the temperature setpoint."""
		return self.qdi_instrument.WaitFor(True, False, False, False, delay, timeout)
		
	def getField(self): #Returns (0, -0.05000622570514679, 4)
		"""Return the current field, in gauss."""
		return self.qdi_instrument.GetField(0, 0)
	
	def setField(self, field, rate=100, persistent=False):
		"""Set the field. Keyword arguments: field(gauss), rate(gauss/second)"""
		if persistent: return self.qdi_instrument.SetField(field, rate, QDI_FIELD_APPROACH, QDI_FIELD_MODE)
		else: return self.qdi_instrument.SetField(field, rate, QDI_FIELD_APPROACH, QDI_FIELD_MODE_driven)
		
	def waitForField(self, delay=5, timeout=3600):
		"""Pause execution until the PPMS reaches the field setpoint."""
		return self.qdi_instrument.WaitFor(False, True, False, False, delay, timeout)


def connect2PPMS(ipAddress=PPMS_ComputerIPAddress):
	#The computer LAN address is 192.168.0.7. The computer server must be up in order to respond to command.
	param = '-n' if platform.system().lower() == 'windows' else '-c'
	command = ["ping", param, '1', ipAddress]
	print("Try to connect 2 PPMS", command, ipAddress)
	if subprocess.call(command) == 0:
		ppms = Dynacool(ipAddress)
		print("Successfully pinged the PPMS IP address", ipAddress, "\nThe PPMS:", ppms)
		print("Current field: {}G".format(ppms.getField()[1])) #ppms.getField() returns a tuple 
		print("Current temperature: {}K".format(ppms.getTemperature()[1])) #ppms.getTemperature() returns a tuple 
		return ppms
	else:
		print("Attempt to ping the PPMS computer failed.")
		raise
	
	
TimeConst_WaitTime_Conversion = 5

import wx, pyvisa
import pymeasure
import threading
import numpy, scipy #Generate arrays and fit arrays
from datetime import datetime
import time, os

import pandas as pd
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

wx.Log.EnableLogging(False)
wx.InitAllImageHandlers()

def get_resources():
	return pyvisa.ResourceManager().list_resources()
	
def scale_bitmap(bitmap, width, height):
	image = bitmap.ConvertToImage()
	image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
	result = wx.Bitmap(image)
	return result

def plotandSave(fileName, plotTotal):
	df = pd.read_csv(fileName, sep=',')
	fig, ax = plt.subplots()
	fields, lockinReading1, lockinReading2 = df["Field(G)"], df["Lockin_X_Ave"], df["Lockin_Y_Ave"]
	if plotTotal:
		lockinReadingSqrt = []
		for x, y in zip(lockinReading1.values, lockinReading2.values):
			sqrt = numpy.sqrt(x ** 2 + y ** 2)
			lockinReadingSqrt.append(sqrt if x >= 0 else -sqrt)
	ax.set_xlabel("Field (G)")
	ax.set_ylabel("Lockin_Ave")
	ax.plot(fields, lockinReading1, '-bo')
	ax.plot(fields, lockinReading2, '-ro')
	if plotTotal:
		ax.plot(fields, lockinReadingSqrt, '--y')
		ax.legend(['X', 'Y', "Total"])
	else:
		ax.legend(['X', 'Y'])
	figName = fileName.replace("csv", "png")
	plt.grid(True)
	plt.savefig(figName)
	plt.close()
	return figName
	
	
def connect(address, logs=None):
	device = None
	if address:
		try:
			device = pyvisa.ResourceManager().open_resource(address)
			print("Successfully connected")
			logs.add("{}:  {}".format(address, device.query("*IDN?").strip()))
			print(device.query("*IDN?"))
		except Exception as e:
			logs.add("error: {}".format(e))
			print(e)
	else: logs.add("Address NOT given. Connection failed.")
	return device
	
def lockinRead(lockin, waitTime):
	signals_1, signals_2 = [], []
	time.sleep(waitTime) #unit in seconds
	for i in range(5):
		#The mod freq is typically 573.1Hz, so 0.1sec sampling separation should be long enough
		time.sleep(0.1)
		signals_1.append(float(lockin.query("OUTP? 1")))
		signals_2.append(float(lockin.query("OUTP? 2")))
	#Discard the highest and lowest values measured
	return numpy.average(signals_1), numpy.average(signals_2)
	
def generateFieldswithCentersandLinewidths_DenseatCenter(Hres_atFreqs, linewidth_0, linewidth_1, reverse, fieldStepSize=0):
	#We want there to be 10 data points between the peak-peak
	#For each frequency, there is a set of fields the measurement will scan
	fields2Scan_atFreqs = {}
	for freq in Hres_atFreqs:
		freqs = sorted(list(Hres_atFreqs.keys()))
		if len(Hres_atFreqs) == 1:
			DeltaH_pk2pk = linewidth_0
		else:
			a, b = freqs[0], freqs[-1]
			DeltaH_pk2pk = linewidth_0 + (linewidth_1 - linewidth_0) * (freq - a) / (b - a)
		centerField = Hres_atFreqs[freq]
		fieldRange = 7 * DeltaH_pk2pk
		stepSize = fieldStepSize if fieldStepSize else round(DeltaH_pk2pk / 16, 1)
		field_init, field_1 = centerField - 0.5 * fieldRange, centerField - 0.25 * fieldRange
		field_2, field_3 = centerField - 0.12 * fieldRange, centerField + 0.12 * fieldRange
		field_4, field_end = centerField + 0.25 * fieldRange, centerField + 0.5 * fieldRange
		#Start making the fields at this frequency
		numDataPoints = int((field_1-field_init) / (4 * stepSize))
		fields2Scan_atFreqs[freq] = [round(num, 1) for num in numpy.linspace(field_init, field_1, numDataPoints)]
		numDataPoints = int((field_2-field_1) / (3 * stepSize))
		fields2Scan_atFreqs[freq] += [round(num, 1) for num in numpy.linspace(field_1, field_2, numDataPoints)][1:]
		numDataPoints = int((field_3-field_2) / stepSize)
		fields2Scan_atFreqs[freq] += [round(num, 1) for num in numpy.linspace(field_2, field_3, numDataPoints)][1:]
		numDataPoints = int((field_4-field_3) / (3 * stepSize))
		fields2Scan_atFreqs[freq] += [round(num, 1) for num in numpy.linspace(field_3, field_4, numDataPoints)][1:]
		numDataPoints = int((field_end-field_4) / (4 * stepSize))
		fields2Scan_atFreqs[freq] += [round(num, 1) for num in numpy.linspace(field_4, field_end, numDataPoints)][1:]
		print("Reverse the fields?", reverse)
		if reverse:
			fields2Scan_atFreqs[freq] = list(reversed(fields2Scan_atFreqs[freq]))
		print("At frequency {}GHz: Step Size: {}. Num of steps: {}".format(freq, stepSize, numDataPoints))
		print("\t", fields2Scan_atFreqs[freq][0:5], ".....", fields2Scan_atFreqs[freq][-5:-1])
	return fields2Scan_atFreqs
	
def generateFieldswithCentersandLinewidths_equalSpace(Hres_atFreqs, linewidth_0, linewidth_1, reverse, fieldStepSize):
	#We want there to be 10 data points between the peak-peak
	#For each frequency, there is a set of fields the measurement will scan
	fields2Scan_atFreqs = {}
	for freq in Hres_atFreqs:
		freqs = sorted(list(Hres_atFreqs.keys()))
		if len(Hres_atFreqs) == 1:
			DeltaH_pk2pk = linewidth_0
		else:
			a, b = freqs[0], freqs[-1]
			DeltaH_pk2pk = linewidth_0 + (linewidth_1 - linewidth_0) * (freq - a) / (b - a)
		centerField = Hres_atFreqs[freq]
		fieldRange = 7 * DeltaH_pk2pk
		stepSize = fieldStepSize if fieldStepSize else round(DeltaH_pk2pk / 16, 1)
		field_init, field_end = centerField - 0.5 * fieldRange, centerField + 0.5 * fieldRange
		numDataPoints = int( (field_end-field_init) / stepSize )
		#Start making the fields at this frequency
		fields2Scan_atFreqs[freq] = [round(num, 1) for num in numpy.linspace(field_init, field_end, numDataPoints)]
		print("Reverse the fields?", reverse)
		if reverse:
			fields2Scan_atFreqs[freq] = list(reversed(fields2Scan_atFreqs[freq]))
		print("At frequency {}GHz: Step Size: {}. Num of steps: {}".format(freq, stepSize, numDataPoints))
		print("\t", fields2Scan_atFreqs[freq][0:5], ".....", fields2Scan_atFreqs[freq][-5:-1])
	return fields2Scan_atFreqs
	
#创建一个固定长度的可以容纳n个字符串的列表。这个列表里面每两个元素为一对，首个元素为时间记录，次个元素为字符串
class ListLimited:
	def __init__(self, n):
		self.max_len = 2*n
		self.list = []

	def add(self, s):
		if len(self.list) == self.max_len:
			self.list.pop(0)
			self.list.pop(0)
		self.list.append(datetime.now().strftime("%Y-%m-%d	%H:%M:%S"))
		self.list.append(str(s))

	def last(self):
		return self.list[-1]


Sensitivity_Index = {0:"2nV", 1:"5nV", 2:"10nV", 3:"20nV", 4:"50nV", 5:"100nV", 6:"200nV", 7:"500nV",
					8:"1uV", 9:"2uV", 10:"5uV", 11:"10uV", 12:"20uV", 13:"50uV", 14:"100uV", 15:"200uV", 16:"500uV",
					17:"1mV", 18:"2mV", 19:"5mV", 20:"10mV", 21:"20mV", 22:"50mV", 23:"100mV", 24:"200mV", 25:"500mV",
					26:"1V/uA"
					}
					
TimeConst_Index = {0:"10us", 1:"30us", 2:"100us", 3:"300us",
					4:"1ms", 5:"3ms", 6:"10ms", 7:"30ms", 8:"100ms", 9:"300ms",
					10:"1s", 11:"3s", 12:"10s", 13:"30s", 14:"100s", 15:"300s",
					16:"1ks", 17:"3ks", 18:"10ks", 19:"30ks",
					}
					
TConstNum_Index = {0:"10e-6", 1:"30e-6", 2:"100e-6", 3:"300e-6",
					4:"1e-3", 5:"3e-3", 6:"10e-3", 7:"30e-3", 8:"100e-3", 9:"300e-3",
					10:"1", 11:"3", 12:"10", 13:"30", 14:"100", 15:"300",
					16:"1e3", 17:"3e3", 18:"10e3", 19:"30e3",
					}
					
class PPMS_FMR_App(wx.Frame):
	def __init__(self, parent, title):
		super(PPMS_FMR_App, self).__init__(parent, title=title)
		#Unique identifiers to be assigned to the buttons.
		self.ids = {key: wx.NewId() for key in \
					["refresh_gpib", "connect_gpib",
					"btn_SetRF", "btn_SetACMod", "btn_RampField", "btn_RampTemp",
					"btn_StartAbort", "btn_ToggleRF", "btn_ToggleACMod",
					"btn_LockinSensUp", "btn_LockinSensDown", "btn_AutoPhase",
					"btn_LockinTimeConstUp", "btn_LockinTimeConstDown", 
					"btn_ReverseField",
					"btn_SkipRestofFields", ]
					}
		#Only have 4 devices, so simply list them below
		self.ppms = None
		self.acMod, self.rfPower, self.lockin = None, None, None
		self.equallySpaceFields = True
		self.waitTime, self.plotTotal, self.reverseFields = 0.02, False, False
		self.rfPower_indBm, self.acCurrent_inmA = 0, 0, 
		self.skipRestofFields = False
		self.flag = False #Indicator of whether is a measurement ongoing
		self.current_job = None
		self.logs = ListLimited(8)
		self.logs.add("ping")
		self.last_log = ''
		self.InitUI()
		self.Centre()
		
	def InitUI(self):
		self.timer = wx.Timer(self, 2)
		self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
		self.timer.Start(500)
		panel = wx.Panel(self)
		
		self.sample_id = wx.TextCtrl(panel, value="Test")
		self.folder = wx.TextCtrl(panel, value=os.getcwd()+r"\FMR_Data",
									size=(350, 50), style=wx.TE_MULTILINE)
		self.log_text = wx.TextCtrl(panel, value="", size=(350, 200), style=wx.TE_READONLY| wx.TE_MULTILINE)
		png = wx.Image('ConnectionInstruction.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
		png = scale_bitmap(png, 402, 96)
		self.pic = wx.StaticBitmap(panel, -1, png)
		
		#Text boxes that have parameters for scan experiments
		self.TempsandShifts_Input = wx.TextCtrl(panel, value="21: 3, 22: 4", size=(280, 25), style=wx.TE_MULTILINE)
		self.FreqsandFields_Input = wx.TextCtrl(panel, value="19: 6000, 20: 6001", size=(280, 50), style=wx.TE_MULTILINE)
		self.linewidth_0_Input = wx.TextCtrl(panel, value="4", size=(40, -1))
		self.linewidth_1_Input = wx.TextCtrl(panel, value="5", size=(40, -1))
		self.fieldsShift_Input = wx.TextCtrl(panel, value="0", size=(40, -1))
		self.fieldStepSize_Input = wx.TextCtrl(panel, value="1", size=(40, -1))
		#Text boxes and buttons that change the set points, BUT DON'T IMPLEMENT YET
		self.fieldSetPoint_Input = wx.TextCtrl(panel, value="0", size=(40, -1))
		self.tempSetPoint_Input = wx.TextCtrl(panel, value="300", size=(40, -1))
		self.rfPower_Input = wx.TextCtrl(panel, value="-130", size=(40, -1))
		self.rfFreq_Input = wx.TextCtrl(panel, value="3", size=(40, -1))
		self.acModFreq_Input = wx.TextCtrl(panel, value="573.1", size=(40, -1))
		self.acModAmp_Input = wx.TextCtrl(panel, value="100", size=(40, -1))
		self.btn_SetRF = wx.Button(panel, label="Set RF Freq(GHz)\n\t Power(dBm)", id=self.ids['btn_SetRF'], style=wx.TE_MULTILINE)
		self.btn_SetACMod = wx.Button(panel, label="Set AC Mod\n Freq(Hz)", id=self.ids["btn_SetACMod"], style=wx.TE_MULTILINE)
		#Indicators of the intrument status/set points
		self.lbl_RFPower = wx.StaticText(panel, label="RF Power: 40GHz -130dBM") #SetLabel("New Content")
		self.lbl_ACMod_Freq = wx.StaticText(panel, label="AC Mod: 1000Hz 1mA")
		self.lbl_Field = wx.StaticText(panel, label="PPMS Field: 0G")
		self.lbl_Temp = wx.StaticText(panel, label="PPMS Temp: 300K")
		self.lbl_LockinReading = wx.StaticText(panel, label="Lock-in:\nX 0 Y 0")
		self.lbl_LockinFreq = wx.StaticText(panel, label="Lock-in Freq:\n0Hz")
		self.lbl_LockinSens = wx.StaticText(panel, label="Lock-in: X")
		self.lbl_lockinTConst = wx.StaticText(panel, label="Time Const: X")
		self.lbl_waitTime = wx.StaticText(panel, label="Wait Time: ?s")
		#Buttons that TOGGLES/CHANGES the status of instrument/PPMS
		self.btn_StartAbort = wx.Button(panel, label="Start", id=self.ids['btn_StartAbort'], size=(50, 30))
		self.btn_ToggleRF = wx.Button(panel, label="RF Power is OFF", id=self.ids['btn_ToggleRF'])
		#self.btn_ToggleFieldGenMode = wx.Button(panel, label="Fields are equally spaced", id=self.ids['btn_ToggleFieldGenMode'])
		self.btn_ToggleACMod = wx.Button(panel, label="AC Mod is OFF", id=self.ids['btn_ToggleACMod'])
		self.btn_SetField = wx.Button(panel, label="Set Field\n < 14000G", id=self.ids['btn_RampField'], style=wx.TE_MULTILINE)
		self.btn_SetTemp = wx.Button(panel, label="Set Temp(K)\n 2~350K", id=self.ids['btn_RampTemp'], style=wx.TE_MULTILINE)
		self.btn_ReverseField = wx.Button(panel, label="Field ascends", id=self.ids['btn_ReverseField'])
		#self.btn_ToggleFieldGenMode.SetBackgroundColour((0, 255, 0, 255))
		self.btn_ReverseField.SetBackgroundColour((0, 255, 0, 255))
		self.btn_SkipRestofFields = wx.Button(panel, label="Skip remaining Fields", id=self.ids['btn_SkipRestofFields'])
		self.btn_SkipRestofFields.SetBackgroundColour((128, 128, 128, 255))
		
		btn_AutoPhase = wx.Button(panel, label="Lockin Auto Phase", id=self.ids['btn_AutoPhase'])
		btn_LockinSensUp = wx.Button(panel, label="Sens Up", id=self.ids['btn_LockinSensUp'])
		btn_LockinSensDown = wx.Button(panel, label="Sens Down", id=self.ids['btn_LockinSensDown'])
		btn_LockinTimeConstUp = wx.Button(panel, label="Time Const Up", id=self.ids['btn_LockinTimeConstUp'])
		btn_LockinTimeConstDown = wx.Button(panel, label="Time Const Down", id=self.ids['btn_LockinTimeConstDown'])

		btn_RefreshGPIB = wx.Button(panel, label="Reresh GPIB Conn", id=self.ids['refresh_gpib'])
		btn_ConnGPIB = wx.Button(panel, label="Connect GPIB Conn", id=self.ids['connect_gpib'])
		#Bind the buttons to event types and functions
		#The 1st argument is the event type to process. Here it's a button process
		#The 2nd argument is the function to be bound to the button, identified by id
		self.Bind(wx.EVT_BUTTON, self.refresh_gpib, id=self.ids['refresh_gpib'])
		self.Bind(wx.EVT_BUTTON, self.connect, id=self.ids['connect_gpib'])
		self.Bind(wx.EVT_BUTTON, self.set_RF, id=self.ids['btn_SetRF'])
		self.Bind(wx.EVT_BUTTON, self.set_ACMod, id=self.ids['btn_SetACMod'])
		
		self.Bind(wx.EVT_BUTTON, self.set_Field, id=self.ids['btn_RampField'])
		self.Bind(wx.EVT_BUTTON, self.set_Temp, id=self.ids['btn_RampTemp'])
		self.Bind(wx.EVT_BUTTON, self.start_abort, id=self.ids['btn_StartAbort'])
		self.Bind(wx.EVT_BUTTON, self.toggle_RF, id=self.ids['btn_ToggleRF'])
		self.Bind(wx.EVT_BUTTON, self.toggle_ACMod, id=self.ids['btn_ToggleACMod'])
		self.Bind(wx.EVT_BUTTON, lambda e: self.lockin.write("APHS"), id=self.ids['btn_AutoPhase'])
		self.Bind(wx.EVT_BUTTON, lambda e: self.sens_Change(up=True), id=self.ids['btn_LockinSensUp'])
		self.Bind(wx.EVT_BUTTON, lambda e: self.sens_Change(up=False), id=self.ids['btn_LockinSensDown'])
		self.Bind(wx.EVT_BUTTON, lambda e: self.timeConst_Change(up=True), id=self.ids['btn_LockinTimeConstUp'])
		self.Bind(wx.EVT_BUTTON, lambda e: self.timeConst_Change(up=False), id=self.ids['btn_LockinTimeConstDown'])
		#self.Bind(wx.EVT_BUTTON, lambda e: self.toggle_FieldGenMode(), id=self.ids['btn_ToggleFieldGenMode'])
		self.Bind(wx.EVT_BUTTON, lambda e: self.toggle_ReverseFields(), id=self.ids['btn_ReverseField'])
		self.Bind(wx.EVT_BUTTON, lambda e: self.toggle_SkipRestofFields(), id=self.ids['btn_SkipRestofFields'])
		
		"""Arrange the above text input and buttons"""
		sizer = wx.GridBagSizer(15, 30)
		sizer_folder = wx.GridBagSizer(2, 3)
		sizer_conn = wx.GridBagSizer(3, 3)
		sizer_params = wx.GridBagSizer(8, 10)
		sizer_manual = wx.GridBagSizer(8, 14)
		#sample ID of the sample and where to save the data.
		sizer_folder.Add(wx.StaticText(panel, label="Sample ID"), pos=(0, 0), flag=wx.LEFT, border=5)
		sizer_folder.Add(wx.StaticText(panel, label="Folder"), pos=(1, 0), flag=wx.LEFT | wx.TOP, border=5)
		sizer_folder.Add(self.sample_id, pos=(0, 1), span=(1, 1), flag=wx.TOP | wx.EXPAND)
		sizer_folder.Add(self.folder, pos=(1, 1), span=(1, 4), flag=wx.TOP | wx.EXPAND, border=5)
		#Include the connection buttons/texts
		#ComboBoxes that holds the default values for GPIB addresses
		GPIBS = ['GPIB0::27::INSTR', 'GPIB0::11::INSTR','GPIB0::8::INSTR']
		self.cb_acMod = wx.ComboBox(panel, value='GPIB0::27::INSTR', pos=(50, 30), choices=GPIBS)
		self.cb_rfPower = wx.ComboBox(panel, value='GPIB0::11::INSTR', pos=(50, 30), choices=GPIBS)
		self.cb_lockin = wx.ComboBox(panel, value='GPIB0::8::INSTR', pos=(50, 30), choices=GPIBS)
		self.combo_boxes = [self.cb_acMod, self.cb_rfPower, self.cb_lockin]
		
		status_acMod = wx.StaticText(panel, label="not found")
		status_rfPower = wx.StaticText(panel, label="not found")
		status_lockin = wx.StaticText(panel, label="not found")
		status_PPMS = wx.StaticText(panel, label="PPMS: %s not pinged"%PPMS_ComputerIPAddress)
		self.indicators = [status_acMod, status_rfPower, status_lockin, status_PPMS]
		for indicator in self.indicators:
			indicator.SetForegroundColour((255, 0, 0, 255))
			
		sizer_conn.Add(btn_RefreshGPIB, pos=(0, 0), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_conn.Add(btn_ConnGPIB, pos=(0, 1), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_conn.Add(wx.StaticText(panel, label="6221 Source(Mod):"),
						pos=(1, 0), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_conn.Add(wx.StaticText(panel, label="N5183 Signal Generator:"),
						pos=(1, 1), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_conn.Add(wx.StaticText(panel, label="SR830m Lock-in:"),
						pos=(1, 2), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_conn.Add(self.cb_acMod, pos=(2, 0), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_conn.Add(self.cb_rfPower, pos=(2, 1), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_conn.Add(self.cb_lockin, pos=(2, 2), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_conn.Add(status_acMod, pos=(3, 0), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_conn.Add(status_rfPower, pos=(3, 1), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_conn.Add(status_lockin, pos=(3, 2), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_conn.Add(status_PPMS, pos=(4, 0), span=(1, 3), flag=wx.BOTTOM | wx.Left, border=5)
		
		sizer_conn.Add(self.btn_StartAbort, pos=(5, 2), span=(1, 1), flag=wx.RIGHT | wx.BOTTOM, border=5)
		sizer_conn.Add(self.btn_SkipRestofFields, pos=(6, 2), span=(1, 1), flag=wx.RIGHT | wx.BOTTOM, border=5)
		sizer_conn.Add(self.log_text, pos=(7, 0), span=(3, 3), flag=wx.LEFT | wx.BOTTOM, border=5)
		
		i = 1
		sizer_params.Add(wx.StaticText(panel, label="Temps(K):Shift(G)\n(Seperate with ',')"),
						pos=(0, 1), span=(1, 2), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_params.Add(self.TempsandShifts_Input, 
						pos=(0, 3), span=(1, 2), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_params.Add(wx.StaticText(panel, label="Freq(GHz):Field(G)\npairs(Seperate with ',')"),
						pos=(i+0, 1), span=(2, 2), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_params.Add(self.FreqsandFields_Input, 
						pos=(i+0, 3), span=(2, 2), flag=wx.BOTTOM | wx.Left, border=5)
		#sizer_params.Add(self.btn_ToggleFieldGenMode,
		#				pos=(0, 6), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_params.Add(self.btn_ReverseField, 
						pos=(i+0, 6), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_params.Add(wx.StaticText(panel, label="Shift(G)"),
						pos=(i+1, 6), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_params.Add(self.fieldsShift_Input, 
						pos=(i+1, 7), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_params.Add(wx.StaticText(panel, label="Initial linewidth(G)"),
						pos=(i+2, 1), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_params.Add(self.linewidth_0_Input,
						pos=(i+2, 2), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_params.Add(wx.StaticText(panel, label="Final linewidth(G)"),
						pos=(i+2, 3), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_params.Add(self.linewidth_1_Input, 
						pos=(i+2, 4), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_params.Add(wx.StaticText(panel, label="Fixed Step Size(G)"),
						pos=(i+2, 6), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_params.Add(self.fieldStepSize_Input, 
						pos=(i+2, 7), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		
		sizer_manual.Add(self.acModFreq_Input, pos=(0, 0), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_manual.Add(wx.StaticText(panel, label="Hz"),
												pos=(0, 1), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=0)
		sizer_manual.Add(self.acModAmp_Input, pos=(0, 4), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_manual.Add(wx.StaticText(panel, label="mA"),
												pos=(0, 5), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=0)
		sizer_manual.Add(self.btn_SetACMod, pos=(0, 2), span=(1, 2), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_manual.Add(self.lbl_ACMod_Freq, pos=(0, 6), span=(1, 2), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_manual.Add(self.btn_ToggleACMod, pos=(0, 8), span=(1, 2), flag=wx.BOTTOM | wx.Left, border=5)
		
		sizer_manual.Add(self.rfFreq_Input, pos=(1, 0), span=(1, 1), flag=wx.BOTTOM | wx.Right, border=0)
		sizer_manual.Add(wx.StaticText(panel, label="GHz"),
											pos=(1, 1), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=0)
		sizer_manual.Add(self.rfPower_Input, pos=(1, 2), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=0)
		sizer_manual.Add(wx.StaticText(panel, label="dBm"),
											pos=(1, 3), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=0)
		sizer_manual.Add(self.btn_SetRF, pos=(1, 4), span=(1, 2), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_manual.Add(self.lbl_RFPower, pos=(1, 6), span=(1, 2), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_manual.Add(self.btn_ToggleRF, pos=(1, 8), span=(1, 2), flag=wx.BOTTOM | wx.Left, border=5)
		
		sizer_manual.Add(self.fieldSetPoint_Input,
										pos=(2, 0), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_manual.Add(wx.StaticText(panel, label="G"),
										pos=(2, 1), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=0)
		sizer_manual.Add(self.btn_SetField, pos=(2, 2), span=(1, 2), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_manual.Add(self.lbl_Field, pos=(2, 6), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_manual.Add(self.lbl_LockinFreq, pos=(2, 7), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_manual.Add(btn_AutoPhase, pos=(2, 8), span=(1, 2), flag=wx.BOTTOM | wx.Left, border=5)
		
		sizer_manual.Add(self.tempSetPoint_Input,
										pos=(3, 0), span=(1, 1), flag=wx.Right, border=0)
		sizer_manual.Add(wx.StaticText(panel, label="K"),
										pos=(3, 1), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=0)
		sizer_manual.Add(self.btn_SetTemp, pos=(3, 2), span=(1, 2), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_manual.Add(self.lbl_Temp, pos=(3, 4), span=(1, 2), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_manual.Add(self.lbl_LockinReading, pos=(3, 6), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_manual.Add(self.lbl_LockinSens, pos=(3, 7), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_manual.Add(btn_LockinSensUp, pos=(3, 8), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_manual.Add(btn_LockinSensDown, pos=(3, 9), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		
		sizer_manual.Add(self.lbl_waitTime, pos=(4, 0), span=(1, 3), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_manual.Add(self.lbl_lockinTConst, pos=(4, 4), span=(1, 2), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_manual.Add(btn_LockinTimeConstUp, pos=(4, 6), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_manual.Add(btn_LockinTimeConstDown, pos=(4, 7), span=(1, 1), flag=wx.BOTTOM | wx.Left, border=5)
		sizer_manual.Add(self.pic, pos=(5, 0), span=(1, 9), flag=wx.BOTTOM | wx.Left, border=5)
		
		sizer.Add(sizer_folder, pos=(0, 0), span=(1, 1), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
		sizer.Add(sizer_params, pos=(0, 1), span=(1, 1), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
		sizer.Add(sizer_conn, pos=(1, 0), span=(1, 1), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
		
		sizer.Add(sizer_manual, pos=(1, 1), span=(1, 1), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
		
		panel.SetSizer(sizer)
		sizer.Fit(self)
		
	"""Connection to the 6221 source, N5183 ef power and SR830m lock-in"""
	def refresh_gpib(self, e):
		addresses = get_resources() #Return the GPIB addresses as string list
		self.cb_acMod.Set(addresses)
		self.cb_rfPower.Set(addresses)
		self.cb_lockin.Set(addresses)
		self.rfPower, self.acMod, self.lockin = None, None, None
		
	def connect(self, e):
		try: self.acMod = connect(self.cb_acMod.GetValue(), logs=self.logs)
		except Exception as e:
			self.acMod = None
			print(e)
		try: self.rfPower = connect(self.cb_rfPower.GetValue(), logs=self.logs)
		except Exception as e:
			self.rfPower = None
			print(e)
		try: self.lockin = connect(self.cb_lockin.GetValue(), logs=self.logs)
		except Exception as e:
			self.lockin = None
			print(e)
		try: self.ppms = connect2PPMS()
		except: self.logs.add("Attempt to ping the PPMS computer failed.")
		
		self.update_indicator()
		try: #Try update the status of the instruments
			self.updateDisp_ACModFreq()
			self.updateDisp_ACModStat()
			self.updateDisp_rfFreqandPower()
			self.updateDisp_rfStat()
		except: pass
		
	#Check each device and see if they exist yet. Change the label and color accordingly
	def update_indicator(self):
		print("Updating the indicators", self.ppms)
		for device, indicator in zip([self.acMod, self.rfPower, self.lockin], self.indicators):
			if device: label, colour = "connected", (0, 0, 255)
			else: label, colour = "not found", (255, 0, 0)
			indicator.SetLabel(label)
			indicator.SetForegroundColour(colour)
		if self.ppms: label, colour = "PPMS: %s pinged"%PPMS_ComputerIPAddress, (0, 0, 255)
		else: label, colour = "CANNOT ping PPMS: %s"%PPMS_ComputerIPAddress, (255, 0, 0)
		self.indicators[-1].SetLabel(label)
		self.indicators[-1].SetForegroundColour(colour)
		
	#def toggle_FieldGenMode(self):
	#	self.equallySpaceFields = not self.equallySpaceFields
	#	if self.equallySpaceFields:
	#		self.btn_ToggleFieldGenMode.SetLabel("Fields are equally spaced")
	#		self.btn_ToggleFieldGenMode.SetBackgroundColour((0, 255, 0, 255))
	#	else:
	#		self.btn_ToggleFieldGenMode.SetLabel("Fields are denser at center")
	#		self.btn_ToggleFieldGenMode.SetBackgroundColour((0, 255, 255, 255))
			
	def toggle_PlotTotal(self):
		pass
		#self.plotTotal = not self.plotTotal
		#if self.plotTotal: self.btn_ToggleFieldGenMode.SetLabel("Will Plot sqrt(X^2+Y^2)")
		#else: self.btn_ToggleFieldGenMode.SetLabel("Won't Plot sqrt(X^2+Y^2)")
			
	def toggle_ReverseFields(self):
		self.reverseFields = not self.reverseFields
		if self.reverseFields:
			self.btn_ReverseField.SetLabel("Fields descends")
			self.btn_ReverseField.SetBackgroundColour((0, 255, 255, 255))
		else:
			self.btn_ReverseField.SetLabel("Fields ascends")
			self.btn_ReverseField.SetBackgroundColour((0, 255, 0, 255))
			
	def toggle_SkipRestofFields(self):
		self.skipRestofFields = not self.skipRestofFields
		if self.skipRestofFields:
			self.btn_SkipRestofFields.SetBackgroundColour((255, 0, 0, 255))
		else:
			self.btn_SkipRestofFields.SetBackgroundColour((128, 128, 128, 255))
			
	"""For manual control of the system"""
	def updateDisp_Lockin(self):
		self.lbl_LockinFreq.SetLabel("Lock-in Freq:\n {} Hz".format(self.lockin.query("FREQ?").replace('\n', '')))
		channX = float(self.lockin.query("OUTP? 1"))
		channY = float(self.lockin.query("OUTP? 2"))
		self.lbl_LockinReading.SetLabel("Lock-in:\nX {}\nY {}".format(channX, channY))
		sens = int(self.lockin.query("SENS?").replace('\n', ''))
		timeConst_i = int(self.lockin.query("OFLT?").replace('\n', ''))
		self.lbl_LockinSens.SetLabel("Lockin Sens: {}".format(Sensitivity_Index[sens]))
		self.lbl_lockinTConst.SetLabel("Time Const: {}".format(TimeConst_Index[timeConst_i]))
		self.waitTime = round(float(TConstNum_Index[timeConst_i]) * TimeConst_WaitTime_Conversion, 2)
		self.lbl_waitTime.SetLabel("Wait Time: {}s".format(self.waitTime))
		
	def sens_Change(self, up=True):
		sensitivity = int(self.lockin.query("SENS?").replace('\n', ''))
		if up and sensitivity != 26:
			self.lockin.write("SENS {}".format(sensitivity + 1))
		if not up and sensitivity != 0:
			self.lockin.write("SENS {}".format(sensitivity - 1))
			
	def timeConst_Change(self, up=True):
		timeConst_i = int(self.lockin.query("OFLT?").replace('\n', ''))
		if up and timeConst_i != 19: #The max int is 19, corresponding to 30ks
			self.lockin.write("OFLT {}".format(timeConst_i + 1))
		if not up and timeConst_i != 0:
			self.lockin.write("OFLT {}".format(timeConst_i - 1))
		self.waitTime = round(float(TConstNum_Index[timeConst_i]) * TimeConst_WaitTime_Conversion, 2)
		self.lbl_waitTime.SetLabel("Wait Time: {}s".format(self.waitTime))
		
	def updateDisp_Field(self): #self.ppms.getField() returns a tuple, with the 2nd element the field
		field = round(self.ppms.getField()[1], 1)
		self.lbl_Field.SetLabel("PPMS Field: {} G".format(field))
		
	def updateDisp_Temp(self):
		temp = round(self.ppms.getTemperature()[1], 2)
		self.lbl_Temp.SetLabel("PPMS Temp: {} K".format(temp))
		
	def updateDisp_rfFreqandPower(self):
		realSetFreq = round(float(self.rfPower.query("FREQ?").strip()) / 1e9, 1)
		self.rfPower_indBm = round(float(self.rfPower.query("POW?").strip()))
		self.lbl_RFPower.SetLabel("RF Power: {} GHz {} dBm".format(realSetFreq, self.rfPower_indBm))
		
	def updateDisp_rfStat(self):
		self.updateDisp_rfFreqandPower()
		if '1' in self.rfPower.query(":OUTP?"): label, colour = "ON", (0, 255, 0, 255)
		else: label, colour = "OFF", (255, 0, 0, 255)
		self.btn_ToggleRF.SetLabel("RF Power is "+label)
		self.btn_ToggleRF.SetBackgroundColour(colour)
		
	def set_RF(self, e): #Change the rf power freq set point
		freqinGHz = round(float(self.rfFreq_Input.GetValue()), 1)
		powerindBm = round(float(self.rfPower_Input.GetValue()), 1)
		self.rfPower.write(":SOUR:FREQ:CW {}GHz".format(freqinGHz))
		self.rfPower.write("POW {}".format(powerindBm))
		time.sleep(0.25) #Set the freq and wait for 0.25s. Then read the value and set the indicating label
		self.updateDisp_rfFreqandPower()
		
	def toggle_RF(self, e):
		self.rfPower.write(":OUTP:MOD OFF") #Make sure to turn off the mod first, so the RF power correctly comes out.
		newState = "OFF" if '1' in self.rfPower.query(":OUTP?") else "ON"
		self.rfPower.write(":OUTP " + newState)
		self.updateDisp_rfStat()
	#Ac Modulation update and set, and toggle
	def updateDisp_ACModFreq(self):
		realSetFreq = round(float(self.acMod.query(":SOUR:WAVE:FREQ?").strip()), 1)
		self.acCurrent_inmA = round(1000 * float(self.acMod.query(":SOUR:WAVE:AMPL?").strip()), 1)
		print("real amp of the ac mod", self.acCurrent_inmA)
		self.lbl_ACMod_Freq.SetLabel("Mod Freq: {} Hz {} mA".format(realSetFreq, self.acCurrent_inmA))
		
	def updateDisp_ACModStat(self):
		self.updateDisp_ACModFreq()
		acModState = self.acMod.query(":OUTP:STAT?")
		#The returned value is "1\n" or "0\n"
		if '1' in acModState: label, colour = "ON", (0, 255, 0, 255)
		else:label, colour = "OFF", (255, 0, 0, 255)
		self.btn_ToggleACMod.SetLabel("AC Mod is "+label)
		self.btn_ToggleACMod.SetBackgroundColour(colour)
		
	def set_ACMod(self, e):
		freq = self.acModFreq_Input.GetValue() #Is a string
		self.acMod.write(":SOUR:WAVE:FREQ {}".format(freq))
		self.acMod.write(":SOUR:CURR:COMP 105")
		self.acMod.write(":SOUR:WAVE:AMPL {}".format(0.001*int(self.acModAmp_Input.GetValue())))
		time.sleep(0.25)
		self.updateDisp_ACModFreq()
		
	def toggle_ACMod(self, e):
		if '1' in self.acMod.query(":OUTP:STAT?"): #If the ac source is currently outputing modulation
			print("Turn off the source now")
			self.acMod.write(":SOUR:WAVE:ABOR")
		else: #If the ACMod is on, turn it one
			print("Turn on the source now")
			self.acMod.write(":SOUR:WAVE:ABOR")
			self.acMod.write(":SOUR:WAVE:OFFS 0")
			self.acMod.write(":SOUR:WAVE:PMAR:STAT ON") #Set the phase marker state to ON
			self.acMod.write(":SOUR:WAVE:DUR:TIME +9.9E+037") #Lasts indefinitely
			self.acMod.write(":SOUR:WAVE:ARM")
			time.sleep(1)
			self.acMod.write(":SOUR:WAVE:INIT")
		self.updateDisp_ACModFreq()
		self.updateDisp_ACModStat()
		
	#Read from self.fieldSetPoint_Input and set the PPMS field. For manual control
	def set_Field(self, e):
		print("Start ramping field to the value entered")
		try:
			field = round(float(self.fieldSetPoint_Input.GetValue()), 1)
			if abs(field) > 15000:
				self.logs.add("Target field can't possibly be >1.5T in this experiment")
				raise
			self.ppms.setField(field, 100)
			#self.ppms.waitForField(timeout=240)
		except:
			self.logs.add("Ramping field failed.")
			
	def set_Temp(self, e):
		print("Start ramping temperature to the value entered")
		try:
			temp = round(float(self.tempSetPoint_Input.GetValue()), 1)
			if temp > 310 or temp < 2:
				self.logs.add("Target temperature can't possibly be > 310K or < 2K in this experiment")
				raise
			self.ppms.setTemperature(temp, 7)
			print("Waiting for temp to settle")
			#self.ppms.waitForTemperature(timeout=7200)
		except:
			self.logs.add("Ramping temperature failed.")
			
	"""Prepare and perform measurement"""
	def prepareFieldstoScan(self):
		#Generate dictionary from the Hres vs freqs text box
		Hres_vs_freqs = self.FreqsandFields_Input.GetValue().split(',')
		shift = round(float(self.fieldsShift_Input.GetValue()))
		dict = {}
		try:
			for pair in Hres_vs_freqs: #pair is string '3: 480'
				try: freq, Hres = pair.split(':')
				except:
					print("':' is missing")
					raise
				freq, Hres = float(freq.strip()), float(Hres.strip())
				dict[freq] = Hres + shift
				try:
					linewidth_0 = round(float(self.linewidth_0_Input.GetValue())) #Only read in interger linewidth
					linewidth_1 = round(float(self.linewidth_1_Input.GetValue()))
				except:
					print("Initial or final linewidth is wrong")
					return False
			#With the dict = {Freq: Hres}, combined with initial linewidth and final linewidth, 
				#create the {Freq: [field1, field2...]} for each freq to scan
			print(dict, linewidth_0, linewidth_1)
			#If all field values are negative, then reverse the order of field generated.
			try:
				fieldStepSize = round(float(self.fieldStepSize_Input.GetValue()), 1)
				if self.equallySpaceFields:
					fields2Scan_atFreqs = generateFieldswithCentersandLinewidths_equalSpace(dict, linewidth_0, linewidth_1, self.reverseFields, fieldStepSize)
				else:
					fields2Scan_atFreqs = generateFieldswithCentersandLinewidths_DenseatCenter(dict, linewidth_0, linewidth_1, self.reverseFields, fieldStepSize)
			except:
				print("Failed to generate the final fields to scan dictionary")
				return False
			return fields2Scan_atFreqs
		except Exception as e:
			print("Can't Create dictionary of {Freq: Hres}")
			print(e)
			return False
			
	def start_abort(self, e):
		if self.current_job is None or not self.current_job.is_alive():
			self.logs.add("start measurement")
			self.flag = True
			self.btn_StartAbort.SetLabel("Abort")
			self.current_job = MyThread(self.do_measurement)
			self.current_job.start()
		else:
			self.flag = False #Set the flag to False to notify other parts of the stop
			self.btn_StartAbort.SetLabel("Stopping")
			self.logs.add("Manually stopped measurement")
			wx.CallAfter(lambda: wx.GetApp().Yield())
			print("Stop 1 reached")
			wx.CallAfter(lambda: self.current_job.join())
			print("Stop 2 reached")
			wx.CallAfter(lambda: self.logs.add("measurement stopped"))
			
	#只是把self.current_job设置为一个新的Thread
	def do_measurement(self):
		"""Read the Hres at various frequencies and the initial linewidth(peak 2 peak) and final linewidth"""
		temps_to_shifts, s = {}, self.TempsandShifts_Input.GetValue()
		print("Reading temperatures you want to scan at", s)
		if s:
			try:
				for temp_shift in s.split(","):
					s_temp, s_shift = temp_shift.split(":")
					temps_to_shifts[round(float(s_temp), 1)] = round(float(s_shift), 1)
			except SyntaxError as e:
				print("Temperature input is incorrect. Please inspect, then try again.\n", e)
				return

		if not temps_to_shifts:
			print("Failed to read any temperatures. Using the current temp")
			temps_to_shifts = {round(float(self.ppms.getTemperature()[1]), 1): round(
								float(self.fieldsShift_Input.GetValue()), 1)}

		print("\n--------------Measurements at temperatures with shifts:", temps_to_shifts, "\n--------------")
		for i, (temp, shift) in enumerate(temps_to_shifts.items()):
			if i % 2: self.toggle_ReverseFields()
			self.fieldsShift_Input.SetValue("{}".format(shift))
			if temp != round(self.ppms.getTemperature()[1], 1):
				self.ppms.setTemperature(temp)
				print("Going to set temperature {}K. Waiting to stabilize".format(temp))
				self.ppms.waitForTemperature()
				print("Stabilized at {}K. Starting measurement".format(temp))

			fields2Scan_atFreqs = self.prepareFieldstoScan()
			sampleID = self.sample_id.GetValue()
			folderName = self.folder.GetValue()+"\\%s"%sampleID
			temp = round(float(self.ppms.getTemperature()[1]), 1)
			if not temps_to_shifts or not fields2Scan_atFreqs:
				print("Parameter input incorrect. Please inspect, then try again.")
				return
			else:
				self.logs.add("Start scanning fields at various freqs")
				self.logs.add("Freqs: {}".format(fields2Scan_atFreqs.keys()))
				freqs = sorted(list(fields2Scan_atFreqs.keys()))
				if self.reverseFields: freqs = freqs[::-1]
				for freq in freqs:
					if not self.flag: return
					fields = fields2Scan_atFreqs[freq]
					self.logs.add("Scanning at Freq {} GHz".format(freq))
					self.rfPower.write(":SOUR:FREQ:CW {}GHz".format(freq))
					self.updateDisp_rfFreqandPower()
					ctrIndex = int(len(fields) / 2)
					self.logs.add("Initial field {}, final field {} and stepSize {}".format(fields[0], fields[-1], fields[ctrIndex]-fields[ctrIndex-1]))
					filename = "{}_{}K_{}GHz_{}dBm_{}mA.csv".format(sampleID, int(temp), str(freq).replace('.', 'p'),
																	self.rfPower_indBm, str(self.acCurrent_inmA).replace('.', 'p')
																	)
					filename = os.path.join(folderName, filename)
					paramSumFilename = os.path.join(folderName, "{}_{}K.txt".format(sampleID, temp))
					with open(filename, "w") as file:
						file.write("Temp(K),RF Freq(GHz),Field(G),Lockin_X_Ave,Lockin_Y_Ave,TimeConst\n")
					#Need to go to the first field and make it settle for a few seconds
					self.ppms.setField(fields[0], 100)
					self.ppms.waitForField(timeout=240)
					print("Start the field scan at {}".format(self.ppms.getField()[1]))
					fieldsActual, channXs_Ave = [], []
					i = 1
					for field in fields:
						if not self.flag: return #Abort the measurement
						if self.skipRestofFields: #If enabled, the rest of the field points at this freq will skipped.
							print("Will skip the rest of the fields")
							self.logs.add("Finish the field scan early as user needs")
							self.skipRestofFields = False
							self.btn_SkipRestofFields.SetBackgroundColour((128, 128, 128, 255))
							break
						self.ppms.setField(field, 100)
						ave_1, ave_2 = lockinRead(self.lockin, waitTime=self.waitTime)
						fieldsActual.append(self.ppms.getField()[1])
						channXs_Ave.append(ave_1)
						with open(filename, 'a') as file:
							file.write("{},{},{},{},{},{}\n".format(temp, freq, field, ave_1, ave_2, self.waitTime / TimeConst_WaitTime_Conversion))
						i += 1
						if i % 2 == 1:
							self.pic_string = [plotandSave(filename, self.plotTotal)]

					self.logs.add("Move on to next freq in 2s")
					time.sleep(2)
				
	def OnTimer(self, e):
		try: #把self.pic设置为一个新的图片
			png = wx.Image(self.pic_string[0], wx.BITMAP_TYPE_ANY).ConvertToBitmap()
			png = scale_bitmap(png, 360, 240)
			self.pic.SetBitmap(png)
		except Exception as e:
			pass
		#如果程序线程还没有设置，或者说这个线程已经运行结束，则允许重新开始
		if not self.current_job or not self.current_job.is_alive():
			self.btn_StartAbort.SetLabel("Start")
		if self.ppms:
			self.updateDisp_Field()
			self.updateDisp_Temp()
			self.updateDisp_Lockin()
			
		if not self.last_log == self.logs.last():
			self.log_text.SetValue("\n".join(self.logs.list))
			self.last_log = self.logs.last()
			
			
class MyThread(threading.Thread):
	def __init__(self, job):
		threading.Thread.__init__(self)
		self.job = job
		
	def run(self):
		print("Starting measurement")
		self.job()
		print("Measurement stopped ")
		
		
if __name__ == '__main__':
	app = wx.App()
	ex = PPMS_FMR_App(None, title="PPMS FMR Measurement")
	ex.Show()
	app.MainLoop()