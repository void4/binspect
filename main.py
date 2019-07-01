import sys
from collections import defaultdict
from operator import lt, gt, le, ge, eq, ne
from utils import progressbar
import traceback

files = []

filepaths = sys.argv[1:]

if len(filepaths) < 2:
	print("Can't compare", len(filepaths))
	exit(1)

for path in filepaths:
	files.append(open(path, "rb"))

data = [f.read() for f in files]

opmap = {
	"=":eq,
	"!=":ne,
	">":gt,
	"<":lt,
	"<=":le,
	">=":ge,
}

def getop(op):
	if not op in opmap:
		raise Exception("Unknown operator", op)
	return opmap[op]

class Filter:

	def __init__(self):
		self.reset()
	
	def reset(self):
		print("Reset table")
		self.kv = defaultdict(list)

	def getByte(self, fileindex, byteindex):
			if fileindex==0:
				try:
					previousbyte = data[0][byteindex]
				except IndexError:
					return None
			else:
				if byteindex not in self.kv:
					return None
					
				previousbyte = self.kv[byteindex][-1]
			
			return previousbyte

	def filecmp(self, fileindices, condition):
		
		#self.reset()
		
		for indexno, fileindex in enumerate(fileindices[1:]):# filedata in enumerate(data[1:]):
			print(indexno, fileindex)
			filedata = data[fileindex]
			print(len(filedata))
			if len(self.kv) == 0:
				bytelist = list(enumerate(filedata))
			else:
				bytelist = [(i,b) for i,b in enumerate(filedata) if i in self.kv]
			for byteindex, byte in progressbar(bytelist, filepaths[fileindex]+": ", 40):
				#print("HERE", byteindex)
				previousbyte = self.getByte(fileindices[indexno], byteindex)
				if previousbyte is None:
					#delete
					continue
				
				if condition(byte, previousbyte):
					if fileindex==0:
						self.kv[byteindex].append(previousbyte)
					self.kv[byteindex].append(byte)
				else:
					if fileindex>0:
						if byteindex in self.kv:
							del self.kv[byteindex]
			
			print(len(self.kv))
			
			
	def readall(self):
		print("Readall")
		for d in data:
			for bi, b in enumerate(d):
				self.kv[bi].append(b)#no space for nonexistent data currently! (e.g. file 1 shorter than 0 and 2)

	def filter(self, fileindices, condition, value):
	
		if len(self.kv) == 0:
			self.readall()
	
		filtered = 0
		for key in list(self.kv.keys()):
			value = self.kv[key]
			#BE CAUTIOUS, kv value only includes CHECKED indices, may omit some, like 1 if user just typed 0,2 <
			#FOR NOW, assume user checked all files
			if not condition(value[fileindex], value):
				del self.kv[key]
				filtered += 1
		
		print("Filtered: ", filtered)
			
	def step(self):
		print(len(self.kv))
		cmd = input("$ ")
		
		"""
		use file names for readability? -> but then its not universal, program can't be reused
		index property (value)
		index1 index2 comparison
		ALL comparison
		ALL property
		ANY property
		ANY comparison (?)
		"""
		
		cmd = cmd.split()
		
		if len(cmd) == 0:
			return
		elif len(cmd) == 1:
			if cmd[0] in opmap:
				#new, then old
				condition = opmap[cmd[0]]
				self.filecmp(list(range(len(filepaths))), condition)
			elif cmd[0] in "q exit quit".split():
				exit(0)
			elif cmd[0] == "reset":
				self.reset()
			else:
				raise Exception("Unknown operator", cmd[0])
		elif len(cmd) == 2:
			fileindices = [int(i) for i in cmd[0].split(",")]
			
			if len(fileindices) < 2:
				raise Exception("Not enough file indices", len(fileindices))
			
			condition = getop(cmd[1])
			
			self.filecmp(fileindices, condition)
		
		elif len(cmd) == 3:
			fileindices = [int(i) for i in cmd[0].split(",")]
			condition = getop(cmd[1])
			value = cmd[2]
			self.filter(fileindices, condition, value)
		else:
			raise Exception("Unknown command", cmd)				
		# only at static byteindices right now	
		


flt = Filter()

while True:
	try:
		flt.step()
	except (KeyboardInterrupt, EOFError):
		exit(0)
	except Exception as e:
		print(e)
		print(traceback.format_exc())
