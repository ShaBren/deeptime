def HandleMessage( theConnection, theMessage, theSource, theTarget ):
	messageParts = theMessage.split()
	
	if len( messageParts ) < 2:
		theConnection.SendText( Usage(), theTarget )
	elif messageParts[ 1 ] == "pick":
		theConnection.itsDBCursor.execute( "SELECT name FROM lunch ORDER BY RANDOM() LIMIT 1" )

		aRow = theConnection.itsDBCursor.fetchone()

		if aRow == None:
			theConnection.SendText( "%s: Error: No lunch options found" % ( theSource, ), theTarget )
		else:
			theConnection.SendText( "%s: Go to %s" % ( theSource, aRow[0] ), theTarget )

	elif messageParts[ 1 ] == "add":
		aString = " ".join( messageParts[2:] )

		theConnection.itsDBCursor.execute( "INSERT INTO lunch VALUES ( ?, ? )", ( aString, theSource ) )
		theConnection.SendText( "%s: %s added to lunch options" % ( theSource, aString ), theTarget )

	elif messageParts[ 1 ] == "delete":
		aString = " ".join( messageParts[2:] )

		theConnection.itsDBCursor.execute( "DELETE FROM lunch WHERE name=?", ( aString, ) )

		if theConnection.itsDBCursor.rowcount > 0:
			theConnection.SendText( "%s: %s removed from lunch options" % ( theSource, aString ), theTarget )
		else:
			theConnection.SendText( "%s: Option %s not found" % ( theSource, aString ), theTarget )

	elif messageParts[ 1 ] == "list":
		theConnection.itsDBCursor.execute( "SELECT name FROM lunch" )

		aString = ""

		aRowSet = theConnection.itsDBCursor.fetchall()

		for aRow in aRowSet:
			aString += " %s," % ( aRow[ 0 ], )

		if len( aString ) > 0:
			theConnection.SendText( "%s: %s" % ( theSource, aString[:-1] ), theTarget )
		else:
			theConnection.SendText( "%s: No lunch options found" % ( theSource, ), theTarget )


def Help():
	return "Provides randomized options for lunch"

def Usage():
	return "Usage: lunch pick; lunch add <restaurant>; lunch list; lunch delete <restaurant>"

def Init():
	return
