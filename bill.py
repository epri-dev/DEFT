import copy
from helper_functions import *
import numpy as np
import pandas as pd
from template import Template
from themeclasses import *
import tksheet as tks


class Bill(Template):
	def __init__(self, parent, controller, bd):
		Template.__init__(self, parent, controller, bd)

		title = pagetitle(self.titleframe, 'Utility Bill Input')
		title.grid(row=0, column=0, sticky='nsew')

		with open('UI_Text/Bill_Import_Instructions.txt', 'r') as _f:
			instructions = _f.read()
		self.instructionslabel = instruction_label(self.instructionsframe, instructions)
		self.instructionslabel.grid(row=0, column=0, sticky='nsew')

		self.costlist = []
		self.costs2 = []
		self.sheet = tks.Sheet(self.rightframe, data=[])
		self.template = []
		self.costs = pd.DataFrame()
		self.modelload = pd.DataFrame()

		self.donebutton = tk.Button(self.controlsframe, text='Done Editing Bill Data', command=lambda: self.save_costs(controller))
		self.donebutton.grid(row=0, column=0, sticky='nsew')

	def load_tariff(self):
		# Read Tariff information
		if len(self.costlist) == 0:
			for index, row in self.controller.frames['Tariff'].data.iterrows():
				for mo in range(row['Start Month'], (row['End Month'] + 1)):
					self.costlist.append([mo, row['Name_optional'], 0, row['Billing Period']])
					self.template.append([mo, row['Name_optional'], 0, row['Billing Period']])
				# Template is used for cell value validation and does not change with user interaction
		self.costlist.sort(key=lambda x: x[0])
		self.template.sort(key=lambda x: x[0])
		self.sheet = tks.Sheet(self.rightframe, data=self.costlist,
							   width=800,
							   height=500,
							   page_up_down_select_row=True,
							   column_width=200,
							   startup_select=(0, 1, "rows"),
							   headers=['Month', 'Name', 'Cost ($)', 'Billing Period'])
		self.sheet.enable_bindings(("single_select",  # "single_select" or "toggle_select"
									"drag_select",  # enables shift click selection as well
									"column_drag_and_drop",
									"row_drag_and_drop",
									"column_select",
									"row_select",
									"column_width_resize",
									"double_click_column_resize",
									"arrowkeys",
									"row_height_resize",
									"double_click_row_resize",
									"right_click_popup_menu",
									"rc_select",
									"copy",
									"cut",
									"paste",
									"delete",
									"undo",
									"edit_cell"))
		self.sheet.extra_bindings([("end_edit_cell", self.end_edit_cell)])
		self.sheet.grid(row=0, column=1, sticky='nsew')

	def save_costs(self, controller):
		"""
		Pull and format all data from user bill input
		:return:
		"""
		self.costs = copy.copy(pd.DataFrame(self.costlist))
		self.costs.columns = ['Month', 'Name', 'Cost', 'Billing Period']

		self.calculate_timeseries_load(controller=controller)
		self.controller.show_frame('Load')

	def end_edit_cell(self, event):
		"""
		When a user edits the table, ensure that they only change values they can and validate
		:return:
		"""
		if event[1] != 2:  # Only edit the 3rd column!
			self.sheet.set_cell_data(r=event[0], c=event[1], value=self.template[event[0]][event[1]])

		if event[1] == 2:  # Only allow numbers in the 3rd column
			try:
				self.sheet.set_cell_data(r=event[0], c=event[1],
										 value=float(self.sheet.MT.data_ref[event[0]][event[1]]))
			except ValueError:
				print('You Must input a number')
				self.sheet.set_cell_data(r=event[0], c=event[1], value=0)

	def calculate_timeseries_load(self, controller):
		"""
		Take the bill data and covert it into timeseries data
		:return:
		"""
		# Get energy vs demand charge and the rate into self.costs
		self.costs2 = copy.deepcopy(self.costs.merge(self.controller.frames['Tariff'].data, on=['Billing Period']))
		self.costs2['Cost'] = self.costs2['Cost'].astype(float)

		# Generate time column based on time step, year
		dtstartstring = str(self.controller.frames['Load'].datayear) + '-01-01 00:00:00'
		if isleapyear(self.controller.frames['Load'].datayear):
			self.modelload = pd.DataFrame({'Datetime': pd.date_range(dtstartstring,
																	 periods=8784 / self.controller.frames[
																		 'Load'].dt.get(), freq=dt2freq(
					self.controller.frames['Load'].dt.get()))})
		else:
			self.modelload = pd.DataFrame({'Datetime': pd.date_range(dtstartstring,
																	 periods=8760 / self.controller.frames[
																		 'Load'].dt.get(), freq=dt2freq(
					self.controller.frames['Load'].dt.get()))})
		self.assignenebillingperiods(controller=controller)

		# Calculate no variability energy profile using energy costs alone
		self.costs2['Totalhours'] = 0  # self.modelload['billing_period']
		for rn in range(self.costs2.shape[0]):
			# monthmask = self.modelload['Datetime'].dt.month == self.costs2.loc[rn, 'Month']
			self.costs2.loc[rn, 'Totalhours'] = \
				sum([int(self.modelload.loc[x, 'Billing Period'] == self.costs2.loc[rn, 'Billing Period']) for x in
					 range(self.modelload.shape[0])])
		# self.modelload['Billing Period'] == self.costs2.loc[rn, 'Billing Period'])
		self.costs2['AveragePower'] = (self.costs2['Cost'] / self.costs2['Value']) / self.costs2['Totalhours']
		demandbillingperiods = self.controller.frames['Tariff'].data.loc[self.controller.frames['Tariff'].data.loc[:,
																		 'Charge'] == 'demand', 'Billing Period']
		self.modelload.columns = ['Datetime', 'dayofweek', 'weekday', 'p_energy', 'Billing Period']
		self.modelload['eneonlymodel'] = 0
		self.modelload['Month'] = self.modelload['Datetime'].dt.month
		self.modelload = self.modelload.merge(self.costs2.loc[self.costs2['Charge'] == 'energy', ['Billing Period',
																								  'AveragePower',
																								  'Month']],
											  on=['Billing Period', 'Month'], how='left')
		self.modelload['eneonlymodel'] = self.modelload['AveragePower']

		# Add in demand peak values
		self.assignbillingperiods(controller)  # Change billing period to refer to all billing periods, not just energy
		self.modelload['modelload'] = copy.copy(self.modelload['eneonlymodel'])
		# self.modelload.groupby(['Month','Billing Period']).apply()
		for uniquebp in [list(x) for x in set(tuple(x) for x in self.modelload['Billing Period'])]:
			if any([i in demandbillingperiods for i in uniquebp]):  # If these times contain a demand charge
				# find the billing period of the demand charge that covers fewer hours

				minhours = self.costs2.loc[[i in uniquebp for i in self.costs2['Billing Period']], :]
				minhours = minhours.loc[minhours['Charge'] == 'demand', :]  # keep only demand charges
				minhours = minhours.loc[minhours['Totalhours'] == min(minhours['Totalhours']), :]
				minhoursbp = minhours.iloc[0]['Billing Period']

				for mo in range(1, 13):
					# alternate time steps by multiplying/dividing to preserve average power
					# and match peak power of selected demand charge
					# bpmask = [minhoursbp in self.modelload.loc[i,'Billing Period'] for i in range(self.modelload.shape[0])]
					bpmask = [i == uniquebp for i in self.modelload['Billing Period']]
					monthmask = self.modelload['Datetime'].dt.month == mo
					upmask = [i % 2 == 0 for i in range(len(bpmask))]
					downmask = [i % 2 == 1 for i in range(len(bpmask))]

					# If this month doesn't contain the billing period, pass
					if sum(bpmask * monthmask) == 0:
						continue
					# get current peak
					current_peak = max(self.modelload.loc[bpmask * monthmask, 'eneonlymodel'])
					# calculate expected peak
					newpeak = self.costs2.loc[(self.costs2['Month'] == mo) * (
								self.costs2['Billing Period'] == minhoursbp), 'Cost'] / self.costs2.loc[
								  (self.costs2['Month'] == mo) * (self.costs2['Billing Period'] == minhoursbp), 'Value']
					newpeak = float(newpeak)
					if newpeak <= current_peak:
						print('Demand charge too low - peak below average energy use described by energy charge')

					# Increase some hours
					self.modelload.loc[bpmask * monthmask * upmask, 'modelload'] = newpeak
					# Decrease other hours
					self.modelload.loc[bpmask * monthmask * downmask, 'modelload'] = self.modelload.loc[
																						 bpmask * monthmask * downmask, 'modelload'] - (
																								 newpeak - current_peak)
			else:
				pass  # don't need to do anything for energy-only time steps

		# Save modeled data to the parent object
		self.controller.frames['Load'].data = copy.copy(self.modelload[['Datetime', 'modelload']])
		self.controller.frames['Load'].data.columns = ['Datetime', 'Baseline Electric Load (kW)']

		# Plot!
		controller.frames['Load'].plot_baseline()
		controller.frames['Load'].llwarningupdate(None, None, None)
		controller.show_frame("Load")

	def assignenebillingperiods(self, controller):
		self.modelload['dayofweek'] = self.modelload['Datetime'].dt.dayofweek
		self.modelload['weekday'] = 1
		self.modelload.loc[(self.modelload['dayofweek'] == 5) | (self.modelload['dayofweek'] == 6), 'weekday'] = 0
		tariff = controller.frames['Tariff'].data

		billing_period = [0 for _ in range(self.modelload.shape[0])]
		self.modelload['p_energy'] = 0

		for p in tariff.index:
			bill = tariff.loc[p, :]
			month_mask = (bill["Start Month"] <= self.modelload['Datetime'].dt.month) & (
						self.modelload['Datetime'].dt.month <= bill["End Month"])
			time_mask = ((bill['Start Time'] - 1) <= self.modelload['Datetime'].dt.hour) & (
						self.modelload['Datetime'].dt.hour <= (bill['End Time'] - 1))
			weekday_mask = True
			exclud_mask = False
			if not bill['Weekday?'] == 2:  # if not (apply to weekends and weekdays)
				weekday_mask = bill['Weekday?'] == self.modelload['weekday']
			if not np.isnan(bill['Excluding Start Time']) and not np.isnan(bill['Excluding End Time']):
				exclud_mask = ((bill['Excluding Start Time'] - 1) <= self.modelload['Datetime'].dt.hour) & (
							self.modelload['Datetime'].dt.hour <= (bill['Excluding End Time'] - 1))
			mask = np.array(month_mask & time_mask & np.logical_not(exclud_mask) & weekday_mask)
			if bill['Charge'].lower() == 'energy':
				self.modelload.loc[mask, 'p_energy'] += bill['Value']
				for i, true_false in enumerate(mask):
					if true_false:
						billing_period[i] = p + 1
		# billing_period = pd.DataFrame({'billing_period': billing_period}, dtype='object')
		self.modelload['Billing Period'] = billing_period

	def assignbillingperiods(self, controller):
		tariff = controller.frames['Tariff'].data

		billing_period = [[] for _ in range(self.modelload.shape[0])]

		for p in tariff.index:
			bill = tariff.loc[p, :]
			month_mask = (bill["Start Month"] <= self.modelload['Datetime'].dt.month) & (
						self.modelload['Datetime'].dt.month <= bill["End Month"])
			time_mask = ((bill['Start Time'] - 1) <= self.modelload['Datetime'].dt.hour) & (
						self.modelload['Datetime'].dt.hour <= (bill['End Time'] - 1))
			weekday_mask = True
			exclud_mask = False
			if not bill['Weekday?'] == 2:  # if not (apply to weekends and weekdays)
				weekday_mask = bill['Weekday?'] == self.modelload['weekday']
			if not np.isnan(bill['Excluding Start Time']) and not np.isnan(bill['Excluding End Time']):
				exclud_mask = ((bill['Excluding Start Time'] - 1) <= self.modelload['Datetime'].dt.hour) & (
							self.modelload['Datetime'].dt.hour <= (bill['Excluding End Time'] - 1))
			mask = np.array(month_mask & time_mask & np.logical_not(exclud_mask) & weekday_mask)
			for i, true_false in enumerate(mask):
				if true_false:
					billing_period[i].append(p + 1)
		# billing_period = pd.DataFrame({'billing_period': billing_period}, dtype='object')
		self.modelload['Billing Period'] = billing_period
