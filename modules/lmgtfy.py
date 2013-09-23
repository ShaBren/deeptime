def HandleMessage( theConnection, theMessage, theSource, theTarget ):
	messageParts = theMessage.split()
	
	if len( messageParts ) < 2:
		theConnection.SendText( self.Usage(), theTarget )
	else:
		aString = "+".join( messageParts[1:] )

		theConnection.SendText( "http://www.lmgtfy.com/?q=%s" % ( aString, ), theTarget )

def Help():
	return "Provides a link to LMGTFY"

def Usage():
	return "Usage: lmgtfy <query>"

def Init():
	return
