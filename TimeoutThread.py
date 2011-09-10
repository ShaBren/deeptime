import sys, trace, threading, time

class TimeoutThread( threading.Thread ):

	itsTimeout = 5

	def start( self ):
		self.itsStartTime = time.time()
		self.__run_backup = self.run
		self.run = self.__run_with_trace
		threading.Thread.start( self )

	def __run_with_trace( self ):
		sys.settrace( self.globaltrace )
		self.__run_backup()
		self.run = self.__run_backup

	def globaltrace( self, frame, why, arg ):
		if why == 'call':
			return self.localtrace
		else:
			return None

	def localtrace( self, frame, why, arg ):
		if self.itsStartTime + self.itsTimeout <= time.time():
			if why == 'line':
				raise SystemExit()

		return self.localtrace

	def SetTimeout( self, theTimeout ):
		self.itsTimeout = theTimeout;
