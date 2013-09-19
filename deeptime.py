from ServerConnection import ServerConnection

freenode = ServerConnection( 1, True )
freenode.ConnectToChannel( "#shabren" )
freenode.Listen()
