def HandleMessage( theConnection, theMessage, theSource, theTarget ):
	messageParts = theMessage.split()
	
	if len( messageParts ) < 2:
		theConnection.SendText( self.Usage(), theTarget )
	elif len( messageParts ) == 2:
		theConnection.DisconnectFromChannel( messageParts[1] )
	else:
		for channel in messageParts[1:]:
			theConnection.DisconnectFromChannel( channel )

def Help():
	return "Leaves a channel"

def Usage():
	return "Usage: part <channel> [channel [...]]"

def Init():
	return
