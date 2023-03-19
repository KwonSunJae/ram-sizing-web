const express = require("express");
const server = express();
const bodyParser = require('body-parser');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const spawn = require('child_process').spawn;
server.use(cors({
    origin: ['*','http://127.0.0.1']
}));

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
server.use(bodyParser.json());
server.use(bodyParser.urlencoded());
server.use("/output",express.static(__dirname+'/ouput'));
server.post("/calculate",async (req,res)=> {
    
    const filename = Date.now();
    let content =`SIZING INPUT,,,,
mission_profile,ram_mission_nominal,,,
CONFIGURATION,,,,
aspect_ratio_wing,${req.body.aspect_ratio_wing},,,
taper_ratio_wing,${req.body.taper_ratio_wing},,,
sweep_wing_leading_edge,${req.body.sweep_wing_leading_edge},,,
num_of_propellers_ctol,${req.body.num_of_propellers_ctol},,,
num_of_propeller_blades,${req.body.num_of_propeller_blades},,,
AERODYNAMICS,,,,
oswald_effy,${req.body.oswald_effy},,,
CD_0,${req.body.CD_0},,,
CL_max,${req.body.CL_max},,,
CL_takeoff,${req.body.CL_takeoff},,,
CD_takeoff,${req.body.CD_takeoff},,,
CD_landing,${req.body.CD_landing},,,
CL_landing,${req.body.CL_landing},,,
PROPULSION,,,,
effy_motor,${req.body.effy_motor},,,
effy_propeller,${req.body.effy_propeller},,,
effy_controller,${req.body.effy_controller},,,
effy_propeller_cruise,${req.body.effy_propeller_cruise},,,
effy_propeller_climb,${req.body.effy_propeller_climb},,,
effy_propeller_descent,${req.body.effy_propeller_descent},,,
effy_propeller_takeoff,${req.body.effy_propeller_takeoff},,,
effy_propeller_landing,${req.body.effy_propeller_landing},,,
ENERGY-SYSTEM,,,,
coef_batt_usable_energy,${req.body.coef_batt_usable_energy},,,
spec_energy_batt_wh_per_kg,${req.body.spec_energy_batt_wh_per_kg},,,
effy_batt,${req.body.effy_batt},,,
coef_propulsion_install,${req.body.coef_propulsion_install},,,
MASS,,,,
mass_frac_subsys,${req.body.mass_frac_subsys},,,
mass_frac_avionics,${req.body.mass_frac_avionics},,,
mass_frac_struct,${req.body.mass_frac_struct},,,
mass_payload,954,,,
passenger_number,${req.body.passenger_number},,,
coef_ground_friction,${req.body.coef_ground_friction},,,
height_obstacle,${req.body.height_obstacle},,,
DESIGN VARIABLE,x0,lb,ub,
mass_total_inp,${req.body.mass_total_inp1},${req.body.mass_total_inp2},${req.body.mass_total_inp3},kg
wing_loading,${req.body.wing_loading1},${req.body.wing_loading2},${req.body.wing_loading3},N/m^2
power_loading,${req.body.power_loading1},${req.body.power_loading2},${req.body.power_loading3},W/N
OBJECTIVE,,,,
calc_total_mass,,,,
mass_total_out,min,,,
CONSTRAINT,,,,
calc_stall_speed,,,,
speed_stall,leq,${req.body.speed_stall},m/s,
CONSTRAINT,,,,
calc_maximum_speed,,,,
speed_max,leq,${req.body.speed_max},m/s,
altitude,${req.body.altitude1},,,
CONSTRAINT,,,,
calc_takeoff_dist,,,,
distance_takeoff,leq,${req.body.distance_takeoff},m,
altitude,${req.body.altitude2},,,
CONSTRAINT,,,,
calc_rate_of_climb,,,,
rate_of_climb,geq,${req.body.rate_of_climb},m/s,
altitude,${req.body.altitude3},,,
`;
    console.log(content);
    const inputfile = path.join(__dirname,path.join('input',filename+''));
    fs.writeFile(inputfile+'.csv',content,error =>
        {if (error){
            console.error(error);
        }
    });
    try {
        const result = spawn('python3', [path.join(path.join(__dirname,'tests'),'sizing_test_nominal_mission.py'),filename]);
        result.stderr.on('data', function(data) {
            console.log(data.toString());
    
        });
    } catch (error) {
        console.log(error);
    }
    await delay(3000);
    const filePath = path.join(__dirname,"output/"+filename+"/report.md"); // or any file format

    // Check if file specified by the filePath exists
    fs.exists(filePath, function (exists) {
        if (exists) {
            // Content-type is very interesting part that guarantee that
            // Web browser will handle response in an appropriate manner.
            res.writeHead(200, {
                "Content-Type": "application/octet-stream",
                "Content-Disposition": "attachment; filename=report.md" 
            });
            fs.createReadStream(filePath).pipe(res);
            return;
        }
        res.writeHead(400, { "Content-Type": "text/plain" });
        res.end("ERROR File does not exist "+ filePath);
    });
    
});
server.get("/test",async (req,res)=> {
    
    const filename = Date.now();
    let content =`SIZING INPUT,,,,
mission_profile,ram_mission_nominal,,,
CONFIGURATION,,,,
aspect_ratio_wing,9.7,,,
taper_ratio_wing,0.586,,,
sweep_wing_leading_edge,0,,,
num_of_propellers_ctol,2,,,
num_of_propeller_blades,6,,,
AERODYNAMICS,,,,
oswald_effy,0.7,,,
CD_0,0.0288,,,
CL_max,2.2,,,
CL_takeoff,0.7,,,
CD_takeoff,0.05,,,
CD_landing,0.05,,,
CL_landing,0.7,,,
PROPULSION,,,,
effy_motor,0.95,,,
effy_propeller,0.8,,,
effy_controller,0.7,,,
effy_propeller_cruise,0.8,,,
effy_propeller_climb,0.7,,,
effy_propeller_descent,0.8,,,
effy_propeller_takeoff,0.5,,,
effy_propeller_landing,0.45,,,
ENERGY-SYSTEM,,,,
coef_batt_usable_energy,0.85,,,
spec_energy_batt_wh_per_kg,800,,,
effy_batt,0.8,,,
coef_propulsion_install,1.3,,,
MASS,,,,
mass_frac_subsys,0.05,,,
mass_frac_avionics,0.02,,,
mass_frac_struct,0.2,,,
mass_payload,954,,,
passenger_number,9,,,
coef_ground_friction,0.04,,,
height_obstacle,10.7,,,
DESIGN VARIABLE,x0,lb,ub,
mass_total_inp,8618,3000,12000,kg
wing_loading,1600,100,2000,N/m^2
power_loading,16,7,50,W/N
OBJECTIVE,,,,
calc_total_mass,,,,
mass_total_out,min,,,
CONSTRAINT,,,,
calc_stall_speed,,,,
speed_stall,leq,36,m/s,
CONSTRAINT,,,,
calc_maximum_speed,,,,
speed_max,leq,120,m/s,
altitude,0,,,
CONSTRAINT,,,,
calc_takeoff_dist,,,,
distance_takeoff,leq,800,m,
altitude,0,,,
CONSTRAINT,,,,
calc_rate_of_climb,,,,
rate_of_climb,geq,6.25,m/s,
altitude,0,,,  
`;
    
    const inputfile = path.join(__dirname,path.join('input',filename+''));
    fs.writeFile(inputfile+'.csv',content,error =>
        {if (error){
            console.error(error);
        }
    });
    try {
        const result = spawn('python3', [path.join(path.join(__dirname,'tests'),'sizing_test_nominal_mission.py'),filename]);
        result.stderr.on('data', function(data) {
            console.log(data.toString());
    
        });
    } catch (error) {
        console.log(error);
    }
    
    return res.send("/output/"+filename+"/report.md");
    
});
server.use((req, res) => {
  res.sendFile(__dirname + "/404.html");
});

server.listen(3000, (err) => {
  if (err) return console.log(err);
  console.log("The server is listening on port 3000");
});