#!/usr/bin/env python3

#
# Takes an STM32 CPU Symbol and a CubeMX pinout spreadsheet
# and produces a schematic with the pins labelled.
#
# TODO: Remove any existing label at calculated label position
#       then modify existing schematic to add new label

import sys
from csv import DictReader

OFFSET = 50

class Component:
	def __init__(self, filename, component_name):
		self.filename = filename
		with open(filename) as f:
			lib = f.readlines()
		self.name = component_name
		self.legs = {}
		found = False
		for line in lib:
			line = line.strip()
			if found:
				if line == "ENDDEF":
					break
				elif line.startswith("X"):
					parts = line.split()
					position = (int(parts[3]), int(parts[4]), parts[6])
					self.legs[parts[1]] = position
			elif line.startswith("DEF") and (component_name in line):
				found = True
		if not self.legs:
			raise ValueError("Component {} not found in lib {}".format(component_name, filename))

class Schematic:
	def __init__(self, filename, component_name):
		self.filename = filename
		with open(filename, "r") as f:
			schematic = f.readlines()
		found = False
		for line in schematic:
			if found:
				if line.startswith("P"):
					_, x, y = line.split()
					self.x = int(x)
					self.y = int(y)
					break
			elif line.startswith("L") and (component_name in line):
				found = True
		else:
			raise ValueError("Component {} not found in lib {}".format(component_name, filename))

def main():
	# Such as "<project>-cache.lib"
	component_file = sys.argv[1]
	# Such as STM32F767BGTx
	component_name = sys.argv[2]
	# As exported from CubeMX (without Alt Functions)
	spreadsheet_file = sys.argv[3]
	# This is our input schematic
	schematic_file = sys.argv[4]
	# This is our output schematic
	schematic_out_file = sys.argv[5]

	component = Component(component_file, component_name)
	schematic = Schematic(schematic_file, component_name)

	print("Found CPU at", schematic.x, ",", schematic.y)

	with open(spreadsheet_file, "r") as f:
		pinout_data = DictReader(f)
		for row in pinout_data:
			if row["Signal"]:
				print("> {Name}: '{Signal}' (pin {Position})".format(**row))
				for leg, position in component.legs.items():
					plain_name = row["Name"].split("/")[0]
					if plain_name == leg:
						x = schematic.x + position[0]
						if position[2] == "L":
							x = x + OFFSET
							rotation = 0
						elif position[2] == "R":
							x = x - OFFSET
							rotation = 2
						else:
							raise ValueError("Bad leg position")
						y = schematic.y - position[1]
						print("Mapped {} to {} {}".format(row["Signal"], leg, plain_name)) 
						with open(schematic_out_file, "a") as f:
							f.write("Text Label {} {} {}    50   ~ 0\n".format(x, y, rotation))
							f.write("{}\n".format(row["Signal"]))
						break
				else:
					raise ValueError("Pin {} in spreadsheet not found in component".format(row["Name"]))

	return 0

if __name__ == '__main__':
	sys.exit(main())

