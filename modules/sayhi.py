def Help():
	return "Simple test module to say 'Hi!'"

def Usage():
	return "Usage: sayhi"

class IRCModule:
	
	def __init__( self, theServerConnection ):
		self.itsServerConnection = theServerConnection
		self.itsServerConnection.RegisterHandler( "PRIVMSG", this.HandleMessage ) )

	def HandleMessage( self, theMessageText, theSource, theTarget ):
		self.itsServerConnection.SendText( theTarget, "Hi!" )
