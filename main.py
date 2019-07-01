import sys
from collections import defaultdict
from operator import lt, gt, le, ge, eq, ne
from utils import progressbar
import traceback
import struct

files = []

# TODO support glob *.sav, sorted
filepaths = sys.argv[1:]

if len(filepaths) < 2:
	print("Can't compare", len(filepaths))
	exit(1)

for path in filepaths:
	files.append(open(path, "rb"))

data = []
for f in files:
	data.append([])
	while True:
		try: 
			data[-1].append(struct.unpack_from("<H",f.read(4))[0])
		except struct.error:
			break

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
		self.kv = defaultdict(dict)

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
	
	def print(self):
		for k,v in self.kv.items():
			print(k,hex(k),v)
			
	def readall(self):
		print("Readall")
		for di, d in enumerate(data):
			for bi, b in enumerate(d):
				self.kv[bi][di] = b
				#self.kv[bi].append(b)#no space for nonexistent data currently! (e.g. file 1 shorter than 0 and 2)

	def filter(self, fileindices, condition, target):
	
		if len(self.kv) == 0:
			self.readall()
	
		filtered = 0
		nonexistent = 0
		falsecond = 0
		

		for key in list(self.kv.keys()):
			value = self.kv[key]
			for fileindex in fileindices:
				
				delete = False
				if not fileindex in value:
					delete = True
					nonexistent += 1
					
				
				elif not condition(value[fileindex], target):
					delete = True
					falsecond += 1
					
				if delete:
					del self.kv[key]
					filtered += 1
		
		print(f"Filtered: {filtered} (Falsecond: {falsecond} | Nonexistent: {nonexistent})")
			
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
			cmd = cmd[0]
			if cmd in opmap:
				#new, then old
				condition = opmap[cmd]
				self.filecmp(list(range(len(filepaths))), condition)
			elif cmd in "q exit quit".split():
				exit(0)
			elif cmd in "r reset clear".split():
				self.reset()
			elif cmd in "o p print out show".split():
				self.print()
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
			value = int(cmd[2])
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
