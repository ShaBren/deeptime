def HandleMessage( theConnection, theMessage, theSource, theTarget ):
	theConnection.SendText( "http://github.com/ShaBren/deeptime", theTarget )

def Help():
	return "Returns a link to the source code"

def Usage():
	return "Usage: source"
