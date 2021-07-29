from template import Template
from themeclasses import *

with open('theme.json', 'r') as f:
	theme = json.load(f)


class Splash(Template):
	"""
	The splash page is the first page the user sees after opening the DEFT. This page contains a written description
	of the tool and instructions for getting started.
	"""
	def __init__(self, parent, controller, bd):
		Template.__init__(self, parent, controller, bd)

		title = pagetitle(self.titleframe, 'Disclaimer')
		title.grid(row=0, column=0, sticky='nsew')

		with open('./UI_Text/Splash.txt', 'r') as _f:  # Read splash screen text from file
			splashtext = _f.read()

		label = tk.Label(self.bottomframe, text=splashtext, justify='left')
		label.grid(row=0, column=0, sticky='w')

		acceptbutton = tk.Button(self.bottomframe, text='Accept', command=self.activate, height=5, width=10,
								 font=('Arial 20 bold'), bd=5)
		acceptbutton.grid(row=1, column=0, sticky='n')

	def activate(self):
		self.controller.frames['Navbar'].gotoschedule.configure(state='normal')
		self.controller.frames['Navbar'].gototariff.configure(state='normal')
		self.controller.frames['Navbar'].gotoload.configure(state='normal')
		self.controller.frames['Navbar'].gotozeequip.configure(state='normal')
		self.controller.frames['Navbar'].gotonewload.configure(state='normal')
		self.controller.frames['Navbar'].gotoresults.configure(state='normal')
		self.controller.frames['Title'].savebutton.configure(state="normal")
		self.controller.frames['Title'].loadbutton.configure(state="normal")
		self.controller.frames['Title'].exportbutton.configure(state="normal")

		self.controller.show_frame('Schedule')

		self.controller.writetolog('About Text Accepted')
