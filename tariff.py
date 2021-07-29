
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from template import Template
from themeclasses import *
import tkinter as tk
from tkinter import filedialog


class Tariff(Template):
	"""
	The tariff page collects relevant information about the terminal's electric tariff and offers a visualization
	of the tariff.
	"""
	def __init__(self, parent, controller, bd):
		Template.__init__(self, parent, controller, bd)

		self.plotweekend = False
		self.uploadsuccess = False

		self.filename = ''

		title = pagetitle(self.titleframe, 'Tariff')
		title.grid(row=0, column=0, sticky='nsew')

		self.data = pd.DataFrame(columns=['Billing Period', 'Start Month', 'End Month', 'Start Time', 'End Time',
										  'Excluding Start Time', 'Excluding End Time', 'Weekday?', 'Value',
										  'Charge', 'Name_optional'])

		self.chargetypetoplot = tk.StringVar(self)
		self.chargetypetoplot.set('demand')

		uploadbutton = tk.Button(self.controlsframe, text='Upload Tariff File', command=lambda: self.uploaddata(),
								 height=theme['uploadbuttonheight'])  # , width = uploadbuttonwidth
		self.uploadcheck = tk.PhotoImage(file='./Images/check.png', )
		self.uploadchecklabel = tk.Label(self.controlsframe, image=self.uploadcheck)
		self.uploadchecklabel.image = self.uploadcheck
		self.uploadchecklabel.grid(row=0, column=1)
		self.uploadwarning = tk.Label(self.controlsframe, text='Please upload a tariff file', wraplength=200)
		self.uploadwarning.grid(row=0, column=1)

		dropdown3label = tk.Label(self.controlsframe, text='\n\nShow demand or energy prices below?', wraplength=200)
		dropdown3 = tk.OptionMenu(self.controlsframe, self.chargetypetoplot, 'demand', 'energy',
								  command=lambda _: self.plot_tariff())

		with open('./UI_Text/Tariff_Description.txt', 'r') as _f:  # Read splash screen text from file
			tarifftext = _f.read()
		instructionslabel = instruction_label(self.instructionsframe, tarifftext)
		instructionslabel.grid(row=0, column=0, sticky='nsew')
		uploadbutton.grid(row=0, column=0, sticky='new')
		dropdown3label.grid(row=1, column=0, sticky='new')
		dropdown3.grid(row=2, column=0, sticky='new')

		# Set up plotting canvas
		self.plotwindow = tk.Frame(self.rightframe)
		self.plotwindow.grid(row=0, column=0)
		self.figure = plt.figure(num=1, figsize=(10, 5), dpi=100)
		self.axes = self.figure.add_subplot(111)
		self.chart_type = FigureCanvasTkAgg(self.figure, self.plotwindow)
		self.toolbar = NavigationToolbar2Tk(self.chart_type, self.plotwindow)
		self.toolbar.update()
		self.chart_type._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

	def uploaddata(self):
		"""
		This function (initiated by clicking the "Upload Tariff File" button) brings up a file browser window and lets
		the user select a tariff csv file to import into the tool. After successfully selecting a file to upload,
		the function reads the file into a pandas data frame, calls the validate_tariff() function to ensure the file
		is coherent, and calls the plot_tariff() function to visualize the tariff.
		:return: N/A
		"""
		self.filename = filedialog.askopenfilename(filetypes=[('CSV', '*.csv')],
											  initialdir='./Tariffs')

		if self.filename:  # don't try to import anything if filename is empty
			self.data = pd.read_csv(self.filename)
			self.validate_tariff()  # TODO: build out contingency when validation fails.
			self.plot_tariff()
			self.uploadsuccess = True
			self.controller.writetolog('Uploaded tariff file ' + self.filename)
		else:
			self.uploadsuccess = False
			self.controller.writetolog('Failed to upload tariff file')

		self.dynamicupload()

	def validate_tariff(self):
		"""
		This function contains the tests required to validate that a tariff data frame is valid
		:return:
		"""
		return True

	def plot_tariff(self):
		"""
		This function makes a visualization of a valid tariff data frame and draws it into a canvas in the frame.

		:return: N/A
		"""
		plt.figure(1)
		plt.cla()  # clear the plotting window to allow for re-plotting

		if self.chargetypetoplot.get() == 'energy':
			toplot = []
			energy_filter = ('energy' == self.data["Charge"]) | ('Energy' == self.data["Charge"])
			for mo in range(1, 13):
				month_filter = (mo >= self.data["Start Month"]) & (mo <= self.data["End Month"])
				temp = self.data.loc[(energy_filter & month_filter), :]
				toplot.append([sum(temp.loc[(hr >= temp['Start Time']) & (hr <= temp['End Time']), "Value"])
							   for hr in range(1, 25)])
			im = plt.imshow(toplot, interpolation='nearest')
			plt.xticks(ticks=[i-.5 for i in range(25)],
					   labels=['{}:00'.format(str(j).zfill(2)) for j in range(25)], rotation=45)
			plt.yticks(ticks=[i-0.5 for i in range(13)],
					   labels=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
							   'Aug', 'Sep', 'Oct', 'Nov', 'Dec', ''], va='top')

			# get the colors of the values, according to the
			# colormap used by imshow
			values = np.unique([toplot[i][j] for i in range(12) for j in range(24)])
			colors = [im.cmap(im.norm(value)) for value in values]
			# create a patch (proxy artist) for every color
			patches = [mpatches.Patch(color=colors[i], label="${:1.5}/kWh".format(values[i]))
					   for i in range(len(values))]
			# put those patched as legend-handles into the legend
			plt.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc="upper right", borderaxespad=0.)
			plt.title('Energy Price Heatmap')
		else:
			toplot = []
			demand_filter = ('demand' == self.data["Charge"]) | ('Demand' == self.data["Charge"])
			for mo in range(1, 13):
				month_filter = (mo >= self.data["Start Month"]) & (mo <= self.data["End Month"])
				temp = self.data.loc[(demand_filter & month_filter), :]
				toplot.append([sum(temp.loc[(hr >= temp['Start Time']) & (hr <= temp['End Time']), "Value"]) for hr in
							   range(1, 25)])
			im = plt.imshow(toplot, interpolation='nearest')
			plt.xticks(ticks=[i - .5 for i in range(25)], labels=['{}:00'.format(str(j).zfill(2)) for j in range(25)],
					   rotation=45)
			plt.yticks(ticks=[i - 0.5 for i in range(13)],
					   labels=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', ''],
					   va='top')

			# get the colors of the values, according to the
			# colormap used by imshow
			values = np.unique([toplot[i][j] for i in range(12) for j in range(24)])
			colors = [im.cmap(im.norm(value)) for value in values]
			# create a patch (proxy artist) for every color
			patches = [mpatches.Patch(color=colors[i], label="${:1.5}/kW".format(values[i])) for i in
					   range(len(values))]
			# put those patched as legend-handles into the legend
			plt.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc="upper right", borderaxespad=0.)
			plt.title('Demand Price Heatmap')

		self.chart_type.draw()

		return 0

	def dynamicupload(self):
		# appear or disappear check marks
		if self.validate_tariff():
			self.uploadwarning.grid_remove()
			self.uploadchecklabel.grid()
		else:
			self.uploadchecklabel.grid_remove()
			self.uploadwarning.grid()
