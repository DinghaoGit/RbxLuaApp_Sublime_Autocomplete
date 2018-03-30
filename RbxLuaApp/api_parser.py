import sys
if sys.version_info >= (3,0):
	from urllib.request import urlopen
else:
	from urllib import urlopen
import re
from RbxLuaApp.extra_tags import apply_extra_tags
from RbxLuaApp.extra_entries import extra_entries

API_URL = r"http://anaminus.github.io/rbx/raw/api/latest.txt"
API_REGEX = re.compile(r"^\s*(\w+) (\w+)[ \.]?(\w*)[ \.:]*(\w*)(.*)")
TAG_REGEX = re.compile(r"\[(\w+)\]")
API_TAG_FILTERS = [ "hidden", "deprecated", "RobloxScriptSecurity", "RobloxScriptSecurity" ]

cur_class = None

def parse_dump_line(line):
	"""
	Parses a line from the API dump.
	"""
	match = API_REGEX.match(line)
	line_type = match.group(1)
	remainder = match.group(5)
	tags = TAG_REGEX.findall(remainder)

	entry = {}
	entry["entry_type"] = line_type
	entry["entry_tags"] = tags

	if "deprecated" in tags:
		return None

	global cur_class

	if line_type == "Class":
		cur_class = match.group(2)
		entry["class_name"] = cur_class
		entry["entry_completion"] = ( match.group(2), match.group(2) )
	elif line_type == "Property":
		entry["class_name"] = cur_class
		entry["entry_completion"] = ( match.group(4) + "\t" + cur_class, match.group(4) )
	elif line_type == "Function" or line_type == "YieldFunction" or line_type == "Callback":
		entry["class_name"] = cur_class
		entry["entry_completion"] = ( match.group(4) + "()\t" + cur_class, match.group(4) + "${1:" + match.group(5) + "}" )
	elif line_type == "Event":
		entry["class_name"] = cur_class
		entry["entry_completion"] = ( match.group(3) + "\tEvent " + cur_class, match.group(3) + "${1::connect(function" + match.group(5) + "\n\t\nend)}")
	elif line_type == "Enum":
		entry["entry_completion"] = ( match.group(2) + "\tEnum", match.group(2) )
		#entry["entry_full_completion"] = "Enum.{0}".format(match.group(2))
	elif line_type == "EnumItem":
		entry["entry_completion"] = ( match.group(3) + "\tEnumItem", match.group(3) )
		entry["enum_parent"] = match.group(2)
		#entry["entry_full_completion"] = "Enum.{0}.{1}".format(match.group(2), match.group(3))

	return apply_extra_tags(entry)

def parse_api_dump():
	"""
	Fetches and parses the API dump from the server.
	"""
	raw_data = urlopen(API_URL)
	entries = []

	for line in raw_data:
		entry = parse_dump_line(line.decode())
		if entry is not None:
			entries.append(entry)

	return (entries + extra_entries)

