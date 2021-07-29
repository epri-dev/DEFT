
from helper_functions import *
from template import Template
from themeclasses import *


class ZESpec(Template):
	def __init__(self, parent, controller, bd):
		Template.__init__(self, parent, controller, bd)

		tonly = (self.register(textonly), '%S')
		nonly = (self.register(numonly), '%S')

		title = pagetitle(self.titleframe, 'Create New Technology Option')
		title.grid(row=0, column=0, sticky='nsew')

		with open('./UI_Text/AddZETechInstructions.txt', 'r') as _f:  # Read splash screen text from file
			instructiontext = _f.read()
		self.instructions = instruction_label(self.instructionsframe, instructiontext)
		self.instructions.grid(row=0, column=0, sticky='nsew')

		# Help Text and Check Box Images
		self.namecheck = tk.PhotoImage(file='./Images/check.png', )
		self.namechecklabel = tk.Label(self.rightframe, image=self.namecheck)
		self.namechecklabel.image = self.namecheck
		self.namechecklabel.grid(row=1, column=3)
		self.namewarning = tk.Label(self.rightframe, text='Enter the equipment make and model')
		self.namewarning.grid(row=1, column=3)

		self.etypecheck = tk.PhotoImage(file='./Images/check.png', )
		self.etypechecklabel = tk.Label(self.rightframe, image=self.etypecheck)
		self.etypechecklabel.image = self.etypecheck
		self.etypechecklabel.grid(row=2, column=3)
		self.etypechecklabel.grid_remove()
		self.etypewarning = tk.Label(self.rightframe, text='Enter the equipment type')
		self.etypewarning.grid(row=2, column=3)

		self.ptypecheck = tk.PhotoImage(file='./Images/check.png', )
		self.ptypechecklabel = tk.Label(self.rightframe, image=self.ptypecheck)
		self.ptypechecklabel.image = self.ptypecheck
		self.ptypechecklabel.grid(row=3, column=3)
		self.ptypechecklabel.grid_remove()
		self.ptypewarning = tk.Label(self.rightframe, text='Enter how the equipment is powered')
		self.ptypewarning.grid(row=3, column=3)

		self.durcheck = tk.PhotoImage(file='./Images/check.png', )
		self.durchecklabel = tk.Label(self.rightframe, image=self.durcheck)
		self.durchecklabel.image = self.durcheck
		self.durchecklabel.grid(row=4, column=3)
		self.durwarning = tk.Label(self.rightframe, text='Enter the maximum operating hours on one charge')
		self.durwarning.grid(row=4, column=3)

		self.ctimecheck = tk.PhotoImage(file='./Images/check.png', )
		self.ctimechecklabel = tk.Label(self.rightframe, image=self.ctimecheck)
		self.ctimechecklabel.image = self.ctimecheck
		self.ctimechecklabel.grid(row=5, column=3)
		self.ctimewarning = tk.Label(self.rightframe, text='Enter the time it takes to fully charge')
		self.ctimewarning.grid(row=5, column=3)

		self.cpowercheck = tk.PhotoImage(file='./Images/check.png', )
		self.cpowerchecklabel = tk.Label(self.rightframe, image=self.cpowercheck)
		self.cpowerchecklabel.image = self.cpowercheck
		self.cpowerchecklabel.grid(row=6, column=3)
		self.cpowerwarning = tk.Label(self.rightframe, text='Enter continuous charging power')
		self.cpowerwarning.grid(row=6, column=3)

		self.gridpowercheck = tk.PhotoImage(file='./Images/check.png', )
		self.gridpowerchecklabel = tk.Label(self.rightframe, image=self.gridpowercheck)
		self.gridpowerchecklabel.image = self.gridpowercheck
		self.gridpowerchecklabel.grid(row=7, column=3)
		self.gridpowerwarning = tk.Label(self.rightframe, text='Enter continuous drid power draw')
		self.gridpowerwarning.grid(row=7, column=3)

		self.saveclose = tk.Button(self.rightframe, text='Save and Return', command=lambda: self.saveandclose(controller))
		self.saveclose.grid(row=8, column=3)
		self.saveclose.configure(state='disabled')

		colwidth = 20
		self.name = tk.StringVar()
		self.name.trace_add('write', self.dynamicname)
		self.namelabel = tk.Label(self.rightframe, text='Name:')
		self.namelabel.config(width=colwidth)
		self.nameinput = tk.Entry(self.rightframe, textvariable=self.name, validate='key', validatecommand=tonly)
		self.nameinput.config(width=colwidth)

		self.equiptype = tk.StringVar()
		self.equiplabel = tk.Label(self.rightframe, text='Equipment Type:')
		self.equipinput = tk.OptionMenu(self.rightframe, self.equiptype, *controller.frames['Zeequip'].Fueled_List,
										command=lambda _: self.dynamictype())

		self.powertype = tk.StringVar()
		self.powerlabel = tk.Label(self.rightframe, text='Power Supply:')
		self.powerinput = tk.OptionMenu(self.rightframe, self.powertype, 'Battery', 'Grid',
										command=lambda _: self.dynamicgui())

		self.durability = tk.DoubleVar()
		self.durability.trace_add('write', self.dynamicdur)
		self.durability.set(0)
		self.durabilitylabel = tk.Label(self.rightframe, text='Max Operational Hours:')
		self.durabilitylabel.config(width=colwidth)
		self.durabilityinput = tk.Entry(self.rightframe, textvariable=self.durability, validate='key',
										validatecommand=nonly)
		self.durabilityinput.config(width=colwidth)

		self.chargingtime = tk.DoubleVar()
		self.chargingtime.trace_add('write', self.dynamicctime)
		self.chargingtime.set(0)
		self.chargelabel = tk.Label(self.rightframe, text='Time to fully charge:')
		self.chargelabel.config(width=colwidth)
		self.chargetimeinput = tk.Entry(self.rightframe, textvariable=self.chargingtime, validate='key',
										validatecommand=nonly)
		self.chargetimeinput.config(width=colwidth)

		self.chargepower = tk.DoubleVar()
		self.chargepower.trace_add('write', self.dynamiccpower)
		self.chargepower.set(0)
		self.chargepowerlabel = tk.Label(self.rightframe, text='Charging Power (kW):')
		self.chargepowerlabel.config(width=colwidth)
		self.chargepowerinput = tk.Entry(self.rightframe, textvariable=self.chargepower, validate='key',
										 validatecommand=nonly)
		self.chargepowerinput.config(width=colwidth)

		self.gridpower = tk.DoubleVar()
		self.gridpower.trace_add('write', self.dynamicgpower)
		self.gridpower.set(0)
		self.gridlabel = tk.Label(self.rightframe, text='Grid Power Use:')
		self.gridlabel.config(width=colwidth)
		self.gridpowerinput = tk.Entry(self.rightframe, textvariable=self.gridpower, validate='key',
									   validatecommand=nonly)
		self.gridpowerinput.config(width=colwidth)

		self.namelabel.grid(row=1, column=1)
		self.nameinput.grid(row=1, column=2)
		self.equiplabel.grid(row=2, column=1)
		self.equipinput.grid(row=2, column=2)
		self.powerlabel.grid(row=3, column=1)
		self.powerinput.grid(row=3, column=2)
		self.durabilitylabel.grid(row=4, column=1)
		self.durabilityinput.grid(row=4, column=2)
		self.chargelabel.grid(row=5, column=1)
		self.chargetimeinput.grid(row=5, column=2)
		self.chargepowerlabel.grid(row=6, column=1)
		self.chargepowerinput.grid(row=6, column=2)
		self.gridlabel.grid(row=7, column=1)
		self.gridpowerinput.grid(row=7, column=2)
		self.dynamicgui()

	def enablesave(self):
		self.saveclose.configure(state='normal')

	def saveandclose(self, controller):
		string = '{\n'
		string += "  \"Name\": \"" + self.name.get() + '\",\n'
		string += "  \"Equipment Type\": \"" + self.equiptype.get() + '\",\n'
		string += "  \"Power Supply\": \"" + self.powertype.get() + '\",\n'
		string += "  \"Battery Specs\": {\n"
		if self.powertype.get() == 'Grid':
			string += "    \"Durability (hrs)\": null,\n"
			string += "    \"Charging Time\": null,\n"
			string += "    \"Charging Power (kW)\": null\n  },\n"
			string += "  \"Grid Specs\": {\n"
			string += "    \"Constant_Power\":" + str(self.gridpower.get()) + "\n  }\n}"

		else:
			string += "    \"Durability (hrs)\":" + str(self.durability.get()) + ',\n'
			string += "    \"Charging Time\":" + str(self.chargingtime.get()) + ',\n'
			string += "    \"Charging Power (kW)\":" + str(self.chargepower.get()) + "\n  },\n"
			string += "  \"Grid Specs\": {\n"
			string += "    \"Constant_Power\": null" + "\n  }\n}"

		with open('./ZE_Equipment/' + self.name.get() + '.json', 'w') as _f:
			_f.write(string)
		controller.show_frame("Zeequip")
		controller.frames['Zeequip'].Load_Saved()

	def dynamicgui(self):
		if self.powertype.get() == 'Battery':
			self.gridlabel.grid_remove()
			self.gridpowerinput.grid_remove()
			self.gridpowerwarning.grid_remove()
			self.gridpowerchecklabel.grid_remove()

			self.durabilitylabel.grid()
			self.durabilityinput.grid()
			self.durwarning.grid()
			self.durchecklabel.grid()
			self.chargelabel.grid()
			self.chargetimeinput.grid()
			self.ctimechecklabel.grid()
			self.ctimewarning.grid()
			self.chargepowerlabel.grid()
			self.chargepowerinput.grid()
			self.cpowerchecklabel.grid()
			self.cpowerwarning.grid()

		elif self.powertype.get() == 'Grid':
			self.durabilitylabel.grid_remove()
			self.durabilityinput.grid_remove()
			self.durwarning.grid_remove()
			self.durchecklabel.grid_remove()
			self.chargelabel.grid_remove()
			self.chargetimeinput.grid_remove()
			self.ctimechecklabel.grid_remove()
			self.ctimewarning.grid_remove()
			self.chargepowerlabel.grid_remove()
			self.chargepowerinput.grid_remove()
			self.cpowerchecklabel.grid_remove()
			self.cpowerwarning.grid_remove()
			self.gridlabel.grid()
			self.gridpowerinput.grid()
			self.gridpowerchecklabel.grid()
			self.gridpowerwarning.grid()
		else:
			pass
		self.dynamicptype()

	def dynamicname(self, x, y, z):
		# appear or disappear check marks
		if len(self.name.get()) > 2:
			self.namewarning.grid_remove()
			self.namechecklabel.grid()
		else:
			self.namechecklabel.grid_remove()
			self.namewarning.grid()
		self.enablesave()

	def dynamictype(self):
		# appear or disappear check marks
		if self.equiptype.get() in self.controller.frames['Zeequip'].Fueled_List:
			self.etypewarning.grid_remove()
			self.etypechecklabel.grid()
		else:
			self.etypechecklabel.grid_remove()
			self.etypewarning.grid()
		self.enablesave()

	def dynamicptype(self):
		# appear or disappear check marks
		if self.powertype.get() in ['Grid', 'Battery']:
			self.ptypewarning.grid_remove()
			self.ptypechecklabel.grid()
		else:
			self.ptypechecklabel.grid_remove()
			self.ptypewarning.grid()
		self.enablesave()

	def dynamicdur(self, x, y, z):
		# appear or disappear check marks
		try:
			if self.durability.get() > 0:
				self.durwarning.grid_remove()
				self.durchecklabel.grid()
			else:
				self.durchecklabel.grid_remove()
				self.durwarning.grid()
		finally:
			pass
		self.enablesave()

	def dynamicctime(self, x, y, z):
		try:
			if self.chargingtime.get() > 0:
				self.ctimewarning.grid_remove()
				self.ctimechecklabel.grid()
			else:
				self.ctimechecklabel.grid_remove()
				self.ctimewarning.grid()
		finally:
			pass
		self.enablesave()

	def dynamiccpower(self, x, y, z):
		try:
			if self.chargepower.get() > 0:
				self.cpowerwarning.grid_remove()
				self.cpowerchecklabel.grid()
			else:
				self.cpowerchecklabel.grid_remove()
				self.cpowerwarning.grid()
		finally:
			pass
		self.enablesave()

	def dynamicgpower(self, x, y, z):
		try:
			if self.gridpower.get() > 0:
				self.gridpowerwarning.grid_remove()
				self.gridpowerchecklabel.grid()
			else:
				self.gridpowerchecklabel.grid_remove()
				self.gridpowerwarning.grid()
		finally:
			pass
		self.enablesave()
