def HandleMessage( theServerConnection ):
	theServerConnection.SendText( "Hi!", theServerConnection.itsTarget )

def Help():
	return "Simple test module to say 'Hi!'"
