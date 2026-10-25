const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const catalogs=Object.fromEntries(fs.readdirSync(__dirname+'/locales').filter(n=>n.endsWith('.json')).map(n=>[n.slice(0,-5),JSON.parse(fs.readFileSync(__dirname+'/locales/'+n,'utf8'))]));
const script = 'var CORRIDORKEY_CATALOGS='+JSON.stringify(catalogs)+';\n'+fs.readFileSync(__dirname+'/i18n.js','utf8')+'\n'+fs.readFileSync(__dirname + '/CorridorKey.jsx', 'utf8');
function setup(options = {}) {
    const controls = [], requests = [], commands = [], store = options.store || {};
    let job = {id: 'job1', state: options.state || 'running', log: '/out/log', output: '/out/cutout.mov'};
    let root;
    class Control {
        constructor(type, text, props = {}) {
            Object.assign(this, {type, text, name: props.name, enabled: true, visible: true,
                layout: {layout() {}}, value: false});
        }
        add(type, bounds, text, props) { if(type === "item") { const c={text:bounds,index:this.items.length}; this.items.push(c); return c; } const c = new Control(type, text, props); controls.push(c); return c; }
        set selection(v) { this.selected = typeof v === 'number' ? {index:v,text:this.items && this.items[v] ? this.items[v].text : undefined} : v; }
        get selection() { return this.selected; }
        show() {}
        removeAll() { this.items = []; this.selection=null; }
    }
    class Panel extends Control {}
    class Window extends Control { constructor(...args) { super(...args); root = this; } }
    class CompItem { constructor() { this.id = 1; this.numLayers = 1; this.frameRate=24;this.workAreaStart=5;this.workAreaDuration=2;this.time=5; } }
    class FootageItem { constructor() { this.id = 2; this.file = {fsName: '/shot.mp4'};
        this.width=256;this.height=256;this.duration=.5;this.mainSource = {isStill: false,nativeFrameRate:24}; this.frameRate = 24000 / 1001; }
    }
    const source = new FootageItem(), comp = new CompItem();
    const copy = {remove() { this.removed = true; },
        replaceSource(value) { this.source = value; }, moveBefore(value) { this.before = value; }};
    const layer = {id: 42, source, hasVideo: true, locked: false, name: 'Shot', enabled: true,
        audioEnabled: true, startTime: 3, inPoint: 5, outPoint: 11, stretch: 150,
        duplicate() { Object.assign(copy, {startTime: this.startTime, inPoint: this.inPoint,
            outPoint: this.outPoint, stretch: this.stretch}); return copy; }};
    comp.selectedLayers = [layer]; comp.layer = () => layer;
    const footage = {id: 3, remove() { this.removed = true; }};
    const project = {activeItem: comp, file: {fsName: '/project.ecproj'},
        itemByID() { return comp; }, importFile() { return footage; }};
    let groups = 0, cancelled = false;
    const app = {project, beginUndoGroup() { groups++; }, endUndoGroup() { groups--; },
        run(id, params) { commands.push({id, params}); if(id==="prefs.get" && params.key==="general.language")return options.language||"de"; if(id==="prefs.pages" && options.hostLanguages)return [{key:"general.language",options:options.hostLanguages.map(value=>({value}))}]; },
        settings: {haveSetting(sec, key) { return key in store; }, getSetting(sec, key) { return store[key]; },
            saveSetting(sec, key, value) { store[key] = value; }},
        scheduleTask() { return 1; }, cancelTask() { cancelled = true; }};
    class Socket {
        open() { return options.online !== false; }
        writeln(line) { this.req = JSON.parse(line); requests.push(this.req); return true; }
        readln() { if(options.respond){const value=options.respond(this.req);if(value!==undefined)return JSON.stringify({ok:true,result:value});} return JSON.stringify(options.unknownJob && this.req.method === 'status' ?
            {ok: false, error: 'Unknown job'} : {ok: true, result: this.req.method === 'hello' ? {api: 1,backend:'stock-cli'} : this.req.method === 'queue' ? [] : this.req.method === 'submit_batch' ? this.req.params.items.map((p,i)=>({...job,id:'job'+i,context:p.context})) : job}); }
        close() {}
    }
    class File {
        constructor(path) { this.fsName = path;this.exists=false;this.parent={fsName:'/'}; }
        open() { return true; }
        read() { return JSON.stringify({port: 9878, token: 'auto-token'}); }
        close() {}
    }
    const context = {Panel, Window, CompItem, FootageItem, Socket, app, File,
        ImportOptions: function (file) { this.file = file; }, $: {global: {}},
        ScriptUI:{newImage(file){return {path:file.fsName};}},
        CORRIDORKEY_SYSTEM_LOCALE:options.systemLocale||'en',CORRIDORKEY_CONNECTION_FILE: '/connection.json'};
    vm.runInNewContext(script, context);
    const get = name => controls.find(c => c.name === name);
    return {get, tick: () => context.$.global.__corridorKeyTick(), store, close: () => root.onClose(),
        requests, commands, layer, copy, footage, app, comp, options,
        setJob(value) { job = {...job, ...value}; }, get groups() { return groups; }, get cancelled() { return cancelled; }};
}
let tests = 0;
function test(name, body) { body(); tests++; console.log('ok - ' + name); }
test('automatic connection, presets, automatic status and explicit insertion', () => {
    const s = setup(); assert.match(s.get('connection').text, /Verbunden/);
    s.get('useHint').value = true; s.get('hint').text = '/hint.png'; s.get('despill').selection = 3;
    s.get('start').onClick(); const request = s.requests.find(r => r.method === 'submit');
    assert.equal(request.token, 'auto-token'); assert.equal(request.params.despill, 1); assert.equal(request.params.hint, '/hint.png');
    assert.equal(s.get('insert').enabled, false); s.setJob({state: 'completed'}); s.tick();
    assert.equal(s.get('insert').enabled, true); assert.equal(s.get('start').enabled, true);
    s.get('insert').onClick(); assert.equal(s.copy.source, s.footage);
    for (const key of ['startTime', 'inPoint', 'outPoint', 'stretch']) assert.equal(s.copy[key], s.layer[key]);
    assert.equal(s.layer.enabled, false); assert.equal(s.layer.audioEnabled, true);
    assert.equal(s.copy.audioEnabled, false); assert.equal(s.groups, 0);
    assert.equal(s.commands.find(c=>c.id==='file.interpretFootage').params.frameRate, 24000 / 1001); assert.equal(s.commands.find(c=>c.id==='file.interpretFootage').params.alpha, 'straight');
    const count = s.requests.length; s.get('insert').onClick(); assert.equal(s.requests.length, count);
});
test('missing selection and missing enabled hint never submit', () => {
    const s = setup(); s.comp.selectedLayers = []; s.tick(); assert.equal(s.get('start').enabled, false);
    s.get('start').onClick(); assert.match(s.get('status').text, /Videoebene/);
    s.comp.selectedLayers = [s.layer]; s.get('useHint').value = true; s.get('start').onClick();
    assert.match(s.get('status').text, /Bildpfad/); assert.equal(s.requests.filter(r => r.method === 'submit').length, 0);
});
test('project switch and changed source prevent insertion', () => {
    const s = setup(); s.get('start').onClick(); s.setJob({state: 'completed'});
    s.app.project.file.fsName = '/other.ecproj'; s.get('insert').onClick();
    assert.match(s.get('status').text, /Projekt/); assert.equal(s.copy.source, undefined);
    s.app.project.file.fsName = '/project.ecproj'; s.layer.source.file.fsName = '/different.mp4';
    s.get('insert').onClick(); assert.match(s.get('status').text, /Quelle geändert/);
});
test('failed insertion cleans up and keeps original visible', () => {
    const s = setup(); s.get('start').onClick(); s.setJob({state: 'completed'});
    s.copy.replaceSource = () => { throw new Error('replace failed'); }; s.get('insert').onClick();
    assert.equal(s.copy.removed, true); assert.equal(s.footage.removed, true); assert.equal(s.layer.enabled, true); assert.equal(s.groups, 0);
});
test('failed or cancelled jobs cannot import partial results', () => {
    for (const state of ['failed', 'cancelled', 'cancelling']) {
        const s = setup(); s.get('start').onClick(); s.setJob({state}); s.tick();
        assert.equal(s.get('insert').enabled, false); s.get('insert').onClick(); assert.equal(s.copy.source, undefined);
    }
});
test('v0.16 fallback rebuilds an independent source', () => {
    const s = setup(); s.layer.property = () => null; s.layer.marker = {numKeys: 0}; s.app.version = '0.16.0';
    s.copy.replaceSource = () => { throw new Error('replaceSource is not supported yet'); };
    const rebuilt = {property: () => null, moveBefore() {}};
    s.comp.layers = {add(footage) { rebuilt.source = footage; return rebuilt; }};
    s.get('start').onClick(); s.setJob({state: 'completed'}); s.get('insert').onClick();
    assert.equal(rebuilt.source, s.footage); assert.equal(s.copy.removed, true);
    for (const key of ['startTime', 'inPoint', 'outPoint', 'stretch']) assert.equal(rebuilt[key], s.layer[key]);
});
test('v0.16 rejects advanced unsupported layers before GPU work', () => {
    const s = setup(); s.app.version = '0.16.0'; s.layer.property = () => null; s.layer.threeDLayer = true;
    s.get('start').onClick(); assert.match(s.get('status').text, /3D/); assert.equal(s.requests.filter(r => r.method === 'submit').length, 0);
});
test('connection recovers without typing a token', () => {
    const s = setup({online: false}); assert.equal(s.get('start').enabled, false);
    s.options.online = true; for (let i = 0; i < 5; i++) s.tick();
    assert.match(s.get('connection').text, /Verbunden/); assert.equal(s.get('start').enabled, true);
});
test('reopening restores a job and preferences without saved credentials', () => {
    const first = setup(); first.get('despill').selection = 1; first.get('despill').onChange(); first.get('start').onClick(); first.close();
    assert.equal(first.cancelled, true);
    const reopened = setup({store: first.store, state: 'completed'});
    assert.equal(reopened.get('despill').selection.index, 1); assert.equal(reopened.get('insert').enabled, true);
    assert.equal(JSON.stringify(reopened.store).includes('auto-token'), false);
    reopened.get('insert').onClick(); assert.equal(reopened.copy.source, reopened.footage);
});
test('reset keeps output files and clears saved job link', () => {
    const s = setup(); s.get('start').onClick(); s.setJob({state: 'completed'}); s.tick();
    s.get('reset').onClick(); assert.equal(s.store.pending, ''); assert.equal(s.get('start').enabled, true); assert.equal(s.footage.removed, undefined);
});
test('undo or deletion of the inserted layer makes the result available again', () => {
    const s = setup(); s.copy.id = 99; s.comp.numLayers = 2;
    s.comp.layer = i => i === 1 ? s.copy : s.layer;
    s.get('start').onClick(); s.setJob({state: 'completed'}); s.get('insert').onClick(); s.tick();
    assert.equal(s.get('insert').enabled, false);
    s.comp.numLayers = 1; s.comp.layer = () => s.layer; s.layer.enabled = true; s.tick();
    assert.equal(s.get('insert').enabled, true);
    assert.equal(s.requests.filter(r => r.method === 'submit').length, 1);
});
test('preview options use the playhead and completed previews cannot be inserted',()=>{
 const s=setup();s.layer.property=()=>null;s.get('preview').onClick();
 const r=s.requests.find(r=>r.method==='submit');assert.equal(r.params.preview,true);
 assert.ok(Math.abs(r.params.range_start-(5-3)/1.5*(24000/1001)/24)<1e-8);
 s.setJob({state:'completed',preview:true});s.tick();assert.equal(s.get('insert').enabled,false);
 s.get('insert').onClick();assert.match(s.get('status').text,/Vorschau/);assert.equal(s.copy.source,undefined);
});
test('work area is mapped through stretch and conformed frame rate',()=>{
 const s=setup();s.layer.property=()=>null;s.get('range').selection=2;s.get('start').onClick();
 const r=s.requests.find(r=>r.method==='submit');assert.ok(r);
 assert.equal(r.params.range_start,0);assert.equal(r.params.context.trim_in,5);
 assert.ok(Math.abs(r.params.range_end-(7-3)/1.5*(24000/1001)/24)<1e-8);
 s.layer.stretch=-100;s.get('start').onClick();assert.match(s.get('status').text,/positive/);
});
test('multiple selection submits a batch and retains every job',()=>{
 const s=setup();s.comp.selectedLayers=[s.layer,{...s.layer,id:43,name:'Second'}];s.get('start').onClick();
 const r=s.requests.find(r=>r.method==='submit_batch');assert.equal(r.params.items.length,2);
 assert.equal(r.params.items[1].context.layer,43);assert.equal(JSON.parse(s.store.records).length,2);
});
test('matte validation and presets round trip without copying per-clip hint paths',()=>{
 const s=setup();s.get('black').text='80';s.get('white').text='20';s.get('start').onClick();
 assert.match(s.get('status').text,/Schwarzpunkt/);assert.equal(s.requests.filter(r=>r.method==='submit').length,0);
 s.get('black').text='5';s.get('white').text='95';s.get('expand').text='-2';s.get('feather').text='1,5';
 s.get('presetName').text='Haare';s.get('hint').text='/private-mask.png';s.get('presetSave').onClick();
 const stored=JSON.parse(s.store.presets);assert.equal(stored.Haare.expand,'-2');assert.equal(JSON.stringify(stored).includes('/private-mask'),false);
 s.get('presets').selection=0;s.get('presets').onChange();assert.equal(s.get('black').text,'0');
 s.get('presets').selection=1;s.get('presets').onChange();assert.equal(s.get('black').text,'5');
 s.get('start').onClick();const r=s.requests.find(r=>r.method==='submit');assert.equal(r.params.matte_feather,1.5);
});
test('cropped source begins at the correct timeline offset and EXR uses sequence import',()=>{
 const s=setup();s.layer.property=()=>null;s.layer.marker={numKeys:0};
 const rebuilt={property:()=>null,moveBefore(){}};s.comp.layers={add(footage){rebuilt.source=footage;return rebuilt;}};
 s.get('start').onClick();s.setJob({state:'completed',cropped:true,sequence:true,first_frame:24,frame_count:48});
 s.get('insert').onClick();assert.ok(Math.abs(rebuilt.startTime-(3+24/(24000/1001)*1.5))<1e-8);
 assert.equal(rebuilt.inPoint,5);assert.ok(Math.abs(rebuilt.outPoint-(rebuilt.startTime+48/(24000/1001)*1.5))<1e-8);
 assert.equal(s.commands.find(c=>c.id==='file.interpretFootage').params.linearLight,true);
});
test('changed timing cannot silently attach an old result',()=>{
 const s=setup();s.get('start').onClick();const r=s.requests.find(r=>r.method==='submit');
 s.setJob({state:'completed',context:r.params.context});s.layer.inPoint+=1;s.get('insert').onClick();
 assert.match(s.get('status').text,/Zeitbereich/);assert.equal(s.copy.source,undefined);
});

test('cached correction sends only finishing values and retains the original job',()=>{
 const s=setup({respond(r){if(r.method==='refine')return {id:'job2',state:'queued',log:'/out/log2'};}});s.get('start').onClick();s.setJob({state:'completed',can_refine:true});s.tick();
 assert.equal(s.get('refine').enabled,true);s.get('black').text='5';s.get('expand').text='-2';s.get('refine').onClick();
 const r=s.requests.find(r=>r.method==='refine');assert.equal(r.params.id,'job1');assert.equal(r.params.changes.matte_black,.05);assert.equal(r.params.changes.matte_expand,-2);
 assert.equal('input' in r.params.changes,false);assert.equal(s.requests.filter(r=>r.method==='submit').length,1);
 assert.equal(JSON.parse(s.store.records).length,2);
});
test('retry and retry with current settings keep the source layer reference',()=>{
 const s=setup();s.get('start').onClick();s.setJob({state:'failed'});s.tick();s.get('retry').onClick();
 assert.equal(s.requests.find(r=>r.method==='retry').params.id,'job1');
 s.get('despill').selection=3;s.get('retrySettings').onClick();
 const r=s.requests.filter(r=>r.method==='retry')[1];assert.equal(r.params.changes.despill,1);assert.equal(r.params.changes.context.layer,42);
});
test('internal player preserves the first scrub position and releases its lease on close',()=>{
 const s=setup({respond(r){if(r.method==='player.open')return {id:'lease',duration:2,fps:8};if(r.method==='player.frame')return {state:'ready',seconds:r.params.seconds,path:'/proxy/'+r.params.seconds+'.jpg'};}});
 s.get('start').onClick();s.setJob({state:'completed'});s.tick();s.get('scrub').value=750;s.get('scrub').onChange();
 const r=s.requests.find(r=>r.method==='player.frame');assert.equal(r.params.seconds,1.5);assert.equal(s.get('previewImage').image.path,'/proxy/1.5.jpg');
 s.get('previewView').selection=3;s.get('previewView').onChange();assert.equal(s.requests.filter(r=>r.method==='player.frame').at(-1).params.view,'original');
 s.close();assert.equal(s.requests.filter(r=>r.method==='player.close').at(-1).params.id,'lease');
});
test('cleanup requires a concrete plan and sends no output-deletion command',()=>{
 const s=setup({respond(r){if(r.method==='storage.plan')return {id:'plan',bytes:1048576,folders:1};if(r.method==='storage.clean')return {id:'task',state:'running'};}});
 s.get('start').onClick();s.setJob({state:'completed'});s.tick();s.get('planClean').onClick();assert.equal(s.get('doClean').enabled,true);
 assert.match(s.get('doClean').text,/1.0 MB/);s.get('doClean').onClick();assert.equal(s.requests.find(r=>r.method==='storage.clean').params.id,'plan');
 assert.equal(s.get('doClean').enabled,false);assert.equal(s.requests.some(r=>r.method==='delete_output'),false);
});
test('project packaging saves a copy rather than saving or replacing the open project',()=>{
 const s=setup({respond(r){if(r.method==='picker.start')return {id:'picker'};if(r.method==='picker.status')return {state:'selected',path:'/destination'};
 if(r.method==='package.prepare')return {id:'snapshot',path:'/temporary/snapshot.ecproj'};if(r.method==='package.start')return {id:'copy',state:'running'};if(r.method==='task.status')return {id:'copy',state:'running',message:'copy'};}});
 s.get('package').onClick();s.tick();assert.equal(s.requests.find(r=>r.method==='picker.start').params.kind,'folder');
 assert.equal(s.commands.find(c=>c.id==='file.saveCopy').params.path,'/temporary/snapshot.ecproj');
 assert.equal(s.app.project.file.fsName,'/project.ecproj');assert.equal(s.commands.some(c=>c.id==='file.save'||c.id==='file.saveAs'),false);
 const r=s.requests.find(r=>r.method==='package.start');assert.equal(r.params.destination,'/destination');assert.equal(r.params.include_cache,true);
});

test('reopening the panel resumes an asynchronous file task and keeps the completed package link',()=>{
 const store={fileTask:JSON.stringify({id:'copy',kind:'package',package:''})};
 let completed=false;
 const s=setup({store,respond(r){if(r.method==='task.status')return completed?{id:'copy',state:'completed',result:{path:'/saved/package'},message:'Fertig'}:{id:'copy',state:'running',message:'Copying',done:1,total:2};}});
 assert.equal(s.get('cancelFile').enabled,true);assert.match(s.get('fileStatus').text,/kopiert/);
 completed=true;s.tick();assert.equal(s.get('cancelFile').enabled,false);assert.equal(s.get('openPackage').enabled,true);
 assert.equal(JSON.parse(s.store.fileTask).package,'/saved/package');
});
test('space estimate includes temporary raw frames even without retained correction data',()=>{
 const s=setup();s.get('estimateSpace').onClick();const withCache=s.get('estimateInfo').text;
 s.get('keepCache').value=false;s.get('estimateSpace').onClick();
 assert.match(withCache,/Bilder.*Rohdaten/);assert.equal(withCache,s.get('estimateInfo').text);
 assert.equal(s.requests.some(r=>r.method==='submit'),false);
});
for(const [code,catalog] of Object.entries(catalogs)){
 test('localized workflow '+code,()=>{
  const s=setup({language:code});
  assert.equal(s.get('start').text,catalog['Remove background']);
  assert.equal(s.get('connection').text,catalog['Connected · ready locally']);
  assert.equal(s.get('presetName').text,catalog['My preset']);
  s.get('presetName').text='User_日本語_ქართული';s.get('presetSave').onClick();
  assert.equal(JSON.parse(s.store.presets)['User_日本語_ქართული'].despill,2);
  s.get('start').onClick();assert.equal(s.requests.find(r=>r.method==='submit').params.input,'/shot.mp4');
  s.setJob({state:'completed'});s.tick();assert.equal(s.get('insert').text,catalog['Insert result']);
  s.get('insert').onClick();assert.equal(s.copy.source,s.footage);
  s.comp.selectedLayers=[];s.tick();assert.equal(s.get('selection').text,catalog['Select a video layer in the timeline.']);
 });
}
test('language override persists without changing EffectCraft preferences',()=>{
 const store={language:'ja'},s=setup({language:'de',store});
 assert.equal(s.get('start').text,catalogs.ja['Remove background']);
 s.get('language').selection=1;s.get('language').onChange();
 assert.equal(store.language,'en');assert.equal(s.commands.some(c=>c.id==='prefs.set'),false);
 assert.equal(setup({language:'de',store}).get('start').text,'Remove background');
});
test('system locale aliases and unsupported languages fall back predictably',()=>{
 for(const [locale,code] of [['pt_PT.UTF-8','pt-br'],['zh_TW','zh-hant'],['zh_CN','zh-hans'],['ja_JP','ja'],['ka_GE','ka'],['de_DE','de'],['nl_NL','en'],['__proto__','en'],['constructor','en']]){
  const s=setup({language:'system',systemLocale:locale});assert.equal(s.get('start').text,catalogs[code]['Remove background']);
 }
});
test('unknown-job recovery works with localized service errors',()=>{
 const s=setup({language:'ja',unknownJob:true});s.get('start').onClick();s.tick();
 assert.equal(s.get('status').text,catalogs.ja['The service restarted. Start a new job; existing outputs are kept.']);
});
test('dynamic templates preserve Unicode names and replace every placeholder',()=>{
 const s=setup({language:'ka'});s.layer.name='Haare_日本語_ქართული';s.tick();
 assert.equal(s.get('selection').text,catalogs.ka['Selected ({count}):\n{name}'].replace('{count}','1').replace('{name}',s.layer.name));
 s.get('black').text='invalid';s.get('start').onClick();assert.equal(s.get('status').text.includes('{'),false);
});
test('older hosts never show unreadable Georgian text',()=>{
 const s=setup({language:'ka',hostLanguages:['en','de','ja']});
 assert.equal(s.get('start').text,'Remove background');
 assert.equal(s.get('languageNotice').text,catalogs.en['This EffectCraft version does not support Georgian. English is used instead.']);
});
test('stock CLI backend never silently connects to the old patched backend',()=>{
 const s=setup({respond(r){if(r.method==='hello')return {api:1,version:'0.5.0'};}});
 assert.equal(s.get('start').enabled,false);
 assert.equal(s.get('status').text.includes(catalogs.de['Unsupported service version.']),true);
});
console.log(tests + ' panel checks passed');
