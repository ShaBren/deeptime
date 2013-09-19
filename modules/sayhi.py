def Help():
	return "Simple test module to say 'Hi!'"

def Usage():
	return "Usage: sayhi"

def HandleMessage( theConnection, theMessageText, theSource, theTarget ):
	theConnection.SendText( "Hi!", theTarget )
