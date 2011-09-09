import socket, string, threading, time, sqlite3, imp, traceback, sys

from os.path import isfile
from collections import deque

class ServerConnection:

	itsChannels = []
	itsUsers = {}
	itsModules = {}
	itsSendQueue = deque()
	itsCommandPrefix = "+"
	isConnected = False
	
	def __init__( self, theNetworkID ):
		self.itsNetworkID = str( theNetworkID )
		
		self.itsDB = sqlite3.connect( "config.db" )
		self.itsDBCursor = self.itsDB.cursor()
		
		self.itsDBCursor.execute( "SELECT * FROM network WHERE network_id=?", self.itsNetworkID )
		aRow = self.itsDBCursor.fetchone()
		
		if not aRow:
			return
		
		self.itsHostname = aRow[1]
		self.itsPort = aRow[2]
		self.itsUsername = aRow[3]
		
		self.itsSocket = socket.socket()
		self.itsSocket.connect( ( self.itsHostname, self.itsPort ) )
		
		self.itsSocket.send( "NICK %s\r\n" % self.itsUsername )
		self.itsSocket.send( "USER %s %s PB :%s\r\n" % ( self.itsUsername, self.itsHostname, self.itsHostname ) )
		
		self.LoadCommands()
		
		self.isConnected = True
		
		self.itsSendThread = threading.Thread( target=self.ProcessSendQueue )
		self.itsSendThread.daemon = True
		self.itsSendThread.start()
		
	def LoadCommands( self ):
		self.itsCommands = {}
		self.itsDBCursor.execute( "SELECT command, required_role FROM command WHERE network=?", self.itsNetworkID )
		
		aFailedImport = []
		
		for aRow in self.itsDBCursor:
			aCommand = aRow[0]
			
			try:
				self.itsModules[ aCommand ] = imp.load_source( aCommand, "modules/%s.py" % aCommand )
				self.itsCommands[ aRow[0] ] = aRow[1]
			except:
				traceback.print_exc(file=sys.stdout)
				aFailedImport.append( aCommand )
		
		if self.isConnected:
			if len( aFailedImport ) == 0:
				self.SendText( "Commands reloaded.", self.itsTarget )
			else:
				self.SendText( "Failed to reload: %s" % ",".join( aFailedImport ), self.itsTarget )
	
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
						
					if aMessage[0] == self.itsCommandPrefix:
						self.itsMessage = self.itsMessage.lstrip( self.itsCommandPrefix )
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
		elif aCommand == "auth":
			self.AuthenticateUser()
		elif aCommand in self.itsCommands:
			if self.GetUserRole( self.itsSource ) >= self.itsCommands[ aCommand ]:
				try:
					self.itsModules[ aCommand ].HandleMessage( self.itsMessage, self.itsSource, self.itsTarget, self.itsSendQueue )
				except:
					traceback.print_exc(file=sys.stdout)
		elif self.GetUserRole( self.itsSource ) >= 100:
			if aCommand == "update":
				self.LoadCommands()
			elif aCommand == "quit":
				self.Disconnect()

	def DoHelp( self ):
		if len( self.itsMessageParts ) > 1:
			if self.itsMessageParts[1] in self.itsCommands:
				try:
					self.SendText( self.itsModules[ self.itsMessageParts[1] ].Help(), self.itsTarget )
				except:
					traceback.print_exc(file=sys.stdout)
			else:
				self.SendText( "Unknown command. Try %shelp to view all available commands." % self.itsCommandPrefix, self.itsTarget )
		else:
			self.SendText( "Available commands: %s" % ",".join( self.itsCommands ), self.itsTarget )
		
	def LogMessage( self ):
		self.itsDBCursor.execute( 'INSERT INTO `log` VALUES (?,?,?,?,?)', ( self.itsNetworkID, self.itsSource, self.itsTarget, str( time.time() ), self.itsMessage ) )
		self.itsDB.commit()
		
	def ConnectToChannel( self, theChannel ):
		if theChannel not in self.itsChannels:			
			self.itsSocket.send( "JOIN %s\r\n" % theChannel )
			self.itsChannels.append( theChannel )
		
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
