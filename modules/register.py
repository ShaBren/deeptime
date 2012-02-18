import sqlite3

def HandleMessage( theConnection, theMessage, theSource, theTarget ):
	messageParts = theMessage.split()
	
	if len( messageParts ) < 3:
		theConnection.SendText( self.Usage(), theTarget )
	else:
		aDB = sqlite3.connect( "config.db" )
		aCursor = aDB.cursor()
		aCursor.execute( "SELECT * FROM user WHERE username=?", ( messageParts[1], ) )
		
		if aCursor.fetchone() == None:
			aCursor.execute( "INSERT INTO user VALUES ( ?, ?, ?, ? )", ( theConnection.itsNetworkID, messageParts[1], messageParts[2], 1 ) )
			aDB.commit()
			theConnection.SendText( "Successfully added user %s" % messageParts[1], theTarget )
		else:
			theConnection.SendText( "Username already exists!", theTarget )

def Help():
	return "Registers a nick"

def Usage():
	return "Usage: register <nick> <pass>"
