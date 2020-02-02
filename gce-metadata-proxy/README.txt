This crude proxy provides a simple way to detect and log access to the GCE
metadata server. It is currently set to match and log the deprecated access
to the 0.1 and beta URLs which are set to be shutdown soon.

It requires the following iptables rules,which redirect metadata connections
to the proxy, and redirect connections from the proxy to the actual metadata
server:

### CUT ###

## [client on localhost connects to 169.254.168.254:80]
##   => iptables redirects this to localhost:8040
iptables -t nat -A OUTPUT -p tcp -d 169.254.169.254 --dport 80 \
    -j DNAT --to 127.0.0.1:8040

## [gce-metadata-server-sniffer receives connection on 8040]
##   => opens new connection to 169.254.168.154:8040
##   => iptables redirects this to 169.254.168.254:80
iptables -t nat -A OUTPUT -p tcp -d 169.254.169.254 --dport 8040 \
    -j DNAT --to 169.254.169.254:80

## all connections to 169.254.169.254 go through NAT
iptables -t nat -A POSTROUTING -d 169.254.169.254 -j MASQUERADE
