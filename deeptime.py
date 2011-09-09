from ServerConnection import ServerConnection

freenode = ServerConnection( 1 )
freenode.ConnectToChannel( "##bottest" )
freenode.Listen()
