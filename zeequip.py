import os
from template import Template
from themeclasses import *


class Zeequip(Template):
	"""
	Manage the data set of zero-emissions equipment. Select from lists of pre-built equipment types, add to the data
	set, remove equipment (delete), edit existing equipment, etc.

	The outcome from this class is a dictionary of selected technologies, mapping those that need replacement
	to the technology option they will be replaced by.
	"""
	def __init__(self, parent, controller, bd):
		Template.__init__(self, parent, controller, bd)

		self.foldername = "./ZE_Equipment"
		self.tech = []
		self.typetodisplay = ''
		self.Fueled_List = self.controller.parameters['Equipment_list']

		self.selected = {}
		for _type in self.Fueled_List:
			self.selected[_type] = None

		title = pagetitle(self.titleframe, 'Zero Emissions Equipment Inputs')
		title.grid(row=0, column=0, sticky='nsew')

		self.controlsframe.grid_rowconfigure(0, weight=1)
		self.controlsframe.grid_rowconfigure(1, weight=1)
		self.buttonsframe = tk.Frame(self.controlsframe)
		self.buttonsframe.grid(row=0, column=0, sticky='nsew')

		self.viewframe = tk.Frame(self.bottomframe)
		self.viewframe.configure(highlightbackground="black", highlightthickness=2)
		self.viewframe.grid(row=0, column=3, sticky='nsew')

		self.addtechframe = tk.Frame(self.controlsframe)
		self.addtechframe.grid(row=1, column=0, sticky='nsew')

		self.notechwarning = tk.Label(self.buttonsframe,
									  text='No technologies are present. Please modify the schedule to include some equipment',
									  wraplength=200)
		self.notechwarning.grid(row=0, column=0, sticky='new')
		self.notechwarning.grid_remove()

		self.addentry = tk.Button(self.addtechframe, text='Add Entry to\nTechnology Database',
								  command=lambda: controller.show_frame("ZESpec"),
								  width=theme['uploadbuttonwidth'], height=theme['uploadbuttonheight'])
		self.addentry.grid(row=0, column=0, sticky='sew')

		self.labels = {}
		self.viewbuttons = {}
		self.selectbuttons = {}
		self.typeselectbuttons = {}

		self.Load_Saved()

		self.techtext = tk.StringVar()
		self.techtext.set('')
		self.techtextlabel = tk.Label(self.viewframe, textvariable=self.techtext)
		self.techtextlabel.grid(row=0, column=0, sticky='nsew')

		with open('./UI_Text/Zeequip_Instructions.txt', 'r') as _f:  # Read splash screen text from file
			self.zeinstructiontext = _f.read()
		self.zeinstructionlabel = instruction_label(parentframe=self.instructionsframe, text=self.zeinstructiontext)
		self.zeinstructionlabel.grid(row=0, column=0, sticky='new')

		self.warnings = tk.StringVar()
		self.warnings.set('')
		self.warningslabel = tk.Label(self.buttonsframe, textvariable=self.warnings, bg='orange red')
		self.warningslabel.grid(row=19, column=0, sticky='sew')

		self.Update_Warnings()
		self.buildanddisplay()

		for key, value in self.labels.items():
			self.labels[key].configure(bg='gainsboro')

	def updatetypebg(self):
		for equiptype in self.typeselectbuttons.keys():
			if self.selected[equiptype] is not None:
				self.typeselectbuttons[equiptype].configure(bg=theme['POLBcolor'])
			else:
				self.typeselectbuttons[equiptype].configure(bg='gainsboro')

	def buildanddisplay(self):
		# Put type selector buttons in controlsframe
		# clear existing buttons
		for value in self.typeselectbuttons.values():
			value.destroy()

		self.typeselectbuttons = {}
		r = 0
		for equiptype in self.controller.frames['Schedule'].equip_types_present:
			self.typeselectbuttons[equiptype] = tk.Button(self.buttonsframe, text=equiptype,
														  command=lambda n=equiptype: self.populatetech(n),
														  width=theme['uploadbuttonwidth'])
			self.typeselectbuttons[equiptype].grid(row=r, column=0, sticky='nsew')
			r = r + 1
		if len(self.typeselectbuttons) == 0:
			self.notechwarning.grid()
		else:
			self.notechwarning.grid_remove()

	def populatetech(self, typetodisplay):
		# Put Tech option lables, view, and select buttons in rightframe
		# remove previous labels and buttons
		for lab in self.labels.values():
			lab.destroy()
		for but in self.viewbuttons.values():
			but.destroy()
		for but in self.selectbuttons.values():
			but.destroy()

		self.labels = {}
		self.viewbuttons = {}
		self.selectbuttons = {}

		r = 0
		for value in self.tech:
			if value['Equipment Type'] == typetodisplay:
				self.labels[value['Name']] = tk.Label(self.rightframe, text=value['Name'])
				self.viewbuttons[value['Name']] = tk.Button(self.rightframe, text='View',
															command=lambda n=value['Name']: self.View_Tech(n))
				self.selectbuttons[value['Name']] = tk.Button(self.rightframe, text='Select',
															  command=lambda n=value['Name']: self.Select_Tech(n))

				self.labels[value['Name']].grid(row=r, column=0)
				self.viewbuttons[value['Name']].grid(row=r, column=1)
				# self.editbuttons[value['Name']].grid(row=r, column=2)
				self.selectbuttons[value['Name']].grid(row=r, column=3)
				r = r + 1

				if self.selected[value['Equipment Type']] == value['Name']:  # If the label is selected, color it blue
					self.labels[value['Name']].configure(bg=theme['POLBcolor'])
				else:
					self.labels[value['Name']].configure(bg='gainsboro')

	def Select_Tech(self, name):
		t = self.tech[0]
		for value in self.tech:
			if value['Name'] == name:
				t = value
		self.selected[t['Equipment Type']] = name

		# re-format labels to indicate which is selected
		for key, value in self.labels.items():
			if key in self.selected.values():
				self.labels[key].configure(bg=theme['POLBcolor'])
			else:
				self.labels[key].configure(bg='gainsboro')

		self.Update_Warnings()
		self.updatetypebg()

	def View_Tech(self, name):
		# fetch the specs of the technology name
		# format tech specs and output to main window
		t = self.tech[0]  # initialize t
		for value in self.tech:  # TODO: fix the case where the name is not found in the list
			if value['Name'] == name:
				t = value
		outtext = ''
		outtext = outtext + 'Name: ' + t['Name'] + '\n'
		outtext = outtext + 'Equipment Type: ' + t['Equipment Type'] + '\n'
		outtext = outtext + 'Lifetime (years): ' + str(t['Lifetime (yrs)']) + '\n'
		outtext = outtext + 'Power Supply: ' + t['Power Supply'] + '\n'
		if t['Power Supply'] == 'Battery':
			outtext = outtext + 'Battery Durability (hrs): ' + str(t['Battery Specs']['Durability (hrs)']) + '\n'
			outtext = outtext + 'Battery Charging Time (hrs): ' + str(t['Battery Specs']['Charging Time']) + '\n'
			outtext = outtext + 'Battery Charging Power (kW): ' + str(t['Battery Specs']['Charging Power (kW)']) + '\n'
		else:
			outtext = outtext + 'Peak Grid Power (kW): ' + str(t['Grid Specs']['Constant_Power']) + '\n'
		outtext = outtext + 'Capital Cost ($/unit): ' + str(t['Cost Specs']['Capital Cost ($/unit)']) + '\n'
		outtext = outtext + 'Yearly Maintenance Cost ($/unit-year): ' + \
				  str(t['Cost Specs']['Yearly Maintenance ($/yr)']) + '\n'

		self.techtext.set(outtext)

	def Edit_Tech(self):
		pass

	def Load_Saved(self):
		self.tech = []
		filenames = os.listdir(self.foldername)
		for t in filenames:
			with open('./ZE_Equipment/' + t) as _f:
				self.tech.append(json.load(_f))

		# Remove all old labels
		if self.labels:
			for key, value in self.labels.items():
				value.destroy()
		if self.viewbuttons:
			for key, value in self.viewbuttons.items():
				value.destroy()

		if self.selectbuttons:
			for key, value in self.selectbuttons.items():
				value.destroy()
		self.labels = {}
		self.viewbuttons = {}

		# add new labels
		self.buildanddisplay()

	def Update_Warnings(self):
		# techstoupdate = {x for x in self.Fueled_List if self.controller.frames['Schedule'].nfueled[x].get() != 0}
		techstoupdate = {x for x in self.controller.frames['Schedule'].equip_types_present}
		techsselected = {x for x, value in self.selected.items() if value is not None}
		techsleft = techstoupdate.difference(techsselected)

		warningtext = ''
		if techsleft:
			warningtext += \
				'The following are present in the list of\nfueled equipment to be replaced, but no ZE alternative is selected:\n'
			self.warningslabel.configure(bg='orange red')
		else:
			self.warningslabel.configure(bg='#F0F0F0')
			pass
		for tech in techsleft:
			warningtext = warningtext + tech + '\n'
			# print(warningtext)
		self.warnings.set(warningtext)
