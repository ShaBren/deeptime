def HandleMessage( theMessage, theSource, theTarget, theSendQueue ):
	theSendQueue.append( "PRIVMSG %s :%s\r\n" % ( theTarget, "Hi!" ) )

def Help():
	return "Simple test module to say 'Hi!'"