import copy
from helper_functions import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from template import Template
from themeclasses import *
import tkinter.messagebox
from tkinter import filedialog


class Load(Template):
	"""
	The Load class represents all data structures, methods, and visualization associated with importing a baseline
	electric load, generating it based on tariff inputs, or assuming it is flat at zero kW.
	"""
	def __init__(self, parent, controller, bd):
		Template.__init__(self, parent, controller, bd)

		# State variables
		self.uploadsuccess = False
		self.llwarningstate = False

		# Internal variables
		self.loadvalidation = dict()
		self.data = pd.DataFrame()
		self.dt = tk.DoubleVar()
		self.dt.set(.25)
		self.datayear = 2019  # tk.IntVar()
		# self.datayear.set(2019)
		self.loads_folder = './Baseline_Loads/'
		self.loadlimit = tk.DoubleVar()
		self.llwarningtext = tk.StringVar()
		self.llwarningtext.set('')

		# Read Text from files
		with open('./UI_Text/Load_Description.txt', 'r') as _f:  # Read splash screen text from file
			loadtext = _f.read()
		with open('./UI_Text/Load_Limit_Warning.txt', 'r') as _f:  # Read splash screen text from file
			self.loadlimitwarningtext = _f.read()

		# Graphic Elements
		title = pagetitle(self.titleframe, 'Baseline Electric Load')
		title.grid(row=0, column=0, sticky='nsew')

		self.loaddt = tk.OptionMenu(self.controlsframe, self.dt, .25)
		# self.datayearinput = tk.OptionMenu(self.controlsframe, self.datayear, 2020, 2019, 2018, 2017, 2016, 2017)
		self.uploadbutton = tk.Button(self.controlsframe,
									  text='Upload Baseline Load Data',
									  command=lambda: self.uploaddata(),
									  height=theme['uploadbuttonheight'],
									  width=theme['uploadbuttonwidth'])
		orlabel = tk.Label(self.controlsframe, text='OR', font=('quicksand', 16, 'bold'))
		self.uploadbillbutton = tk.Button(self.controlsframe,
										  text='Upload Utility Bills',
										  command=lambda: self.uploadbill(),
										  height=theme['uploadbuttonheight'],
										  width=theme['uploadbuttonwidth'])

		self.uploadcheck = tk.PhotoImage(file='./Images/check.png', )
		self.uploadchecklabel = tk.Label(self.controlsframe, image=self.uploadcheck)
		self.uploadchecklabel.image = self.uploadcheck
		self.uploadchecklabel.grid(row=1, column=1)
		self.uploadwarning = tk.Label(self.controlsframe,
									  text='Please upload a baseline load file or enter your past utility bills',
									  wraplength=200)
		self.uploadwarning.grid(row=1, column=1)

		nonly = (self.register(numonlynoblank), '%S')
		self.loadlimitinput = tk.Entry(self.controlsframe, textvariable=self.loadlimit, validate='key',
									   validatecommand=nonly)
		self.loadlimit.trace('w', self.llwarningupdate)  # Trace to update plot when variable changes
		self.lllabel = tk.Label(self.controlsframe, text='\n\nPlanned Load Limit (kW): ', justify='right')
		self.loadlabel = instruction_label(parentframe=self.instructionsframe, text=loadtext)

		# Put graphical elements on screen
		self.uploadbutton.grid(row=0, column=0, sticky='new')  # pack()
		orlabel.grid(row=1, column=0, sticky='new')
		self.uploadbillbutton.grid(row=2, column=0, sticky='new')
		self.lllabel.grid(row=3, column=0, sticky='nsew')
		self.loadlimitinput.grid(row=4, column=0)
		self.loadlabel.grid(row=0, column=0, sticky='nsew')
		# self.datayearinput.grid(row=5, column=0)

		self.popuppeakbymonthbutton = tk.Button(self.controlsframe,
												text='Show Peak Day by Month Plot',
												command=lambda: self.popuppeakbymonth())
		self.popuppeakbymonthbutton.grid(row=6, column=0, sticky='nsew')

		self.popupavgbymonthbutton = tk.Button(self.controlsframe,
											   text='Show Average Day by Month Plot',
											   command=lambda: self.popupavgbymonth())
		self.popupavgbymonthbutton.grid(row=7, column=0, sticky='nsew')

		# Set up plotting canvas
		self.plotwindow = tk.Frame(self.rightframe)
		self.plotwindow.grid(row=0, column=0, sticky='nsew')

		self.figure = plt.figure(num=2, figsize=(10, 5), dpi=100)
		self.axes = self.figure.add_subplot(111)
		self.chart_type = FigureCanvasTkAgg(self.figure, self.plotwindow)
		self.toolbar = NavigationToolbar2Tk(self.chart_type, self.plotwindow)
		self.toolbar.update()
		self.chart_type._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

	def uploaddata(self):
		"""
		Upload a baseline electric load file, call the validate_load() function to ensure it is valid, and call the
		plot_baseline() function to visualize the valid load profile.
		:return: N/A
		"""
		filename = filedialog.askopenfilename(filetypes=[('CSV', '*.csv')], initialdir='./Baseline_Loads')

		if filename:  # don't try to import anything if filename is empty
			self.data = pd.read_csv(filename)
			# Convert datetime to datetime format
			self.data['Datetime'] = pd.to_datetime(self.data['Datetime'])
			self.data.set_index('Datetime')

			self.validate_load()
			self.plot_baseline()
			self.llwarningupdate(None, None, None)
			self.controller.writetolog('Uploaded baseline load data file ' + filename)
			self.datayear = self.data.loc[1, 'Datetime'].year
		else:
			self.controller.writetolog('Failed to upload baseline load data file')

	def uploadbill(self):
		"""
		Input Data from utility bills and generate a modeled time series load profile
		:return: N/A
		"""
		# Require that a tariff has already been uploaded
		if not self.controller.frames['Tariff'].uploadsuccess:
			tkinter.messagebox.showinfo('Error', 'A valid tariff file needs to be imported before inputting bill information')
			# print('A valid tariff file needs to be uploaded before inputting bill information')
			self.controller.writetolog('Could not enter utility bill data, tariff still required')
			return None

		# Open new frame
		self.controller.frames['Bill'].load_tariff()
		self.controller.show_frame("Bill")

	def validate_load(self):
		"""
		Run a set of checks on an uploaded baseline electric load data frame to ensure it is valid.
		:return: N/A
		"""
		self.loadvalidation = dict()
		# Initialize all checks as passing
		loadvalidation = {'nsteps': True,
						  'dtype': True,
						  'positive': True}

		# Check if imported data matches input dt
		expectedtimesteps = 8760/self.dt.get()  # for a full year of time steps
		if self.data.shape[0] != expectedtimesteps:
			loadvalidation['nsteps'] = False

		# Check if imported data is numeric
		if not np.issubdtype(self.data['Baseline Electric Load (kW)'].dtype, np.number):
			loadvalidation['dtype'] = False

		# check if data is strictly positive
		if any(self.data['Baseline Electric Load (kW)'] < 0):
			loadvalidation['positive'] = False

		# Update the success status
		if all(value for value in loadvalidation.values()):
			self.uploadsuccess = True
			self.controller.writetolog('Baseline electric load successfully validated')
		if not all(value for value in loadvalidation.values()):
			self.uploadsuccess = False
			self.controller.writetolog('Baseline electric load validation failed')

		self.loadvalidation = loadvalidation
		self.dynamicupload()

	def plot_baseline(self):
		"""
		Make a visualization of a valid baseline load data frame and draw it into the window.
		:return:
		"""
		if self.data.shape[0] > 0:  # test to ensure that there is actually data in the data frame
			plt.figure(2)
			plt.cla()  # Clear the plotting window to allow for re-plotting.

			# Plot the peak day
			self.axes.step(x=self.data['Datetime'], y=self.data['Baseline Electric Load (kW)'],
					 where='post', color=theme['loadcolor'], zorder=1)

			# Add load limit line
			if self.loadlimit.get() > 0:
				self.axes.hlines(self.loadlimit.get(), xmin=min(self.data['Datetime']), xmax=max(self.data['Datetime']),
						   colors='r', zorder=2)

			self.axes.set_title('Baseline Load')
			self.axes.set_ylabel('Baseline Electric Load (kW)')
			self.figure.tight_layout()
			self.chart_type.draw()
			# plt.savefig('Plots/Baseline_Load.png')

	def llwarningupdate(self, a, b, c):
		"""
		 Update the load limit exceeded warning
		 a, b, and c are dummy variables so this function can be used with trace
		"""
		try:
			loadlimit = self.loadlimit.get()
			if loadlimit < max(self.data['Baseline Electric Load (kW)']):
				self.llwarningtext.set(self.loadlimitwarningtext)
				self.llwarningstate = True
			else:
				self.llwarningtext.set('')
				self.llwarningstate = False
			self.plot_baseline()
		except:
			pass

	def dynamicupload(self):
		# appear or disappear check marks
		if self.loadvalidation:
			self.uploadwarning.grid_remove()
			self.uploadchecklabel.grid()
		else:
			self.uploadchecklabel.grid_remove()
			self.uploadwarning.grid()

	def popuppeakbymonth(self):
		if self.data.shape[0] == 0:
			print('Cannot plot yet - we need the baseline load first')
			return 1

		top = tk.Toplevel(self.controller)
		top.title('Peak Day by Month')

		monthlypeakids = \
			self.data.groupby(self.data['Datetime'].dt.month).apply(lambda x: x['Baseline Electric Load (kW)'].idxmax())
		peakdates = self.data.loc[monthlypeakids, "Datetime"].dt.date
		mask = [(x in set(peakdates)) for x in self.data['Datetime'].dt.date]
		toplot = copy.deepcopy(self.data.loc[mask, :])

		figure = plt.figure(num=7, figsize=(10, 5), dpi=100)
		axes = figure.add_subplot(111)
		chart_type = FigureCanvasTkAgg(figure, top)
		toolbar = NavigationToolbar2Tk(chart_type, top)
		toolbar.update()
		chart_type._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

		toplot.loc[:, 'Date'] = copy.deepcopy(toplot['Datetime'].dt.date)
		mo = 0
		for date in sorted(set(toplot['Date'])):
			mask = [x == date for x in toplot['Datetime'].dt.date]
			axes.step(x=(1/60)*toplot.loc[mask, 'Datetime'].dt.minute + toplot.loc[mask, 'Datetime'].dt.hour,
					  y=toplot.loc[mask, 'Baseline Electric Load (kW)'],
					  where='post',
					  zorder=1,
					  label=str(date),
					  color=theme['MONTHCOLORS'][mo])
			mo += 1
		plt.xlabel('Hour of the Day')
		plt.ylabel('Baseline Electric Load (kW)')
		plt.title('Peak Day in Each Month')
		plt.legend()
		figure.show()

	def popupavgbymonth(self):
		if self.data.shape[0] == 0:
			print('Cannot plot yet - we need the baseline load first')
			return 1

		top = tk.Toplevel(self.controller)
		top.title('Average Day by Month')

		toplot = copy.deepcopy(self.data)
		toplot['month'] = toplot['Datetime'].dt.month
		toplot['hour'] = (1/60)*toplot['Datetime'].dt.minute + toplot['Datetime'].dt.hour
		toplot = toplot.groupby(['month', 'hour']).mean().reset_index()

		figure = plt.figure(num=8, figsize=(10, 5), dpi=100)
		axes = figure.add_subplot(111)
		chart_type = FigureCanvasTkAgg(figure, top)
		toolbar = NavigationToolbar2Tk(chart_type, top)
		toolbar.update()
		chart_type._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

		mo = 0
		for month in sorted(set(toplot['month'])):
			mask = [x == month for x in toplot['month']]
			axes.step(x=(1/60)*toplot.loc[mask, 'hour'],
					  y=toplot.loc[mask, 'Baseline Electric Load (kW)'],
					  where='post',
					  zorder=1,
					  label=theme['MONTHNAMES'][mo],
					  color=theme['MONTHCOLORS'][mo])
			mo += 1
		plt.xlabel('Hour of the Day')
		plt.ylabel('Baseline Electric Load (kW)')
		plt.title('Average Day in Each Month')
		plt.legend()
		figure.show()
