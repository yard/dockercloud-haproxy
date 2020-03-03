#!/bin/sh

PID_FILE="/var/run/haproxy.pid"

if kill -0 $(cat $PID_FILE)
then
    echo "haproxy is running - performing hitless reload..."
    
    echo "Dumping current cluster state"
    echo "show servers state" | socat stdio /var/run/haproxy.stats > /var/run/haproxy.servers

    echo "Appending new servers to the server state"
    python /haproxy-src/haproxy/append_server_state.py

    echo "haproxy is running - performing hitless reload..."
    /usr/local/sbin/haproxy -f /haproxy.cfg -p $PID_FILE -sf $(cat $PID_FILE) -x /var/run/haproxy.stats
else
    echo "haproxy is stopped - performing full reload..."
    /usr/local/sbin/haproxy -f /haproxy.cfg -p $PID_FILE -D
fi