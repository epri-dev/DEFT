import copy
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from template import Template
from themeclasses import *
import tksheet as tks

from report import Report


class Results(Template):
	def __init__(self, parent, controller, bd):
		Template.__init__(self, parent, controller, bd)

		title = pagetitle(self.titleframe, 'Results')
		title.grid(row=0, column=0, sticky='nsew')

		with open('./UI_Text/Results_Instructions.txt', 'r') as _f:  # Read splash screen text from file
			self.resultsinstructiontext = _f.read()
		self.resultsinstructionlabel = instruction_label(self.instructionsframe, self.resultsinstructiontext)
		self.resultsinstructionlabel.grid(row=0, column=0, sticky='nsew')

		self.shortinstructins = tk.Label(self.controlsframe, text='Select what kind of plot to show')
		self.shortinstructins.grid(row=2, column=0)
		self.plottype = tk.StringVar()
		self.plottype.set('Demand')
		self.plotselector = tk.OptionMenu(self.controlsframe, self.plottype, 'Demand', 'Energy', 'Fuel',
										  command=lambda _: self.plotdiverter())
		self.plotselector.grid(row=3, column=0, sticky='nsew')
		self.billts = pd.DataFrame()
		self.bill = pd.DataFrame({'Month': [i for i in range(1, 13)]})
		self.financialsummary = []

		# Set up single results frame
		self.calcinstructions = tk.Label(self.controlsframe, text='Calculate electricity bills')
		self.calcinstructions.grid(row=0, column=0, sticky='nsew')
		self.runbutton = tk.Button(self.controlsframe, text='(Re-)Calculate Monthly Electric Bills',
								   command=lambda: self.calcmonthlybills(controller))
		self.runbutton.grid(row=1, column=0, sticky='nsew')

		self.popupmonthbillbutton = tk.Button(self.controlsframe, text='View tabular electric bill data',
											  command=lambda: self.popuptabularbill())
		self.popupmonthbillbutton.grid(row=4, column=0, sticky='nsew')

		self.popupfinsummary = tk.Button(self.controlsframe, text='View tabular financial summary',
										 command=lambda: self.popuptabularfinancials())
		self.popupfinsummary.grid(row=5, column=0, sticky='nsew')

		self.dervetbutton = tk.Button(self.controlsframe, text='Use DER-VET to Optimize DERs',
									  command=lambda: self.opendervet())
		self.dervetbutton.grid(row=9, column=0, sticky='nsew')

		self.reportbutton = tk.Button(self.controlsframe, text='Generate PDF Report',
									  command=lambda: self.create_report())
		self.reportbutton.grid(row=10, column=0, sticky='nsew')

		# Set up plotting canvas
		self.plotwindow = tk.Frame(self.rightframe)
		self.plotwindow.grid(row=0, column=0)

		self.figure = plt.figure(num=4, figsize=(7, 5), dpi=100)
		self.axes = self.figure.add_subplot(111)
		self.chart_type = FigureCanvasTkAgg(self.figure, self.plotwindow)
		self.toolbar = NavigationToolbar2Tk(self.chart_type, self.plotwindow)
		self.toolbar.update()
		self.chart_type._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

	def create_report(self):
		Report(self.controller)

	def calcmonthlybills(self, controller):
		# print('Calculating Monthly Bill')
		self.billts = self.assignbillingperiods(controller)
		self.billts['Baseline Electric Load (kW)'] = copy.deepcopy(
			controller.frames['Load'].data['Baseline Electric Load (kW)'])
		self.billts['BusyNewLoad'] = copy.deepcopy(controller.frames['Newload'].newload['Busy Day New Load'])
		self.billts['AvgNewLoad'] = copy.deepcopy(controller.frames['Newload'].newload['Average Day New Load'])

		self.billts['Energy Cost'] = self.billts['AvgNewLoad'] * controller.frames['Load'].dt.get() * self.billts['p_energy']
		self.billts['month'] = self.billts['Datetime'].dt.month
		self.bill['Energy Charge'] = self.billts.groupby(['month'])['Energy Cost'].agg(sum).values

		self.billts['Original Energy Cost'] = self.billts['Baseline Electric Load (kW)'] * \
											  controller.frames['Load'].dt.get() * \
											  self.billts['p_energy']
		self.bill['Original Energy Charge'] = self.billts.groupby(['month'])['Original Energy Cost'].agg(sum).values
		# calculate demand charges
		self.bill['Demand Charge'] = 0
		self.bill['Original Demand Charge'] = 0
		for mo in range(1, 13):
			demand_charge = 0
			original_demand_charge = 0
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
				demand = self.billts.loc[billing_per_mask, 'BusyNewLoad'].max()
				demand_charge += demand * controller.frames['Tariff'].data.loc[per, 'Value']
				original_demand = self.billts.loc[billing_per_mask, 'Baseline Electric Load (kW)'].max()
				original_demand_charge += original_demand * controller.frames['Tariff'].data.loc[per, 'Value']
			self.bill.loc[(mo-1), 'Demand Charge'] = demand_charge
			self.bill.loc[(mo-1), 'Original Demand Charge'] = original_demand_charge

		self.plotmonthlybills()

		yearlydcincrease = sum(self.bill['Demand Charge']) - sum(self.bill['Original Demand Charge'])
		yearlyecincrease = sum(self.bill['Energy Charge']) - sum(self.bill['Original Energy Charge'])
		yearlybillincrease = yearlydcincrease + yearlyecincrease
		fuelcostsavings = self.controller.frames['Newload'].fuelandemissions['Fuel (Gallons)'] * \
						  self.controller.parameters['DIESEL_DOLLARS_PER_GALLON']

		self.financialsummary.append(['Yearly Electricity Bill Increase ($)', yearlybillincrease])
		if sum(self.bill['Original Energy Charge']) + sum(self.bill['Original Demand Charge']) > 0:
			self.financialsummary.append(['Yearly Electricity Bill Increase (%)',
										  yearlybillincrease/(sum(self.bill['Original Energy Charge']) +
															  sum(self.bill['Original Demand Charge']))])
		self.financialsummary.append(['Yearly Fuel Cost Savings ($)', fuelcostsavings])
		self.financialsummary.append(['Net Yearly Operating Expense Increase ($)',
									  yearlybillincrease - fuelcostsavings])
		self.financialsummary.append(['Most Expensive Month with ZE Equipment',
									  theme['MONTHNAMES'][(self.bill['Energy Charge'] +
														   self.bill['Demand Charge']).idxmax()]])
		self.financialsummary.append(['Most Expensive Month without ZE Equipment',
									  theme['MONTHNAMES'][(self.bill['Original Energy Charge'] +
														   self.bill['Original Demand Charge']).idxmax()]])

		# self.calcworstpeak()

	def assignbillingperiods(self, controller):
		baselineload = copy.copy(controller.frames['Load'].data)
		baselineload['dayofweek'] = copy.copy(baselineload['Datetime']).dt.dayofweek
		baselineload['weekday'] = 1
		baselineload.loc[(baselineload['dayofweek'] == 5) | (baselineload['dayofweek'] == 6), 'weekday'] = 0
		tariff = controller.frames['Tariff'].data

		billing_period = [[] for _ in range(baselineload.shape[0])]
		output = pd.DataFrame()
		output['Datetime'] = baselineload['Datetime']
		output['p_energy'] = 0

		for p in tariff.index:
			bill = tariff.loc[p, :]
			month_mask = (bill["Start Month"] <= baselineload['Datetime'].dt.month) & \
						 (baselineload['Datetime'].dt.month <= bill["End Month"])
			time_mask = ((bill['Start Time']-1) <= baselineload['Datetime'].dt.hour) & \
						(baselineload['Datetime'].dt.hour <= (bill['End Time']-1))
			weekday_mask = True
			exclud_mask = False
			if not bill['Weekday?'] == 2:  # if not (apply to weekends and weekdays)
				weekday_mask = bill['Weekday?'] == baselineload['weekday']
			if not np.isnan(bill['Excluding Start Time']) and not np.isnan(bill['Excluding End Time']):
				exclud_mask = ((bill['Excluding Start Time']-1) <= baselineload['Datetime'].dt.hour) & \
							  (baselineload['Datetime'].dt.hour <= (bill['Excluding End Time']-1))
			mask = np.array(month_mask & time_mask & np.logical_not(exclud_mask) & weekday_mask)
			if bill['Charge'].lower() == 'energy':
				output.loc[mask, 'p_energy'] += bill['Value']
			elif bill['Charge'].lower() == 'demand':
				for i, true_false in enumerate(mask):
					if true_false:
						billing_period[i].append(p)
		# billing_period = pd.DataFrame({'billing_period': billing_period}, dtype='object')
		output['billing_period'] = billing_period
		return output

	def plotdiverter(self):
		if self.plottype.get() == 'Energy' or self.plottype.get() == 'Demand':
			self.plotmonthlybills()
		elif self.plottype.get() == 'Fuel':
			self.plotfueluse()

	def plotmonthlybills(self):
		plt.figure(4)
		plt.cla()  # Clear the plotting window to allow for re-plotting.

		# Plot the peak day
		if self.plottype.get() == 'Energy':
			plt.bar(x=self.bill['Month'] - (1/6), height=self.bill['Original Energy Charge'], width=1/4,
					label='Original Energy Charge')
			plt.bar(x=self.bill['Month'] + (1/6), height=self.bill['Energy Charge'], width=1/4,
					label='Energy Charge with ZE Equipment')

			plt.title('Energy Charges Before and After ZE Equipment')
			plt.ylabel('Energy Charges ($)')
			plt.xlabel('Month')
			plt.xticks([i for i in range(1, 13)])
		elif self.plottype.get() == 'Demand':
			plt.bar(x=self.bill['Month'] - (1 / 6), height=self.bill['Original Demand Charge'],
					width=1 / 4,
					label='Original Demand Charge')
			plt.bar(x=self.bill['Month'] + (1 / 6), height=self.bill['Demand Charge'],
					width=1 / 4,
					label='Demand Charge with ZE Equipment')

			plt.title('Demand Charges Before and After ZE Equipment')
			plt.ylabel('Demand Charges ($)')
			plt.xlabel('Month')
			plt.legend()
			plt.xticks([i for i in range(1, 13)])
		self.chart_type.draw()
		plt.savefig('Plots/Monthly_Bills.png')

	def plotfueluse(self):
		plt.figure(4)
		plt.cla()

		d = self.controller.frames['Newload'].fuelandemissions
		plt.bar(range(len(d)), list(d.values()), align='center')
		plt.xticks(range(len(d)), list(d.keys()))

		plt.title('Annual Fuel and Emissions Savings')
		plt.ylabel('Quantity Saved')

		self.chart_type.draw()
		plt.savefig('Plots/Fuel_And_Emissions.png')

	def opendervet(self):
		self.controller.show_frame("DERVET")

	def popuptabularbill(self):
		top = tk.Toplevel(self.controller)
		top.title('Monthly Bill Results')

		sheet = tks.Sheet(top, data=self.bill,
							   width=800,
							   height=450,
							   page_up_down_select_row=True,
							   column_width=200,
							   startup_select=(0, 1, "rows"),
							   headers=['Month', 'Energy Charge', 'Original Energy Charge',
										'Demand Charge', 'Original Demand Charge'],
							   set_all_heights_and_widths=True)  # set_all_heights_and_widths = True
		sheet.enable_bindings(("single_select",  # "single_select" or "toggle_select"
									"drag_select",  # enables shift click selection as well
									"column_select",
									"row_select",
									"column_width_resize",
									"double_click_column_resize",
									"arrowkeys",
									"row_height_resize",
									"double_click_row_resize",
									"right_click_popup_menu",
									"rc_select",
									"copy"))
		sheet.grid(row=0, column=0, sticky='nsew')
		sheet.set_column_data(0, values=[i for i in range(1, 13)])
		sheet.set_column_data(1, values=self.bill['Energy Charge'])
		sheet.set_column_data(2, values=self.bill['Original Energy Charge'])
		sheet.set_column_data(3, values=self.bill['Demand Charge'])
		sheet.set_column_data(4, values=self.bill['Original Demand Charge'])

	def popuptabularfinancials(self):
		top = tk.Toplevel(self.controller)
		top.title('Yearly Financial Results')

		sheet = tks.Sheet(top, data=self.financialsummary,
						  width=800,
						  height=450,
						  page_up_down_select_row=True,
						  column_width=200,
						  startup_select=(0, 1, "rows"),
						  set_all_heights_and_widths=True)  # set_all_heights_and_widths = True
		sheet.enable_bindings(("single_select",  # "single_select" or "toggle_select"
							   "drag_select",  # enables shift click selection as well
							   "column_select",
							   "row_select",
							   "column_width_resize",
							   "double_click_column_resize",
							   "arrowkeys",
							   "row_height_resize",
							   "double_click_row_resize",
							   "right_click_popup_menu",
							   "rc_select",
							   "copy"))
		sheet.grid(row=0, column=0, sticky='nsew')
		r = 0
		for row in self.financialsummary:
			sheet.set_row_data(r, row)
			r += 1

	def calcworstpeak(self):
		selectedspecs = {}
		selected = {key: value for key, value in self.controller.frames['Zeequip'].selected.items()
						 if value is not None}
		avgsched = pd.DataFrame(
			list(map(list, zip(*self.controller.frames['Schedule'].avgsheet.get_sheet_data())))[1:], )
		avgsched.columns = list(map(list, zip(*self.controller.frames['Schedule'].avgsheet.get_sheet_data())))[0]
		avgsched = avgsched.astype(int)
		busysched = pd.DataFrame(
			list(map(list, zip(*self.controller.frames['Schedule'].busysheet.get_sheet_data())))[1:], )
		busysched.columns = list(map(list, zip(*self.controller.frames['Schedule'].busysheet.get_sheet_data())))[0]
		busysched = busysched.astype(int)

		for tech in self.controller.frames['Zeequip'].tech:
			if tech['Name'] in selected.values():
				selectedspecs[tech['Name']] = tech

		peak = max(self.controller.frames['Load'].data['Baseline Electric Load (kW)'])
		for key, value in selectedspecs.items():
			if value['Power Supply'] == 'Grid':
				peak += max(
						max(avgsched[value['Equipment Type']]),
						max(busysched[value['Equipment Type']])) * \
						value['Grid Specs']['Constant_Power']
			else:
				max(
					max(avgsched[value['Equipment Type']]),
					max(busysched[value['Equipment Type']])) * \
				value['Battery Specs']['Charging Power (kW)']
		return peak
