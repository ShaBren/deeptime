def HandleMessage( theMessage, theSource, theTarget, theSendQueue ):
	theSendQueue.append( "JOIN %s\r\n" % ( theMessage.split()[0] ) )

def Help():
	return "Joins a channel"
