import tkinter as tk
import json

with open('theme.json', 'r') as f:
	theme = json.load(f)


class instruction_label(tk.Label):
	"""Class for holding all instruction labels"""
	def __init__(self, parentframe, text):
		wraplength = 200
		# Borderwidth = 2
		justify = 'left'
		title = "Instructions:"
		text = title + '\n\n'+text
		padx = 10
		pady = 10
		super().__init__(parentframe, text=text, wraplength=wraplength, justify=justify, padx=padx,
						 anchor='nw', pady=pady)

class pagetitle(tk.Label):
	"""Class to design page titles"""
	def __init__(self, parentframe, title):
		super().__init__(parentframe, text=title, font=theme['subtitlefont'], justify='center',
					 bg=theme['POLBcolor'], fg=theme['POLBcolordark'])
