def HandleMessage( theConnection, theMessage, theSource, theTarget ):
	messageParts = theMessage.split()
	
	if len( messageParts ) < 2:
		theConnection.SendText( self.Usage(), theTarget )
	else:
		theConnection.SendText( "Hello, %s!" % ( messageParts[1] ), theTarget )

def Help():
	return "Greets a user"

def Usage():
	return "Usage: greet <user>"

def Init():
	return
