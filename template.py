import tkinter as tk
import json

with open('theme.json', 'r') as f:
	theme = json.load(f)


class Template(tk.Frame):
	"""
	This template will be the parent of each dynamic frame. Settings common to each of the dynamic frames should be
	kept here. This includes colors, fonts, sizes, etc.
	"""
	def __init__(self, parent, controller, bd):
		tk.Frame.__init__(self, parent, highlightthickness=bd, highlightbackground=theme['POLBcolor'])
		self.controller = controller
		self.headerfont = ('quicksand', 20, 'bold')

		# Set up Sub-frames consistently
		self.grid_rowconfigure(1, weight=1)
		self.grid_columnconfigure(0, weight=1)

		self.titleframe = tk.Frame(self)
		self.titleframe.grid_columnconfigure(0, weight=1)
		self.titleframe.grid(row=0, column=0, sticky='nsew')

		self.bottomframe = tk.Frame(self)
		self.bottomframe.grid_rowconfigure(0, weight=1)
		self.bottomframe.grid_columnconfigure('all', weight=1)
		self.bottomframe.grid(row=1, column=0, sticky='nsew')

		self.instructionsframe = tk.Frame(self.bottomframe)
		self.instructionsframe.grid_rowconfigure(0, weight=1)
		self.instructionsframe.configure(highlightbackground="black", highlightthickness=2)
		self.instructionsframe.grid(row=0, column=0, sticky='nsew')

		self.controlsframe = tk.Frame(self.bottomframe)

		self.controlsframe.configure(highlightbackground="black", highlightthickness=2)
		self.controlsframe.grid(row=0, column=1, sticky='nsew')

		self.rightframe = tk.Frame(self.bottomframe)
		self.rightframe.configure(highlightbackground="black", highlightthickness=2)
		self.rightframe.grid(row=0, column=2, sticky='nsew')
