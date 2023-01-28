var express = require("express");
var fs = require("fs-js");
var https = require("https");
var http = require("http");
const { string } = require("yup");
const configs = JSON.parse(fs.readFileSync("./Deploy/config.json", "utf8"));
var app = express();
var PORT = 8443;
// NOTE @Mohamed that is better than storing all the info in config.json. Because a structure of information is the most effective,
// If the Redundancy is reduced.
var privateKey = fs.readFileSync("./Deploy/SSL/Sslkey.key", "utf8");
var certificate = fs.readFileSync("./Deploy/SSL/JointCer.cer", "utf8");

var credentials = { key: privateKey, cert: certificate };

const models = {
  user: ["set", "get", "post", "delete"],
  article: ["set", "get", "post", ""],
  article: ["set", "get", "post", "delete"],
  methods: ["login", "signup"],
};

function returnModelStruct(models) {
  var strArr = [];
  Object.keys(models).forEach((key) => {
    strArr.push(`<h1>${key}</h1><section>${models[key]}</section><br/>`);
  });
  return strArr.join("");
}

app.get("/", function (req, res) {
  res.send(" hello you are pinging the api.");

  subdomain = req.headers.host.split(".")[0];
  if (subdomain === "sub1") {
    // rerouting
    res.send(" hello you are on the sub1 test subdomain");
  } else if (subdomain === "sub2") {
    // rerouting
    res.send(" hello you are on another subdomain for testing");
  } else if (subdomain === "lgtest") {
    // rerouting
    res.send(" backend respondign on subdomain lgtest");
  } else if (subdomain === "aottest") {
    // rerouting
    res.send(" Backend responding on subdomain aottest");
  } else {
    res.send("you hit an unknown subdmain");
  }
});

app.get("/api/", function (req, res) {
  subdomain = req.headers.host;
  res.send(`The '/api/ url is the root url of all api calls. <br/>
  \n You have the following host:${subdomain} <br/>
  \n the following models are accessble at their respective routes: <br/>
  \n ${JSON.stringify(returnModelStruct(models).replace('"', ""))}
  `);
});
app.get("/api/sample/", function (req, res) {
  subdomain = req.headers.host;
  res.send(`This is a sample for api requests \n host: ${subdomain}`);
});
https.createServer(credentials, app).listen(8443);
http.createServer(app).listen(4000);
