# Import external modules
import copy
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import os
import pandas as pd
from pandas.plotting import register_matplotlib_converters
import pickle
import pyplot_themes
from tkinter import filedialog

# Import DEFT Modules
from bill import Bill
from dervet import DERVET
from load import Load
from newload import Newload
from results import Results
from schedule import Schedule
from splash import Splash
from tariff import Tariff
from themeclasses import *
from zeequip import Zeequip
from zespec import ZESpec

# Setup scripts
register_matplotlib_converters()
pyplot_themes.theme_ucberkeley()

with open('theme.json', 'r') as f:
	theme = json.load(f)


class DEFT(tk.Tk):
	"""The DEFT class holds all data, methods, and GUI elements for the DEFT tool. It inherits from tkinter, building
	the GUI directly into its class structure. The tkinter mainloop method will run the GUI after the DEFT class
	is initialized. This loop runs through all GUI elements looking for changes then re-evaluates code that is
	impacted by GUI decisions."""

	def __init__(self):
		tk.Tk.__init__(self)
		self.title('DEFT')

		# Clear out old plots
		filestodelete = os.listdir('Plots')
		for file in filestodelete:
			os.remove('Plots/'+file)

		with open('parameters.json') as _f:
			self.parameters = json.load(_f)

		opentime = datetime.datetime.now()
		self.logfilename = opentime.strftime('%Y%m%d_%H%M%S') + '.LOG'
		with open('Logs/' + self.logfilename, 'w') as _f:
			_f.writelines('BEGIN\n')

		self.writetolog('Opening DEFT')

		# Construct "Main" container that will change every time a navigation button is pressed. The container is
		# static but the frame shown on top in the container will change with navigation buttons.
		container = tk.Frame(self)
		container.grid(row=0, column=0)
		container.columnconfigure('all', weight=1)
		container.rowconfigure('all', weight=1)
		self.protocol('WM_DELETE_WINDOW', lambda: self.closefunction())

		# Maintain an attribute that contains all frame objects, regardless of whether they are static (i.e. the
		# header frame) or dynamic (like all of the interactive content frames).
		self.frames = {}

		# Build Title frame (static)
		title = Title(parent=container, controller=self)
		self.frames['Title'] = title
		title.grid(row=0, column=0, sticky='nsew')

		self.bottomframe = tk.Frame(container)
		self.bottomframe.grid(row=1, column=0, sticky='nsew')

		# Build Navbar frame (static)
		navbar = Navbar(parent=self.bottomframe, controller=self)
		self.frames['Navbar'] = navbar
		navbar.grid(row=0, column=0, sticky='nsew')
		navbar.columnconfigure('all', weight=1)
		navbar.rowconfigure('all', weight=1)

		self.dynamicframes = (Schedule, Tariff, Load, Zeequip, Newload, Results,
							  ZESpec, Bill, DERVET, Splash)  # Put Splash at the end to start the window there

		# Build all dynamic frames. This loops through all of the dynamic frames, adds them to the self.frames
		# object and draws them into the GUI in the bottom right corner (row 1, col 1).
		for F in self.dynamicframes:
			page_name = F.__name__
			self.writetolog('Loading ' + page_name + ' Frame')
			frame = F(parent=self.bottomframe, controller=self, bd=2)
			self.frames[page_name] = frame
			frame.grid(row=0, column=1, sticky="nsew")

	def show_frame(self, page_name):
		"""
		Show a frame for the given page name. This function raises the frame with the given page_name to the top
		of the container so it is visible and so the users can interact with it GUI elements.
		"""
		frame = self.frames[page_name]
		frame.tkraise()

		self.frames['Navbar'].changehighlight(page_name)

		if (page_name == 'Newload') & (not self.frames['Newload'].calculated):
			self.frames['Newload'].calc_battery_charging(self)
			self.frames['Newload'].update_warning()

		# if page_name == 'DERVET':
		# 	self.frames['DERVET'].plotdervetts()

		if page_name == 'Zeequip':
			self.frames['Zeequip'].Update_Warnings()
			self.frames['Zeequip'].Load_Saved()
			self.frames['Zeequip'].updatetypebg()

	def closefunction(self):
		self.writetolog('Closing!')
		self.quit()
		self.destroy()

	def writetolog(self, text):
		with open('Logs/' + self.logfilename, 'a') as _f:
			_f.writelines('LOG: ' + text + ' [' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ']\n')

	def save(self):
		# pop up file selector window to create download file
		datatype = [('DEFT Files', '*.deft')]
		savetofilename = filedialog.asksaveasfile(filetypes=datatype, defaultextension=datatype,
												  initialfile=self.logfilename[:-4] + '.deft')
		datatosave = {"Average Day Schedule": self.frames['Schedule'].avgschedulelist,
					  "Busy Day Schedule": self.frames['Schedule'].busyschedulelist,
					  "Tariff": self.frames['Tariff'].data,
					  "Tarifffilename": self.frames['Tariff'].filename,
					  "dt": self.frames['Load'].dt.get(),
					  "Datayear": self.frames['Load'].datayear.get(),
					  "Baseline Load": self.frames['Load'].data,
					  "Load Limit": self.frames['Load'].loadlimit.get(),
					  "Selected": self.frames["Zeequip"].selected,
					  "Avg ZE Load": self.frames["Newload"].avgzeload,
					  "Busy ZE Load": self.frames["Newload"].busyzeload,
					  "New Load": self.frames["Newload"].newload,
					  "Controlled vs Uncontrolled": self.frames['Newload'].chargingmode.get(),
					  "Charge on Breaks": self.frames['Newload'].allowbreakcharge.get(),
					  "Bill": self.frames["Results"].bill,
					  "Fuel": self.frames["Newload"].fuelandemissions}

		with open(savetofilename.name, 'wb') as _f:
			pickle.dump(datatosave, _f)

	def load(self):
		filetoload = filedialog.askopenfilename(filetypes=[('DEFT Files', '*.deft')])

		with open(filetoload, 'rb') as _f:
			loadeddata = pickle.load(_f)

		# Distribute data to appropriate frames
		# Schedule
		self.frames['Schedule'].avgsheet.set_sheet_data(data=loadeddata["Average Day Schedule"],
														reset_col_positions=False,
														reset_row_positions=False)
		self.frames['Schedule'].avgschedulelist = copy.deepcopy(loadeddata['Average Day Schedule'])
		self.frames['Schedule'].recolor_all_avg(self.frames['Schedule'])
		self.frames['Schedule'].busysheet.set_sheet_data(data=loadeddata["Busy Day Schedule"],
														reset_col_positions=False,
														reset_row_positions=False)

		self.frames['Schedule'].busyschedulelist = copy.deepcopy(loadeddata['Busy Day Schedule'])
		self.frames['Schedule'].recolor_all_busy(self.frames['Schedule'])

		# Tariff
		self.frames['Tariff'].data = copy.deepcopy(loadeddata['Tariff'])
		self.frames['Tariff'].filename = copy.deepcopy(loadeddata['Tarifffilename'])
		if not loadeddata['Tariff'].empty:
			self.frames['Tariff'].plot_tariff()
		else:
			self.frames['Tariff'].data = pd.DataFrame(columns=['Billing Period', 'Start Month', 'End Month',
															   'Start Time', 'End Time', 'Excluding Start Time',
															   'Excluding End Time', 'Weekday?', 'Value', 'Charge',
															   'Name_optional'])

		# Baseline Load
		self.frames["Load"].dt.set(loadeddata["dt"])
		self.frames["Load"].datayear = copy.deepcopy(loadeddata["Datayear"])
		self.frames["Load"].loadlimit.set(loadeddata["Load Limit"])
		self.frames["Load"].data = copy.deepcopy(loadeddata["Baseline Load"])
		if not loadeddata['Baseline Load'].empty:
			self.frames["Load"].plot_baseline()
		else:
			self.frames['Load'].data = pd.DataFrame()

		# ZE Tech
		self.frames["Zeequip"].selected = copy.deepcopy(loadeddata["Selected"])

		# New Load
		self.frames["Newload"].avgzeload = copy.deepcopy(loadeddata['Avg ZE Load'])
		self.frames["Newload"].busyzeload = copy.deepcopy(loadeddata['Busy ZE Load'])
		self.frames["Newload"].newload = copy.deepcopy(loadeddata['New Load'])
		self.frames["Newload"].fuelandemissions = copy.deepcopy(loadeddata["Fuel"])
		self.frames['Newload'].chargingmode.set(loadeddata['Controlled vs Uncontrolled'])
		self.frames['Newload'].allowbreakcharge.set(loadeddata['Charge on Breaks'])

		if not loadeddata["Avg ZE Load"].empty:
			self.frames["Newload"].plot_newload()

		# Results
		self.frames["Results"].bill = copy.deepcopy(loadeddata['Bill'])

	def plot_all(self):
		"""Run through every plot in the DEFT, plotting and saving the plots as pngs for report-building purposes"""

		# remove all plots from plot directory
		for _p in os.listdir('Plots'):
			os.remove('Plots/' + _p)

		# re-plot each and save png
		#    Tariff Demand and Energy Prices (figure 1)
		if self.frames['Tariff'].data.shape[0] > 0:
			plottype = self.frames['Tariff'].chargetypetoplot.get()
			self.frames['Tariff'].chargetypetoplot.set('energy')
			self.frames['Tariff'].plot_tariff()
			plt.savefig('Plots/Tariff_Energy.png')
			self.frames['Tariff'].chargetypetoplot.set('demand')
			self.frames['Tariff'].plot_tariff()
			plt.savefig('Plots/Tariff_Demand.png')
			if plottype == 'energy':
				self.frames['Tariff'].chargetypetoplot.set('energy')
				self.frames['Tariff'].plot_tariff()

		# Baseline Electric Load (figure 2)
		if not self.frames['Load'].data.empty:
			self.frames['Load'].plot_baseline()
			plt.savefig('Plots/Baseline_Load.png')

		# TODO: Plot x by month plots

		# Newload
		if not self.frames['Newload'].newload.empty:
			plottype = self.frames['Newload'].plottype.get()
			self.frames['Newload'].plottype.set('Average')
			self.frames['Newload'].plot_newload()
			plt.savefig('Plots/New Average Load.png')
			self.frames['Newload'].plottype.set('Busy')
			self.frames['Newload'].plot_newload()
			plt.savefig('Plots/New Busy Load.png')
			if plottype == 'Average':
				self.frames['Newload'].plottype.set('Average')
				self.frames['Newload'].plot_newload()
			self.frames['Newload'].plot_newload_peakday()
			plt.savefig('Plots/New Load Peak Day.png')

		# Monthly Bills
		if not self.frames['Newload'].newload.empty:
			self.frames['Results'].calcmonthlybills(self)
			plottype = self.frames['Results'].plottype.get()
			self.frames['Results'].plottype.set('Demand')
			self.frames['Results'].plotmonthlybills()
			plt.savefig('Plots/Monthly_Demand_Bills.png')
			self.frames['Results'].plottype.set('Energy')
			self.frames['Results'].plotmonthlybills()
			plt.savefig('Plots/Monthly_Energy_Bills.png')
			self.frames['Results'].plotfueluse()
			plt.savefig('Plots/Fuel Use and Emissions.png')
			if plottype == 'Demand':
				self.frames['Results'].plottype.set('Demand')
				self.frames['Results'].plotmonthlybills()

	def export_csvs(self):
		datatosave = {"Baseline Load": self.frames['Load'].data,
					  "Avg ZE Load": self.frames["Newload"].avgzeload,
					  "Busy ZE Load": self.frames["Newload"].busyzeload,
					  "New Load": self.frames["Newload"].newload,
					  "Bill": self.frames["Results"].bill}
		savetofolder = filedialog.askdirectory()
		for key, value in datatosave.items():
			value.to_csv(savetofolder + '/' + key +'.csv')




		# DER-VET



class Title(tk.Frame):
	"""
	This class sets up, formats, and draws the title to the row=0, col=1 cell in the main grid.
	"""

	def __init__(self, parent, controller):
		tk.Frame.__init__(self, parent)
		self.controller = controller

		logo = tk.PhotoImage(file='./Images/Logo_Updated_2.png')
		logolabel = tk.Label(self, image=logo)
		logolabel.image = logo  # keep this reference to keep image visible!
		logolabel.grid(row=0, column=0, sticky='nsew')

		titlelabel = tk.Label(self, text='Dynamic Energy Forecasting Tool', font=theme['maintitlefont'], justify='center')
		titlelabel.grid(row=0, column=1, sticky='nsew')

		icon = tk.PhotoImage(file='./Images/Icon2.png')  # Logos_downsized.gif

		iconlabel = tk.Label(self, image=icon)
		iconlabel.image = icon  # keep this reference to keep image visible!
		iconlabel.grid(row=0, column=2, sticky='nsew')

		self.savebutton = tk.Button(self, text='Save', command=lambda: self.controller.save())
		self.savebutton.grid(row=0, column=3, sticky='nsew')
		self.savebutton.configure(state='disabled')

		self.loadbutton = tk.Button(self, text='Load', command=lambda: self.controller.load())
		self.loadbutton.grid(row=0, column=4, sticky="nsew")
		self.loadbutton.configure(state='disabled')

		self.exportbutton = tk.Button(self, text='Export .csvs', command=lambda: self.controller.export_csvs())
		self.exportbutton.grid(row=0, column=5, sticky='nsew')
		self.exportbutton.configure(state='disabled')


class Navbar(tk.Frame):
	"""
	This class sets up the navigation bar for the row=1, col=0 cell of the main grid. All of the buttons that raise
	a frame to the top of the GUI stack are here, which call the DEFT.show_frame() method when clicked.
	"""

	def __init__(self, parent, controller):
		tk.Frame.__init__(self, parent)
		self.controller = controller

		self.grid_rowconfigure(0, weight=1)
		self.configure(highlightbackground="black", highlightthickness=2)

		# Configure Navbar Theme
		self.headerfont = ('quicksand', 20, 'bold')
		self.buttonfont = ('quicksand', 18)

		self.buttonsframe = tk.Frame(self)
		self.labelsframe = tk.Frame(self)

		self.labelsframe.grid(row=0, column=0, sticky='nsew')
		self.labelsframe.grid_rowconfigure(0, weight=1)
		self.labelsframe.grid_rowconfigure(1, weight=4)
		self.labelsframe.grid_rowconfigure(2, weight=2)

		self.buttonsframe.grid_rowconfigure(1, weight=1)
		self.buttonsframe.grid_rowconfigure(3, weight=1)
		self.buttonsframe.grid_rowconfigure(4, weight=1)
		self.buttonsframe.grid_rowconfigure(5, weight=1)
		self.buttonsframe.grid_rowconfigure(6, weight=1)
		self.buttonsframe.grid_rowconfigure(9, weight=1)
		self.buttonsframe.grid_rowconfigure(10, weight=1)
		self.buttonsframe.grid(row=0, column=1, sticky='nsew')

		# Create Navigation Buttons
		self.gotosplash = tk.Button(self.buttonsframe, text="1. About",
									command=lambda: controller.show_frame("Splash"),
							   		font=self.buttonfont, bg=theme['POLBcolor'], bd=3, anchor='w')
		self.gotoschedule = tk.Button(self.buttonsframe, text="2. Schedule",
									  command=lambda: controller.show_frame("Schedule"),
									  font=self.buttonfont, bg='gainsboro', bd=3, anchor='w')
		self.gototariff = tk.Button(self.buttonsframe, text="3. Tariff",
									command=lambda: controller.show_frame("Tariff"),
									font=self.buttonfont, bg='gainsboro', bd=3, anchor='w')
		self.gotoload = tk.Button(self.buttonsframe, text="4. Baseline Load",
								  command=lambda: controller.show_frame("Load"),
								  font=self.buttonfont, bg='gainsboro', bd=3, anchor='w')
		self.gotozeequip = tk.Button(self.buttonsframe, text="5. ZE Equipment",
									 command=lambda: controller.show_frame("Zeequip"),
									 font=self.buttonfont, bg='gainsboro', bd=3, anchor='w')
		self.gotonewload = tk.Button(self.buttonsframe, text="6. Simulate",
									 command=lambda: controller.show_frame("Newload"),
									 font=self.buttonfont, bg='gainsboro', bd=3, anchor='w')
		self.gotoresults = tk.Button(self.buttonsframe, text="7. Results",
									 command=lambda: controller.show_frame("Results"),
									 font=self.buttonfont, bg='gainsboro', bd=3, anchor='w')

		self.buttonnamedic = {'Splash': self.gotosplash,
							  'Schedule': self.gotoschedule,
							  'Tariff': self.gototariff,
							  'Load': self.gotoload,
							  'Zeequip': self.gotozeequip,
							  'Newload': self.gotonewload,
							  'Results': self.gotoresults}

		# Place Navigation Buttons
		self.gotosplash.grid(row=1, column=0, sticky='nsew')
		self.gotoschedule.grid(row=3, column=0, sticky='nsew')
		self.gototariff.grid(row=4, column=0, sticky='nsew')
		self.gotoload.grid(row=5, column=0, sticky='nsew')
		self.gotozeequip.grid(row=6, column=0, sticky='nsew')
		self.gotonewload.grid(row=9, column=0, sticky='nsew')
		self.gotoresults.grid(row=10, column=0, sticky='nsew')

		# Start disabled
		self.gotoschedule.configure(state='disabled')
		self.gototariff.configure(state='disabled')
		self.gotoload.configure(state='disabled')
		self.gotozeequip.configure(state='disabled')
		self.gotonewload.configure(state='disabled')
		self.gotoresults.configure(state='disabled')

	def changehighlight(self, frame):
		for key, value in self.buttonnamedic.items():
			if key == frame:
				self.buttonnamedic[key].configure(bg=theme['POLBcolor'])
			else:
				self.buttonnamedic[key].configure(bg='gainsboro')


def main():
	app = DEFT()
	app.mainloop()


if __name__ == "__main__":
	"""
	Run the DEFT program. Initialize the DEFT class and call its main loop, which will run until stopped by 
	terminating the python script or clicking the x button.
	"""
	main()
