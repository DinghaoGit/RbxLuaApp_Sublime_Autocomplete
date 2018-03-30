import sublime, sublime_plugin
import re
from collections import defaultdict
from RbxLuaApp.api_parser import parse_api_dump

CALL_REGEX = re.compile(r"\b(\w+)\s*\(?([\"\'])(\w*)\2?\)?")
ENUM_REGEX = re.compile(r"\bEnum\.(\w*)([\.:]?\w*)")
PROPERTY_REGEX = re.compile(r"\w+\.\w*")
FUNCTION_REGEX = re.compile(r"\w+\:\w*")

service_detections = [ "GetService", "FindService", "getService", "service" ]
creatable_detections = [ "new", "createElement"]
class_detections = [ "FindFirstOfClass" ]

class AutoCompleteProvider(sublime_plugin.EventListener):

	def __init__(self):
		self.classes = []
		self.services = []
		self.creatables = []
		self.properties = []
		self.events = []
		self.functions = []
		self.enum_names = []
		self.enum_items_dict = defaultdict(list)

		completion_items = parse_api_dump()

		for e in completion_items:
			entry_type = e["entry_type"]
			entry_tags = e["entry_tags"]
			entry_completion = e["entry_completion"]

			if "Class" == entry_type:
				if "service" in entry_tags:
					self.services.append(entry_completion)
				elif "notCreatable" not in entry_tags and "deprecated" not in entry_tags and "abstract" not in entry_tags:
					self.creatables.append(entry_completion)
				else:
					self.classes.append(entry_completion)
			elif "Enum" == entry_type:
				self.enum_names.append(entry_completion)
			elif "EnumItem" == entry_type:
				enum_parent = e["enum_parent"]
				if enum_parent is not None:
					self.enum_items_dict[enum_parent].append(entry_completion)
			elif "Property" == entry_type:
				self.properties.append(entry_completion)
			elif "Event" == entry_type:
				self.events.append(entry_completion)
			elif "Function" == entry_type:
				self.functions.append(entry_completion)

	def on_query_completions(self, view, prefix, points):
		for point in points:
			if "source.rbxlua" not in view.scope_name(point):
				return None

			row_col = view.rowcol(point)
			line_region = view.line(point)
			line_text = view.substr(line_region)

			if len(line_text) <= 0:
				continue

			"""
			Call
			"""
			call_match = CALL_REGEX.search(line_text, 0, row_col[1])
			if call_match is not None and call_match.end(0) >= row_col[1]:
				caller_name = call_match.group(1)

				if caller_name in service_detections:
					return (self.services, sublime.INHIBIT_EXPLICIT_COMPLETIONS)
				elif caller_name in creatable_detections:
					return (self.creatables, sublime.INHIBIT_EXPLICIT_COMPLETIONS)
				elif caller_name in class_detections:
					return (self.classes, sublime.INHIBIT_EXPLICIT_COMPLETIONS)

				return None

			"""
			Enum
			"""
			enum_match = ENUM_REGEX.search(line_text, 0, row_col[1])
			if enum_match is not None and enum_match.end(0) >= row_col[1]:
				if enum_match.group(2) is None or enum_match.group(2) == "":
					return (self.enum_names, sublime.INHIBIT_EXPLICIT_COMPLETIONS | sublime.INHIBIT_WORD_COMPLETIONS)
				else:
					if enum_match.group(2)[0] == ".":
						enum_items = self.enum_items_dict[enum_match.group(1)]
						if enum_items is not None:
							return (enum_items, sublime.INHIBIT_EXPLICIT_COMPLETIONS | sublime.INHIBIT_WORD_COMPLETIONS)

				return ([ ["GetEnumItems()", "GetEnumItems()"] ], sublime.INHIBIT_EXPLICIT_COMPLETIONS | sublime.INHIBIT_WORD_COMPLETIONS)

			"""
			Property, Event
			"""
			if prefix[0:1].isupper():
				return (self.properties)
			else:
				match_list = PROPERTY_REGEX.findall(line_text, 0, row_col[1])
				if len(match_list) > 0:
					for m in match_list:
						if m.endswith(prefix) and line_text[row_col[1]-len(prefix)-1] == ".":
							return (self.properties + self.events)
			
			"""
			Function
			"""		
			func_match_list = FUNCTION_REGEX.findall(line_text, 0, row_col[1])
			if len(func_match_list) > 0:
				for m in func_match_list:
					if m.endswith(prefix) and line_text[row_col[1]-len(prefix)-1] == ":":
						return (self.functions)

			return None



