import socket, string, threading, time, sqlite3, imp, traceback, sys

from os.path import isfile
from collections import deque
from TimeoutThread import TimeoutThread

class ServerConnection:

	itsChannels = []
	itsUsers = {}
	itsModules = {}
	itsHandlers = {}
	itsSendQueue = deque()
	itsCommandPrefix = "+"
	isConnected = False
	itsModuleClasses = {}
	
	def __init__( self, theNetworkID, theDebugFlag ):
		self.itsNetworkID = str( theNetworkID )
		self.itsDebugFlag = theDebugFlag
		
		self.itsDB = sqlite3.connect( "config.db" )
		self.itsDBCursor = self.itsDB.cursor()
		
		self.itsDBCursor.execute( "SELECT * FROM network WHERE network_id=?", self.itsNetworkID )
		aRow = self.itsDBCursor.fetchone()
		
		if not aRow:
			return
		
		self.itsHostname = aRow[1]
		self.itsPort = aRow[2]
		self.itsUsername = aRow[3]
		
		if self.itsDebugFlag:
			self.itsDebugFile = open( "%s.debug" % self.itsHostname, "a" )

		self.Connect()

	def Connect( self ):
		self.isConnected = False

		try:
			self.itsSocket = socket.socket()
			self.itsSocket.connect( ( self.itsHostname, self.itsPort ) )
		
			self.itsSocket.send( "NICK %s\r\n" % self.itsUsername )
			self.itsSocket.send( "USER %s %s PB :%s\r\n" % ( self.itsUsername, self.itsHostname, self.itsHostname ) )
		except:
			self.isConnected = False
			print "Connect to %s on port %s failed.\n" % ( self.itsHostname, self.itsPort )
			return
		
		self.LoadCommands( False )
		
		self.isConnected = True

		try:
			if self.itsSendThread.is_alive():
				self.itsSendThread.join( 1 )
		except:
			pass

		try:
			if self.itsSendThread.is_alive():
				return
		except:
			pass
			
		self.itsSendThread = threading.Thread( target=self.ProcessSendQueue )
		self.itsSendThread.daemon = True
		self.itsSendThread.start()
	
	def LoadCommands( self, theForceFlag ):
		self.itsCommands = {}
		self.itsDBCursor.execute( "SELECT command, required_role FROM command WHERE network=?", self.itsNetworkID )
		
		aFailedImport = []
		
		if theForceFlag:
			self.itsModules = {}
			self.itsHandlers = {}

		for aRow in self.itsDBCursor:
			aCommand = aRow[0]
			
			if aCommand not in self.itsModules:
				try:
					self.itsModules[ aCommand ] = imp.load_source( aCommand, "modules/%s.py" % aCommand )
					#self.itsModuleClasses[ aCommand ] = self.itsModules[ aCommand ].IRCModule( self )
					self.itsCommands[ aRow[0] ] = aRow[1]

					#try:
						#self.itsModules[ aCommand ].Init()
					#except:
						#traceback.print_exc( file=sys.stdout )
				except:
					traceback.print_exc( file=sys.stdout )
					aFailedImport.append( aCommand )
					del self.itsModules[ aCommand ]
		
		if self.isConnected:
			if len( aFailedImport ) == 0:
				self.SendText( "Commands reloaded.", self.itsTarget )
			else:
				self.SendText( "Failed to reload: %s" % ",".join( aFailedImport ), self.itsTarget )

	def RegisterHandler( self, theHandlerType, theHandler ):
		if not self.itsHandlers.has_key( theHandlerType ):
			self.itsHandlers[ theHandlerType ] = []

		self.itsHandlers[ theHandlerType ].append( theHandler )
	
	def AuthenticateUser( self ):
		if self.itsSource != self.itsTarget:
			self.SendText( "%s: What are you, stupid? Authenticate using /msg!" % self.itsSource, self.itsTarget )
			return
		
		if len( self.itsMessageParts ) != 3:
			self.SendText( "Usage: %sauth <username> <password>" % self.itsCommandPrefix, self.itsTarget )
			return
			
		aUsername = self.itsMessageParts[1]
		aPassword = self.itsMessageParts[2]
		
		self.itsDBCursor.execute( "SELECT role FROM user WHERE username=? AND password=? AND network=?", ( aUsername, aPassword, self.itsNetworkID ) )

		aRow = self.itsDBCursor.fetchone()
		
		if aRow:
			self.itsUsers[ self.itsSource ] = int( aRow[0] )
			self.SendText( "Authentication succeeded.", self.itsTarget )
		else:	
			self.SendText( "Authentication failed.", self.itsTarget )
		
	def Listen( self ):
		while self.isConnected:
			aBuffer = self.itsSocket.recv( 4096 )
			
			if len( aBuffer ) == 0:
				print "Connection to %s lost. Attempting to reconnect...\n" % self.itsHostname
				self.Connect()

			if self.itsDebugFlag:
				self.itsDebugFile.write( aBuffer )
				self.itsDebugFile.flush()

			aBuffer = aBuffer.rstrip()
			aLine = aBuffer.split()
	
			if aLine[0] == "PING":
				self.SendRaw( "PONG " + aLine[1] )
			elif len( aLine ) > 2:
				if aLine[1] == 'PRIVMSG':
 					aSource = aLine[0].split('!')[0].lstrip(':')
 					aDest = aLine[2]
					aMessage = " ".join(aLine[3:]).lstrip(':')
					
					if aDest == self.itsUsername:
						aTarget = aSource
					else:
						aTarget = aDest
						
					self.itsTarget = aTarget
					self.itsSource = aSource
					self.itsDest = aDest
					self.itsMessage = aMessage
					
					self.LogMessage()

					self.CheckCommand()

				elif aLine[1] == 'QUIT':
 					aSource = aLine[0].split('!')[0].lstrip(':')

					if aSource in self.itsUsers:
						self.itsUsers.remove( aSource )
				elif aLine[1] == 'NICK':
 					aSource = aLine[0].split('!')[0].lstrip(':')
					aNewNick = aLine[2].lstrip(':')

					if aSource in self.itsUsers:
						self.itsUsers[ aNewNick ] = self.itsUsers[ aSource ]
						self.itsUsers.remove( aSource )


		
	def CheckCommand( self ):
		if ( self.itsMessage.startswith( self.itsCommandPrefix ) 
			or self.itsTarget == self.itsSource 
			):
				self.itsMessage = self.itsMessage.lstrip( self.itsCommandPrefix )
				self.itsMessageParts = self.itsMessage.split()
				self.ParseCommand()
		elif self.itsMessage.startswith( self.itsUsername ):
			self.itsMessage = self.itsMessage[ self.itsMessage.find( " " ) : ]
			self.itsMessageParts = self.itsMessage.split()
			self.ParseCommand()
			

	def GetUserRole( self, theUsername ):
		if theUsername in self.itsUsers:
			return self.itsUsers[ theUsername ]
		else:
			return 0

	def ParseCommand( self ):
		aCommand = self.itsMessageParts[0]
		
		if aCommand == "help":
			self.DoHelp()
		elif aCommand == "usage":
			self.DoUsage()
		elif aCommand == "auth":
			self.AuthenticateUser()
		elif aCommand in self.itsCommands:
			if self.GetUserRole( self.itsSource ) >= self.itsCommands[ aCommand ]:
				self.DoCommand( aCommand )
		elif self.GetUserRole( self.itsSource ) >= 100:
			if aCommand == "reload":
				self.LoadCommands( True )
			elif aCommand == "update":
				self.LoadCommands( False )
			elif aCommand == "quit" or aCommand == "exit":
				self.Disconnect()

	def DoCommand( self, theCommand ):
		try:
			aThread = TimeoutThread( target=self.itsModules[ theCommand ].HandleMessage, args=( self, self.itsMessage, self.itsSource, self.itsTarget ) )
			aThread.daemon = True
			aThread.start()
		except:
			traceback.print_exc(file=sys.stdout)

	def DoUsage( self ):
		if len( self.itsMessageParts ) > 1:
			if self.itsMessageParts[1] in self.itsCommands:
				try:
					self.SendText( self.itsModules[ self.itsMessageParts[1] ].Usage(), self.itsTarget )
				except:
					traceback.print_exc(file=sys.stdout)
			else:
				self.SendText( "Unknown command. Try %shelp to view available commands." % self.itsCommandPrefix, self.itsTarget )
		else:
			self.SendText( "Available commands: %s" % ", ".join( self.itsCommands ), self.itsTarget )
			self.SendText( "Try %shelp <command> or %susage <command>" % ( self.itsCommandPrefix, self.itsCommandPrefix ), self.itsTarget )
	
	def DoHelp( self ):
		if len( self.itsMessageParts ) > 1:
			if self.itsMessageParts[1] in self.itsCommands:
				try:
					self.SendText( self.itsModules[ self.itsMessageParts[1] ].Help(), self.itsTarget )
				except:
					traceback.print_exc(file=sys.stdout)
			else:
				self.SendText( "Unknown command. Try %shelp to view available commands." % self.itsCommandPrefix, self.itsTarget )
		else:
			self.SendText( "Available commands: %s" % ", ".join( self.itsCommands ), self.itsTarget )
			self.SendText( "Try %shelp <command> or %susage <command>" % ( self.itsCommandPrefix, self.itsCommandPrefix ), self.itsTarget )
		
	def LogMessage( self ):
		try:
			self.itsDBCursor.execute( 'INSERT INTO `log` VALUES (?,?,?,?,?)', ( self.itsNetworkID, self.itsSource, self.itsTarget, str( time.time() ), self.itsMessage ) )
			self.itsDB.commit()
		except:
			pass
		
	def ConnectToChannel( self, theChannel ):
		if theChannel not in self.itsChannels:
			self.itsSocket.send( "JOIN %s\r\n" % theChannel )
			self.itsChannels.append( theChannel )

	def DisconnectFromChannel( self, theChannel ):
		if theChannel in self.itsChannels:			
			self.itsSocket.send( "PART %s\r\n" % theChannel )
			self.itsChannels.remove( theChannel )
		
	def SendText( self, theText, theTarget ):
		aMessage = "PRIVMSG %s :%s\r\n" % ( theTarget, theText )
		self.itsSendQueue.append( aMessage )
	
	def SendRaw( self, theText ):
		aMessage = "%s\r\n" % theText
		self.itsSendQueue.append( aMessage )
		
	def ProcessSendQueue( self ):
		while self.isConnected:
			if len( self.itsSendQueue ) > 0:
				self.itsSocket.send( self.itsSendQueue.popleft() )
			
			time.sleep( 0.5 ) 
			
	def Disconnect( self ):
		self.isConnected = False
		self.itsDB.close()
		self.itsSocket.close()
		self.itsSendThread.join()
