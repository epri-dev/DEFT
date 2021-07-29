import datetime
from fpdf import FPDF
import pandas as pd
from tkinter import filedialog
import os


class Report(FPDF):
	def __init__(self, case):
		super().__init__()
		datatype = [('PDF Files', '*.pdf')]
		self.case = case
		savetofilename = filedialog.asksaveasfile(filetypes=datatype, defaultextension=datatype,
												  initialfile=case.logfilename[:-4] + '.pdf')

		self.case.plot_all()  # Re-make every plot to ensure they are up to date

		self.set_title('Dynamic Energy Forecasting Tool')
		self.coverpage()
		self.schedule_inputs()
		self.tariff_inputs()
		self.load_inputs()
		self.zeequip_inputs()
		self.financial_results()
		self.peak_load_results()
		self.fuel_emissions_results()

		# Save PDF
		self.output(savetofilename.name, 'F')

	def coverpage(self):
		self.add_page()
		self.set_x(10)

		self.ln()
		self.make_title('Dynamic Energy Forecasting Tool Report')
		self.make_header2("Report Generated: " + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
		self.ln()
		self.ln()
		self.make_header1("At A Glance")
		self.make_header2(str(round(
							  max(self.case.frames['Newload'].newload['Busy Day New Load']))) +
						  ' kW: expected peak load with ZE equipment\n(an increase of ' + str(round(
							  max(self.case.frames['Newload'].newload['Busy Day New Load']) -
							  max(self.case.frames['Load'].data['Baseline Electric Load (kW)'])
						  )) +
						  ' kW or ' + str(round((max(self.case.frames['Newload'].newload['Busy Day New Load']) -
							  max(self.case.frames['Load'].data['Baseline Electric Load (kW)'])) /
											   max(self.case.frames['Load'].data['Baseline Electric Load (kW)']) * 100)) +
						  '%')
		self.make_paragraph('Worst-case peak with all equipment consuming power during baseline peak: ' +\
							' ' + str(self.case.frames['Results'].calcworstpeak()) + ' kW')
		if 'New Load Peak Day.png' in os.listdir('Plots'):
			self.image('Plots/New Load Peak Day.png', w=160)
		self.make_header2('$' + "{:,}".format(round(self.case.frames['Results'].financialsummary[0][1])) +
			': Yearly Electric Utility Bill Increase, Expected (' +
						  str(round(self.case.frames['Results'].financialsummary[1][1], 2)) + '%)')
		self.make_header2('$' + "{:,}".format(round(self.case.frames['Results'].financialsummary[2][1])) +
			': Expected yearly fuel cost savings')
		self.make_header2('The following yearly fuel and emissions savings are expected:')
		self.make_table_fuelemissions(self.case.frames['Newload'].fuelandemissions)

		selectedspecs = {}
		for tech in self.case.frames['Zeequip'].tech:
			if tech['Name'] in self.case.frames['Zeequip'].selected.values():
				selectedspecs[tech['Name']] = tech
		avgsched = pd.DataFrame(
			list(map(list, zip(*self.case.frames['Schedule'].avgsheet.get_sheet_data())))[1:], )
		avgsched.columns = list(map(list, zip(*self.case.frames['Schedule'].avgsheet.get_sheet_data())))[0]
		avgsched = avgsched.astype(int)
		busysched = pd.DataFrame(
			list(map(list, zip(*self.case.frames['Schedule'].busysheet.get_sheet_data())))[1:], )
		busysched.columns = list(map(list, zip(*self.case.frames['Schedule'].busysheet.get_sheet_data())))[0]
		busysched = busysched.astype(int)

		self.make_header2('ZE Equipment Selection:')
		pstring = ''
		for tech in selectedspecs.values():
			pstring += tech['Equipment Type'] + ': ' + tech['Name'] + ' (' + tech['Power Supply'] + ')' + '(x'+str(
				max(
					max(avgsched[tech['Equipment Type']]),
					max(busysched[tech['Equipment Type']]))
			)+')\n'
		self.make_paragraph(pstring)

		if self.case.frames['Newload'].durabilitywarning.get():
			self.make_header2('WARNING: Some Battery Equipment Runs Out of Energy During Operation\nin This Model')

		# Add in summary details/plots here
	def schedule_inputs(self):
		self.add_page()
		self.set_x(10)
		self.make_header1('Inputs')

		# Schedule Inputs
		self.make_header2('Schedule')
		pstring = 'This section displays information on the scheduling inputs used to create this case. '
		pstring += 'In total, an average day will involve the following equipment roster, which represents the number of each type of equipment in operation by hour of the day:\n'
		self.make_paragraph(pstring)
		self.make_table_schedule([['Equipment Type', '00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00',
						  '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
						  '18:00', '19:00', '20:00', '21:00', '22:00', '23:00']] +
						self.case.frames['Schedule'].avgschedulelist)
		self.ln()
		pstring = 'A busy day will involve:'
		self.make_paragraph(pstring)
		self.make_table_schedule([['Equipment Type', '00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00',
						  '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
						  '18:00', '19:00', '20:00', '21:00', '22:00', '23:00']] +
						self.case.frames['Schedule'].busyschedulelist)

	def tariff_inputs(self):
		# Tariff Inputs
		self.make_header2('Tariff')
		pstring = 'This case used a tariff called ' + self.case.frames['Tariff'].filename[(len(os.getcwd())+9):-4] +\
				  '.\n'
		self.make_paragraph(pstring)
		if 'Tariff_Energy.png' in os.listdir('Plots'):
			pstring = 'A heatmap of the tariff\'s time of day energy rates is shown below.'
			self.make_paragraph(pstring)
			self.image('Plots/Tariff_Energy.png', w=160)
		if 'Tariff_Demand.png' in os.listdir('Plots'):
			pstring = 'A heatmap of the tariff\'s time of day demand rates is shown below. When demand charges overlap, as in the case of an all-hours facility demand charge and an on-peak energy charge, the demand rates are added together for this plot.'
			self.make_paragraph(pstring)
			self.image('Plots/Tariff_Demand.png', w=160)

	def load_inputs(self):
		self.make_header2('Baseline Electric Load')
		with open('./UI_Text/PDF_Baseline_Descripgion.txt', 'r') as f:  # Read splash screen text from file
			pstring = f.read()
		self.make_paragraph(pstring)
		if 'Baseline_Load.png' in os.listdir('Plots'):
			self.image('Plots/Baseline_Load.png', w=160)

	def zeequip_inputs(self):
		self.make_header2('Zero Emissions Equipment Selection')
		selectedspecs = {}
		for tech in self.case.frames['Zeequip'].tech:
			if tech['Name'] in self.case.frames['Zeequip'].selected.values():
				selectedspecs[tech['Name']] = tech
		avgsched = pd.DataFrame(
			list(map(list, zip(*self.case.frames['Schedule'].avgsheet.get_sheet_data())))[1:], )
		avgsched.columns = list(map(list, zip(*self.case.frames['Schedule'].avgsheet.get_sheet_data())))[0]
		avgsched = avgsched.astype(int)
		busysched = pd.DataFrame(
			list(map(list, zip(*self.case.frames['Schedule'].busysheet.get_sheet_data())))[1:], )
		busysched.columns = list(map(list, zip(*self.case.frames['Schedule'].busysheet.get_sheet_data())))[0]
		busysched = busysched.astype(int)

		pstring = 'Below is a list of all zero-emissions equipment alternatives selected to replace fueled equipment.\n'
		for tech in selectedspecs.values():
			pstring += tech['Equipment Type'] + ': ' + tech['Name'] + ' (' + tech['Power Supply']+'(x'+str(
				max(
					max(avgsched[tech['Equipment Type']]),
					max(busysched[tech['Equipment Type']]))
			)+')\n'
		self.make_paragraph(pstring)

	def financial_results(self):
		self.add_page()
		self.set_x(10)
		self.make_header1('Results')
		self.make_header2('Financial Results')
		self.make_table_finsummary(self.case.frames['Results'].financialsummary)
		if 'Monthly_Demand_Bills.png' in os.listdir('Plots'):
			self.make_paragraph(
				'The plot below shows the monthly demand charges before and after the new ZE equipemnt.')
			self.image('Plots/Monthly_Demand_Bills.png', w=160)
		if 'Monthly_Demand_Bills.png' in os.listdir('Plots'):
			self.make_paragraph(
				'The plot below shows the monthly energy charges before and after the new ZE equipemnt.')
			self.image('Plots/Monthly_Energy_Bills.png', w=160)
		self.make_table_bills(self.case.frames['Results'].bill)

	def peak_load_results(self):
		self.make_header2('Peak Electric Load Changes')
		pstring = 'Original Peak Load: ' + str(round(max(
			self.case.frames['Load'].data['Baseline Electric Load (kW)'])))
		pstring += ' kW\nNew Peak Load: ' + str(round(max(
			self.case.frames['Newload'].newload['Busy Day New Load']))) + ' kW'
		self.make_paragraph(pstring)

		if 'New Average Load.png' in os.listdir('Plots'):
			self.image('Plots/New Average Load.png', w=160)

		if 'New Busy Load.png' in os.listdir('Plots'):
			self.image('Plots/New Busy Load.png', w=160)

	def fuel_emissions_results(self):
		self.make_header2('Fuel Use Reduction and Emissions Savings')
		if 'Fuel Use and Emissions.png' in os.listdir('Plots'):
			self.image('Plots/Fuel Use and Emissions.png', w=160)
		self.make_table_fuelemissions(self.case.frames['Newload'].fuelandemissions)

	def header(self):
		ypos = self.get_y()
		self.image('Images/Logos_highres.png', h=10)
		self.set_y(ypos)
		self.set_x(-25)
		self.image('Images/DEFT_Logo2.png', h=10)

	def make_title(self, text):
		self.set_font('Arial', 'B', 28)
		self.cell(40, 10, text, border=0, ln=1, align='L', fill=False)

	def make_header1(self, text):
		self.set_font('Arial', 'B', 16)
		self.cell(40, 10, '\n'+text, border=0, ln=1, align='L', fill=False)

	def make_header2(self, text):
		self.set_font('Arial', 'B', 14)
		self.cell(40, 10, text, border=0, ln=1, align='L', fill=False)

	def make_paragraph(self, text):
		self.set_font('Arial', style='', size=12)
		self.multi_cell(0, 5, text, border=0, align='L', fill=False)
		self.ln()

	def make_table_schedule(self, data):
		self.set_font('Arial', '', 8)
		epw = self.w - 2 * self.l_margin  # effective page width
		epw = epw - 14*self.font_size
		col_width = epw / (len(data[0])-1)
		th = self.font_size

		self.cell(14 * self.font_size, th, "", border=1)
		self.cell(2*col_width, th, "Hour:", border=1)
		self.ln(th)

		row_counter = 0
		for row in data:
			col_counter = 0
			for datum in row:
				if row_counter == 0:
					self.set_font('Arial', 'B', 8)
				else:
					self.set_font('Arial', '', 8)
				if col_counter == 0:
					self.cell(14 * self.font_size, th, str(datum), border=1)
				elif col_counter != 0 and row_counter == 0:
					self.cell(col_width, th, str(datum)[0:2], border=1)
				else:
					self.cell(col_width, th, str(datum), border=1)
				col_counter += 1
			row_counter += 1
			self.ln(th)

	def make_table_finsummary(self, data):
		self.set_font('Arial', '', 8)
		epw = self.w - 2 * self.l_margin  # effective page width
		col_width = epw / 3  # (len(data[0]) - 1)
		th = self.font_size
		for row in data:
			col_counter = 0
			for datum in row:
				if col_counter == 0:
					self.set_font('Arial', 'B', 8)
				else:
					self.set_font('Arial', '', 8)
				if isinstance(datum, float) or isinstance(datum, int):
					self.cell(col_width, th, "{:,}".format(round(datum, 3)), border=1)
				else:
					self.cell(col_width, th, str(datum), border=1)
			self.ln(th)

	def make_table_bills(self, data):
		self.set_font('Arial', '', 8)
		epw = self.w - 2 * self.l_margin  # effective page width
		col_width = epw / 5
		th = self.font_size
		headers = data.columns.tolist()
		data = [headers] + data.values.tolist()
		row_counter = 0
		for row in data:
			col_counter = 0
			if row_counter == 0:
				self.set_font('Arial', 'B', 8)
			else:
				self.set_font('Arial', '', 8)
			for datum in row:
				if col_counter == 0 or row_counter == 0:
					self.cell(col_width, th, str(datum), border=1)
				else:
					self.cell(col_width, th, "$"+"{:,}".format(round(float(datum))), border=1)
				col_counter += 1
			row_counter += 1
			self.ln(th)

	def make_table_fuelemissions(self, data):
		self.set_font('Arial', '', 8)
		epw = self.w - 2 * self.l_margin  # effective page width
		col_width = epw / 5
		th = self.font_size

		for key, value in data.items():
			self.set_font('Arial', 'B', 8)
			self.cell(col_width, th, str(key), border=1)
			self.set_font('Arial', '', 8)
			self.cell(col_width, th, "{:,}".format(round(value)), border=1)
			self.ln(th)
