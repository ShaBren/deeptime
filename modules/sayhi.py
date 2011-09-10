def HandleMessage( theServerConnection, theMessage, theSource, theTarget ):
	theServerConnection.SendText( "Hi!", theServerConnection.itsTarget )

def Help():
	return "Simple test module to say 'Hi!'"

def Usage():
	return "Usage: sayhi"
