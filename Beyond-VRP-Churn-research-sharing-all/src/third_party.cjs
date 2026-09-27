// Offline differential check. Install rpki-validator@2.14.8; no API requests.
const fs=require('fs'), path=require('path');
const moduleExport=require('rpki-validator');
const RpkiValidator=moduleExport.default || moduleExport;
const root=path.resolve(__dirname,'..');
const transitions=JSON.parse(fs.readFileSync(path.join(root,'results/route-transitions.json')));
const out={package:'rpki-validator',version:require('rpki-validator/package.json').version,scope:'All changed route pairs from the static projection, offline external VRPs',snapshots:[],mismatches:[]};
(async()=>{
  for(const [date,key] of [['2026-09-13','before'],['2026-09-14','after']]){
    const rpki=new RpkiValidator({connector:'external'});
    const input=JSON.parse(fs.readFileSync(path.join(root,`data/ripe-${date}.json`)));
    rpki.setVRPs(input.roas.map(r=>({...r,asn:Number(String(r.asn).replace(/^AS/,''))})));
    await rpki.preCache();
    let checked=0;
    for(const w of transitions){
      const result=await rpki.validate(w.prefix,w.asn);
      const state=result===true?'Valid':result===false?'Invalid':'NotFound';
      if(state!==w[key])out.mismatches.push({date,...w,third_party:state});
      checked++;
    }
    out.snapshots.push({date,checked});rpki.dispose();
    console.log(date,checked,'checked');
  }
  fs.writeFileSync(path.join(root,'results/third-party.json'),JSON.stringify(out,null,2));
  if(out.mismatches.length)throw new Error('Differential validation mismatch');
  console.log('PASS',out.snapshots.reduce((n,x)=>n+x.checked,0));
})().catch(e=>{console.error(e);process.exitCode=1;});
