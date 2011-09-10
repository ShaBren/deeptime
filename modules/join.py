def HandleMessage( theConnection, theMessage, theSource, theTarget ):
	messageParts = theMessage.split()
	
	if len( messageParts ) < 2:
		theConnection.SendText( self.Usage(), theTarget )
	elif len( messageParts ) == 2:
		theConnection.ConnectToChannel( messageParts[1] )
	else:
		for channel in messageParts[1:]:
			theConnection.ConnectToChannel( channel )

def Help():
	return "Joins a channel"

def Usage():
	return "join <channel> [channel [...]]"
