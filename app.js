const express = require("express");
const server = express();
const bodyParser = require('body-parser');
const multer = require('multer');
const form_data = multer();
const fs = require('fs');
const path = require('path');
const spawn = require('child_process').spawn;

server.use(bodyParser.json());
server.use(bodyParser.urlencoded());

server.post("/calculate",cpUpload,async (req,res,next)=> {
    
    const filename = Date.now();
    let content ='';
    const json = req.body;

    console.log(req.file);
    Object.keys(json).forEach(key => {
        
        content+= key +" = "+ json[key]+"\n";
        
        return key;
    });
    console.log(req);
    const inputfile = path.join(__dirname,path.join('input',filename+'.in'));
    fs.writeFile(inputfile,content,error =>
        {if (error){
            console.error(error);
        }
    });
    const ouputfile = path.join(__dirname,path.join('public',filename.toString()));

    const result = spawn('python', [path.join(__dirname,'integrated_analysis.py'),inputfile]);
    result.stderr.on('data', function(data) {
        console.log(data.toString());
	res.sendStatus(401);
    });
    return res.statusCode(200);
    
});
server.use((req, res) => {
  res.sendFile(__dirname + "/404.html");
});

server.listen(80, (err) => {
  if (err) return console.log(err);
  console.log("The server is listening on port 3000");
});