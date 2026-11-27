// Reproduce candidates7–12 from prior six-scanner result and exact original.
const fs=require('node:fs');
const reconstruct=require('./2026-11-27-six-scanner-residual.cjs');
const raw=fs.readFileSync(process.argv[2],'utf8'),prior=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const tracks=Array.from({length:6},(_,i)=>prior['scanner'+(i+1)]);
for(let k=7;k<=12;k++){const t=reconstruct(raw,{blocked:tracks.flatMap(x=>x.visits)});tracks.push(t);}
console.log(JSON.stringify(tracks));
