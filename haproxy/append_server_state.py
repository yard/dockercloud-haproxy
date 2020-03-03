# imports
import re

# regex
server_state_entry = re.compile( "^(\\d+) ([^ ]+) \\d+ ([^ ]+)+ " )
backend_entry = re.compile( "^backend (.+)$" )
server_entry = re.compile( "^ +server ([^ ]+) ([^ ]+)\\:(\\d+) " )

# create a new hashmap to hold all servers. the key is (just to follow haproxy convention)
# is a string of BACKEND_NAME/SERVER_NAME
servers = {}
backend_ids = {}

# read server state file and assembly "known" backends
server_state_file = open( "/var/run/haproxy.servers", "r" )

# iterate over all lines and fine relevant entries
for line in server_state_file:
    # match the line against the regex
    state = server_state_entry.match( line )
    # if the match is there
    if state:
        # memoize backend id
        backend_ids[ state.group( 2 ) ] = state.group( 1 )
        # compose server key
        key = state.group( 2 ) + "/" + state.group( 3 )
        # mark the server as present
        servers[ key ] = True

server_state_file.close()

# read configuration file
haproxy_cfg = open( "/haproxy.cfg", "r" )
# setup state
backend_name = None
new_servers = []

# iterate over all lines and fine relevant entries
for line in haproxy_cfg:
    # try matching the line against backend entry
    backend = backend_entry.match( line )
    if backend:
        # it did match - store backend name
        backend_name = backend.group( 1 )
    # try matching the line against server entry
    server = server_entry.match( line )
    if server:
        key = backend_name + "/" + server.group( 1 )
        if key not in servers:
            new_servers.append( [ backend_name, server.group( 1 ), server.group( 2 ), server.group( 3 ) ] )

# close the file
haproxy_cfg.close()

# compose new server entries and append them to server state
server_state_file = open( "/var/run/haproxy.servers", "a+" )

be_id = 1000000
srv_id = 2000000
for new_server in new_servers:
    backend_id = be_id

    # try re-using backend id if it's a known one
    if new_server[ 0 ] in backend_ids:
        backend_id = int( backend_ids[ new_server[ 0 ] ] )

    line = "%d %s %d %s - 0 0 1 1 1 2 2 0 6 0 0 0 %s %s -" % ( be_id, new_server[ 0 ], srv_id, new_server[ 1 ], new_server[ 2 ], new_server[ 3 ] )
    
    be_id += 1
    srv_id += 1

    server_state_file.write( line )
    server_state_file.write( "\n" )

# close the file
server_state_file.close()