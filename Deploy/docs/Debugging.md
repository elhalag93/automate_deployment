# Debugging

Here the errors that your encounter in the process are listed and how you resolve them , analayse them to identity the root cause

Example:

## Error: mv » path not found (simple example)

A directory was not found

### Steps to resolve

1. run `ls la`in the parent folder of the first directory to see if it exists
1. try to cd into the second directory
1. see if path is somehow protected

## Pinging local subdomain & no response

pinging `https://sub1.localhost:8443/` and no response when testing locally

### Problem

Subdomain is not registered in windows hostfile

### Resolve

attach multiple Subdomains in you host file

add host by appending the following to the end of the host file
at `C:\Windows\System32\drivers\etc`

```
   127.0.0.1       sub1.localhost
   127.0.0.1       sub2.localhost
```

# setup.ipynb builds successfully but unittests fail

find out if something is hosted on the server:

1. ssh into the server
2. To see if something is deployed at ports curl with the following command

```js
curl --request GET --url https://lgtest.Kaiserfranz-engineering.de

curl --request GET --url https://aottest.Kaiserfranz-engineering.de

curl --request GET --url https://aottest.Kaiserfranz-engineering.de:8443
```

# Debugging Server.js and pm2

```
pm2 start <path>
```

to start server.js at path

```
pm2 status <processName>
```

to see what the process is doing

```
pm2 logs
```

to see how a process crashed
