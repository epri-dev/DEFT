import copy
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import pandas as pd
import subprocess
from template import Template
from themeclasses import *
import time


class DERVET(Template):
	def __init__(self, parent, controller, bd):
		Template.__init__(self, parent, controller, bd)

		# bill with baseline, newload, and DER results
		self.bill = pd.DataFrame()
		self.billts = pd.DataFrame()
		self.tsresults = pd.DataFrame()

		# Button to run dervet
		run_dervet = tk.Button(self, text='Run DER-VET', command=lambda: self.rundervet())
		run_dervet.grid(row=0, column=0, sticky='nsew')
		plot_dervetts = tk.Button(self, text='Plot DER-VET Time Series Results', command=lambda: self.plotdervetts())
		plot_dervetts.grid(row=1, column=0, sticky='nsew')
		plot_dervetebill = tk.Button(self, text='Plot DER-VET Energy Bill Results', command=lambda: self.plotdervetbill())
		plot_dervetebill.grid(row=2, column=0, sticky='nsew')
		plot_dervetdbill = tk.Button(self, text='Plot DER-VET Demand Bill Results', command=lambda: self.plotdervetdbill())
		plot_dervetdbill.grid(row=3, column=0, sticky='nsew')

		# Set up plotting canvas
		self.plotwindow = tk.Frame(self)
		self.plotwindow.grid(row=10, column=1)

		self.figure = plt.figure(num=5, figsize=(10, 5), dpi=100)
		self.axes = self.figure.add_subplot(111)
		self.chart_type = FigureCanvasTkAgg(self.figure, self.plotwindow)
		self.toolbar = NavigationToolbar2Tk(self.chart_type, self.plotwindow)
		self.toolbar.update()
		self.chart_type._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

		# Set up text results
		self.textwindow = tk.Frame(self)
		self.textwindow.grid(row=10, column=0)

		self.sizekw = tk.DoubleVar()
		self.sizekw.set(0)
		kwrow = tk.Label(self.textwindow, text='Optimal Battery Size (kW): ', justify='left')
		kwrow.grid(row=0, column=0)
		sizekwlab = tk.Label(self.textwindow, textvariable=self.sizekw, justify='left')
		sizekwlab.grid(row=0, column=1)

		self.sizekwh = tk.DoubleVar()
		self.sizekwh.set(0)
		kwhrow = tk.Label(self.textwindow, text='Optimal Battery Size (kWh): ', justify='left')
		kwhrow.grid(row=1, column=0)
		sizekwhlab = tk.Label(self.textwindow, textvariable=self.sizekwh, justify='left')
		sizekwhlab.grid(row=1, column=1)

		self.sizedur = tk.DoubleVar()
		self.sizedur.set(0)
		durrow = tk.Label(self.textwindow, text='Optimal Battery Duration (hrs): ', justify='left')
		durrow.grid(row=2, column=0)
		sizedurlab = tk.Label(self.textwindow, textvariable=self.sizedur, justify='left')
		sizedurlab.grid(row=2, column=1)

		self.ccost = tk.DoubleVar()
		self.ccost.set(0)
		ccostrow = tk.Label(self.textwindow, text='Estimated Battery Capital Cost ($): ', justify='left')
		ccostrow.grid(row=3, column=0)
		ccostlab = tk.Label(self.textwindow, textvariable=self.ccost, justify='left')
		ccostlab.grid(row=3, column=1)

		self.savings = tk.DoubleVar()
		self.savings.set(0)
		savingsrow = tk.Label(self.textwindow, text='Yearly Savings from battery', justify='left')
		savingsrow.grid(row=4, column=0)
		savingslab = tk.Label(self.textwindow, textvariable=self.savings, justify='left')
		savingslab.grid(row=4, column=1)

	def rundervet(self):
		# detect DER-VET install and stop if not available
		# detect if newload is up to date

		# Edit timeseries
		tstemp = pd.read_csv(self.controller.parameters['DERVET_TIMESERIES_FILENAME'])
		# check if timeseries has the right number of rows
		if self.controller.frames['Load'].data.shape[0] != tstemp.shape[0]:
			print('ERROR: DER-VET time step needs to match DEFT time step.')
			print('DEFT shows ' + str(self.controller.frames['Load'].data.shape[0]) + ' time steps')
			print('DER-VET shows ' + str(tstemp.shape[0]) + ' time steps.')
			print('Please upload a DER-VET time series file with the correct number of rows')
			return 1

		tstemp['Site Load (kW)'] = copy.copy(self.controller.frames['Newload'].newload['Busy Day New Load'])
		tstemp.to_csv(self.controller.parameters['DERVET_TIMESERIES_FILENAME'], index=False)  # save timeseries csv

		# Edit model parameters
		mptemp = pd.read_csv(self.controller.parameters['DERVET_MODEL_PARAMETERS_REFERENCE'])
		mptemp.loc[mptemp['Key'] == 'customer_tariff_filename', 'Optimization Value']\
			= self.controller.frames['Tariff'].filename
		if self.controller.frames['Load'].loadlimit.get() > 0:
			mptemp.loc[mptemp['Key'] == 'max_import', 'Optimization Value'] = \
				-self.controller.frames['Load'].loadlimit.get()
		mptemp.to_csv(self.controller.parameters['DERVET_MODEL_PARAMETERS_FILENAME'])

		print('Starting DER-VET at ' + str(time.time()))
		starttime = time.time()
		subprocess.run(["./dervet/python.exe", "./dervet/dervet/run_DERVET.py",
						self.controller.parameters['DERVET_MODEL_PARAMETERS_FILENAME']])
		print('DER-VET finished at ' + str(time.time()))
		endtime = time.time()
		print('Taking a Total of ' + str(endtime-starttime) + ' seconds')

		self.plotdervetts()

	def plotdervetts(self):
		# read timeseries results
		self.tsresults = pd.read_csv(self.controller.parameters['DERVET_TIMESERIES_RESULTS_FILENAME'])
		plt.figure(5)
		plt.cla()  # Clear the plotting window to allow for re-plotting.

		# Plot the peak day
		plt.step(x=pd.to_datetime(self.tsresults['Start Datetime (hb)'], format='%Y-%m-%d %H:%M:%S'),
				 y=self.tsresults['LOAD: Site Load Original Load (kW)'],
				 where='post', color=theme['batterycolor'], label='New Load with ZE Equipment')
		plt.step(x=pd.to_datetime(self.tsresults['Start Datetime (hb)'], format='%Y-%m-%d %H:%M:%S'),
				 y=self.tsresults['Net Load (kW)'],
				 where='post', color=theme['loadcolor'], label='New Load with ZE Equipment and Battery')
		plt.title('Net Load with and without DERs')
		plt.ylabel('Power (kW)')
		plt.legend()
		# self.axes.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
		self.chart_type.draw()
		plt.savefig('Plots/DER_New_Load.png')
		self.updatetextresults()

	def plotdervetbill(self):
		# Get previous bill information from results class

		if self.controller.frames['Results'].bill.shape[1] < 2:
			try:
				self.controller.frames['Results'].calcmonthlybills(self.controller)
			except ValueError:
				print('There was a problem calculating the original bills')
				return

		self.calcmonthlybilldervet()

		plt.figure(5)
		plt.cla()
		plt.bar(x=self.bill['Month'] - (1 / 5), height=self.bill['Original Energy Charge'], width=1/5,
				label='Original Energy Charge')
		plt.bar(x=self.bill['Month'], height=self.bill['Energy Charge'], width=1/5,
				label='Energy Charge with ZE Equipment')
		plt.bar(x=self.bill['Month'] + (1/5), height=self.bill['DER Energy Charge'], width=1/5,
				label='Energy Charge with ZE Equipment and Battery')

		plt.title('How do DERs Impact Energy Charges?')
		plt.ylabel('Energy Charges ($)')
		plt.xlabel('Month')
		plt.legend()
		plt.xticks([i for i in range(1, 13)])

		self.chart_type.draw()
		plt.savefig('Plots/DER_Monthly_Energy_Bill.png')
		self.updatetextresults()

	def plotdervetdbill(self):
		# Get previous bill information from results class
		if self.controller.frames['Results'].bill.shape[1] < 2:
			print('Need to calculate original bills first on Results page')
			return 1

		self.calcmonthlybilldervet()

		plt.figure(6)
		plt.cla()
		plt.bar(x=self.bill['Month'] - (1 / 5), height=self.bill['Original Demand Charge'], width=1/5,
				label='Original Demand Charge')
		plt.bar(x=self.bill['Month'], height=self.bill['Demand Charge'], width=1/5,
				label='Demand Charge with ZE Equipment')
		plt.bar(x=self.bill['Month'] + (1/5), height=self.bill['DER Demand Charge'], width=1/5,
				label='Demand Charge with ZE Equipment and Battery')

		plt.title('How do DERs Impact Demand Charges?')
		plt.ylabel('Demand Charges ($)')
		plt.xlabel('Month')
		plt.legend()
		plt.xticks([i for i in range(1, 13)])

		self.chart_type.draw()
		plt.savefig('Plots/DER_Monthly_Demand_Bill.png')
		self.updatetextresults()

	def calcmonthlybilldervet(self):
		self.controller.frames['Results'].calcmonthlybills(self.controller)
		self.billts = copy.copy(self.controller.frames['Results'].billts)
		self.bill = copy.copy(self.controller.frames['Results'].bill)

		self.billts['NewNetLoadDER'] = self.tsresults['Net Load (kW)']
		self.billts['DER Energy Cost'] = self.billts['NewNetLoadDER'] * self.controller.frames['Load'].dt.get() * \
										 self.billts['p_energy']

		self.bill['DER Energy Charge'] = self.billts.groupby(['month'])['DER Energy Cost'].agg(sum).values

		# calculate demand charges
		self.bill['DER Demand Charge'] = 0
		for mo in range(1, 13):
			demand_charge = 0
			# array of booleans; true for the selected month (size = subs.size)
			monthly_mask = (self.billts['month'] == mo)

			# unique demand billing periods in the month
			month_billing_periods = set([item for b in self.billts.loc[monthly_mask, 'billing_period'] for item in b])

			# determine the index what has the first True value in the array of booleans
			first_true = min([i for i, x in enumerate(monthly_mask) if x])

			for per in month_billing_periods:
				# Add demand charge calculation for each applicable billing period within the selected month
				billing_per_mask = monthly_mask.copy()

				for i in range(first_true, first_true + sum(monthly_mask)):
					billing_per_mask[i] = billing_per_mask[i] & (per in self.billts.loc[i, 'billing_period'])

				# group demand charges by month
				demand = self.billts.loc[billing_per_mask, 'NewNetLoadDER'].max()
				demand_charge += demand * self.controller.frames['Tariff'].data.loc[per, 'Value']
			self.bill.loc[(mo-1), 'DER Demand Charge'] = demand_charge

	def updatetextresults(self):
		# Get size results from csv
		sizedf = pd.read_csv(self.controller.parameters['DERVET_SIZE_RESULTS_FILENAME'])
		self.sizekw.set(round(sizedf.loc[0, 'Discharge Rating (kW)'], 1))
		self.sizekwh.set(round(sizedf.loc[0, 'Energy Rating (kWh)'], 1))
		self.sizedur.set(round(sizedf.loc[0, 'Duration (hours)'], 2))
		self.ccost.set(round(sizedf.loc[0, 'Capital Cost ($)'] +
							 sizedf.loc[0, 'Capital Cost ($/kWh)']*self.sizekwh.get() +
							 sizedf.loc[0, 'Capital Cost ($/kW)']*self.sizekw.get(), 0))
		self.savings.set(round(sum(self.bill['Energy Charge']) -
							   sum(self.bill['DER Energy Charge']) +
							   sum(self.bill['Demand Charge']) -
							   sum(self.bill['DER Demand Charge'])))
