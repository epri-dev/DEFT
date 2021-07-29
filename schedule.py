
import copy
from template import Template
from themeclasses import *
import tksheet as tks


class Schedule(Template):
	"""
	This frame collects inputs about the existing (fueled) equipment that will be replaced with zero emissions
	equipment. This is the first step of establishing equivalency.
	"""
	def __init__(self, parent, controller, bd):
		Template.__init__(self, parent, controller, bd)
		self.Fueled_path = './Fueled.json'

		self.equip_types_present = []

		# Make Page Title
		title = pagetitle(self.titleframe, 'Schedule Inputs')
		title.grid(row=0, column=0, sticky='nsew')

		with open('./UI_Text/Schedule_Instructions.txt', 'r') as _f:  # Read splash screen text from file
			scheduletext = _f.read()
		instructionslabel = instruction_label(parentframe=self.instructionsframe, text=scheduletext)
		instructionslabel.grid(row=0, column=0, sticky='nsew')

		avgtitle = tk.Label(self.rightframe, text='Average Day Schedule', font=theme['subtitlefont'], justify='center')
		avgtitle.grid(row=0, column=0)
		self.avgschedulelist = [[i, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
								for i in self.controller.parameters['Equipment_list']]
		self.template = copy.deepcopy(self.avgschedulelist)
		self.avgsheet = tks.Sheet(self.rightframe, data=self.avgschedulelist,
							   width=1100,
							   height=200,
							   page_up_down_select_row=True,
							   column_width=200,
							   startup_select=(0, 1, "rows"),
							   headers=['Equipment Type', '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
										'06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '13:00',
										'14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00',
										'22:00', '23:00'],
							   set_all_heights_and_widths=True)  # set_all_heights_and_widths = True
		self.avgsheet.enable_bindings(("single_select",  # "single_select" or "toggle_select"
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
		self.avgsheet.extra_bindings([("end_edit_cell", self.end_edit_cell_avg),
									   ("end_paste", self.end_edit_cell_avg)])
		self.avgsheet.grid(row=1, column=0, sticky='nw')

		busytitle = tk.Label(self.rightframe, text='Busy Day Schedule', font=theme['subtitlefont'], justify='center')
		busytitle.grid(row=2, column=0)
		self.busyschedulelist = [[i, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] for i in
								self.controller.parameters['Equipment_list']]
		self.busysheet = tks.Sheet(self.rightframe, data=self.busyschedulelist,
							   width=1100,
							   height=200,
							   page_up_down_select_row=True,
							   column_width=200,
							   startup_select=(0, 1, "rows"),
							   headers=['Equipment Type', '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
										'06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '13:00',
										'14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00',
										'22:00', '23:00'],
							   set_all_heights_and_widths=True)  # set_all_heights_and_widths = True
		self.busysheet.enable_bindings(("single_select",  # "single_select" or "toggle_select"
									"drag_select",  # enables shift click selection as well
									"column_width_resize",
									"double_click_column_resize",
									"arrowkeys",
									"row_height_resize",
									"double_click_row_resize",
									"right_click_popup_menu",
									"copy",
									"paste",
									"delete",
									"undo",
									"edit_cell"))
		self.busysheet.extra_bindings([("end_edit_cell", self.end_edit_cell_busy),
									   ("end_paste", self.end_edit_cell_busy)])
		self.busysheet.grid(row=3, column=0, sticky='nw')

		for row in range(18):
			for col in range(1, 25):
				self.avgsheet.highlight_cells(row=row, column=col, bg="DarkOrange1")
				self.busysheet.highlight_cells(row=row, column=col, bg="DarkOrange1")

	def end_edit_cell_avg(self, event):
		"""
		When a user edits the table, ensure that they only change values they can and validate
		:return:
		"""
		if isinstance(event[1], tuple):
			# validate the entire list
			for row in range(len(self.avgsheet.MT.data_ref)):
				for col in range(len(self.avgsheet.MT.data_ref[row])):
					if col == 0:
						pass
					else:
						try:
							self.avgschedulelist[row][col] = min(self.controller.parameters['MAXIMUM_N'],max(0,int(self.avgsheet.MT.data_ref[row][col])))
						except ValueError:
							self.avgschedulelist[row][col] = 0
			# self.avgschedulelist = copy.deepcopy(self.avgsheet.MT.data_ref)
		else:
			if event[1] == 0:  # Only the value columns and not the hour column
				self.avgsheet.set_cell_data(r=event[0], c=event[1], value=self.template[event[0]][event[1]])
				return 1

			if event[1] > 0:
				try:
					valuetoset = min(self.controller.parameters['MAXIMUM_N'],max(0, int(self.avgsheet.MT.data_ref[event[0]][event[1]]))) if int(
						self.avgsheet.MT.data_ref[event[0]][event[1]]) else 0
					self.avgsheet.set_cell_data(r=event[0], c=event[1],
												value=valuetoset)
					self.avgschedulelist[event[0]][event[1]] = valuetoset
				except ValueError:
					self.avgsheet.set_cell_data(r=event[0], c=event[1], value=0)

		self.clean_data_types()
		self.update_equip_type()
		self.recolor_all_avg('x')

	def end_edit_cell_busy(self, event):
		"""
		When a user edits the table, ensure that they only change values they can and validate
		:return:
		"""
		if isinstance(event[1], tuple):
			for row in range(len(self.busysheet.MT.data_ref)):
				for col in range(len(self.busysheet.MT.data_ref[row])):
					if col == 0:
						pass
					else:
						try:
							self.busyschedulelist[row][col] = min(self.controller.parameters['MAXIMUM_N'],max(0,int(self.busysheet.MT.data_ref[row][col])))
						except ValueError:
							self.busyschedulelist[row][col] = 0
			# self.busyschedulelist = copy.deepcopy(self.busysheet.MT.data_ref)
		else:
			if event[1] == 0:  # Only the value columns and not the hour column
				self.busysheet.set_cell_data(r=event[0], c=event[1], value=self.template[event[0]][event[1]])
				return 1
			if event[1] > 0:
				try:
					valuetoset = min(self.controller.parameters['MAXIMUM_N'],max(0, int(self.busysheet.MT.data_ref[event[0]][event[1]]))) if int(
						self.busysheet.MT.data_ref[event[0]][event[1]]) else 0
					self.busysheet.set_cell_data(r=event[0], c=event[1],
												 value=valuetoset)
					self.busyschedulelist[event[0]][event[1]] = valuetoset
				except ValueError:
					self.busysheet.set_cell_data(r=event[0], c=event[1], value=0)

		self.clean_data_types()
		self.update_equip_type()
		self.recolor_all_busy('x')

	def recolor_all_busy(self, x):
		for i in range(len(self.busyschedulelist)):
			for j in range(1, len(self.busyschedulelist[i])):
				if 1 if int(self.busyschedulelist[i][j]) else 0:
					self.busysheet.highlight_cells(row=i, column=j, bg="DodgerBlue2")
				else:
					self.busysheet.highlight_cells(row=i, column=j, bg="DarkOrange1")

		self.update_equip_type()

	def recolor_all_avg(self, x):
		for i in range(len(self.avgschedulelist)):
			for j in range(1, len(self.avgschedulelist[i])):
				if 1 if int(self.avgschedulelist[i][j]) else 0:
					self.avgsheet.highlight_cells(row=i, column=j, bg="DodgerBlue2")
				else:
					self.avgsheet.highlight_cells(row=i, column=j, bg="DarkOrange1")
		self.update_equip_type()

	def update_equip_type(self):
		self.equip_types_present = []
		for row in self.avgschedulelist:
			if any(row[1:]) and row[0] not in self.equip_types_present:
				self.equip_types_present.append(row[0])
		for row in self.busyschedulelist:
			if any(row[1:]) and row[0] not in self.equip_types_present:
				self.equip_types_present.append(row[0])

	def clean_data_types(self):
		for row in range(len(self.busyschedulelist)):
			for col in range(1, len(self.busyschedulelist)-1):
				self.busyschedulelist[row][col] = int(self.busyschedulelist[row][col])
		for row in range(len(self.avgschedulelist)):
			for col in range(1, len(self.avgschedulelist)-1):
				self.avgschedulelist[row][col] = int(self.avgschedulelist[row][col])
