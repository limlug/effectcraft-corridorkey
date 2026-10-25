// ES5: EffectCraft's script runtime and the Node test harness use the same code.
function createCorridorKeyI18n(app, dollar) {
    var catalogs = CORRIDORKEY_CATALOGS;
    var codes = ['en','cs','de','es','fr','pt-br','ru','uk','ka','ja','zh-hans','zh-hant'];
    var names = ['English','Čeština','Deutsch','Español','Français','Português (Brasil)','Русский','Українська','ქართული','日本語','简体中文','繁體中文'];
    function normalize(value) {
        var tag=String(value||'en').toLowerCase().replace(/_/g,'-').split('.')[0];
        if(tag.indexOf('zh')===0)return /hant|tw|hk|mo/.test(tag)?'zh-hant':'zh-hans';
        if(tag.indexOf('pt')===0)return 'pt-br';
        var base=tag.split('-')[0];return Object.prototype.hasOwnProperty.call(catalogs,base)?base:'en';
    }
    var stored='auto', host='system';
    try { if(app.settings.haveSetting('CorridorKey','language'))stored=app.settings.getSetting('CorridorKey','language'); } catch(ignore){}
    try { host=app.run('prefs.get',{key:'general.language'}); } catch(ignore){}
    if(typeof host!=='string')host='system';
    // app.isoLanguage and $.locale are fixed en_US stubs in EffectCraft 0.16.
    // The bridge resolves Match System from EffectCraft's process environment.
    var system=typeof CORRIDORKEY_SYSTEM_LOCALE!=='undefined'?CORRIDORKEY_SYSTEM_LOCALE:'en';
    try {
        if(typeof CORRIDORKEY_CONNECTION_FILE!=='undefined'){
            var connectionFile=new File(CORRIDORKEY_CONNECTION_FILE);
            try {if(connectionFile.open('r'))system=JSON.parse(connectionFile.read()).system_locale||system;}
            finally {connectionFile.close();}
        }
    }catch(ignore){}
    var language=stored==='auto'?normalize(host==='system'?system:host):normalize(stored);
    var supportsGeorgian=!/^0\.16\./.test(app.version||'');
    function inspectOptions(node){
        if(!node || typeof node!=='object')return;
        if(node.key==='general.language' && node.options){
            supportsGeorgian=false;
            for(var n=0;n<node.options.length;n++)if(node.options[n].value==='ka')supportsGeorgian=true;
        }
        for(var key in node)if(Object.prototype.hasOwnProperty.call(node,key)){
            var child=node[key];if(child && typeof child==='object')inspectOptions(child);
        }
    }
    try {inspectOptions(app.run('prefs.pages',{}));}catch(ignore){}
    var requestedLanguage=language;
    if(!supportsGeorgian){
        var georgianIndex=codes.indexOf('ka');codes.splice(georgianIndex,1);names.splice(georgianIndex,1);
        if(language==='ka')language='en';
    }
    function t(key,args) {
        var text=catalogs[language] && catalogs[language][key] || catalogs.en[key] || key;
        return String(text).replace(/\{([a-zA-Z]+)\}/g,function(token,name){return args && args[name]!==undefined?String(args[name]):token;});
    }
    function errorKey(text) {
        var s=String(text||'').toLowerCase();
        if(/out of memory/.test(s))return 'Not enough GPU memory. Enable reduced memory usage and close other GPU apps.';
        if(/no module named/.test(s))return 'A Python package is missing. Check the installation.';
        if(/cuda/.test(s) && /unavailable|requires|driver/.test(s))return 'NVIDIA GPU unavailable. Check the driver and CUDA setup.';
        if(/no space left|nicht genügend freier speicher/.test(s))return 'Not enough disk space. Free some space and try again.';
        if(/korrekturdaten|cache.*(missing|unavailable)|cached.*(missing|unavailable)/.test(s))return 'Correction data is unavailable. Run the AI again with correction data enabled.';
        if(/zuerst laufende/.test(s))return 'Finish active jobs before releasing GPU memory.';
        if(/warteschlange voll/.test(s))return 'The queue is full. Wait for a job to finish.';
        if(/aufräumvorschau/.test(s))return 'Refresh the cleanup preview and try again.';
        if(/zielordner außerhalb/.test(s))return 'Choose a destination outside job and temporary folders.';
        if(/no such file|mediendatei fehlt|vorhandenen zielordner|file.*not found/.test(s))return 'The file or folder is unavailable. Check the path.';
        return 'The service could not complete this action. Technical details are available under Details.';
    }
    function serviceError(raw) {var error=new Error(t(errorKey(raw)));error.diagnostic=String(raw||'');return error;}
    function failure(job) {return t(errorKey((job.detail||'')+' '+(job.error||'')));}
    function progress(p) {
        if(p.done!==null && p.done!==undefined)return t(p.kind==='finishing' || /Kantenkorrektur/.test(p.label||'')?'Finishing · frame {done} of {total}':'Analysis · window {done} of {total}',p);
        return t('Preparing processing…');
    }
    function taskMessage(task) {
        if(task.state==='completed')return t('Finished');
        if(task.state==='cancelled')return t('File operation cancelled.');
        if(task.state==='failed')return t('File operation failed. Technical details are available under Details.');
        var message=String(task.message||'');
        if(/^Prüfe /.test(message))return t('Verifying files…');
        if(/Zwischendaten/.test(message))return t('Cleaning temporary data…');
        return t('Copying files…');
    }
    return {t:t,normalize:normalize,language:language,codes:codes,names:names,stored:stored,georgianFallback:requestedLanguage==='ka' && !supportsGeorgian,
        serviceError:serviceError,failure:failure,progress:progress,taskMessage:taskMessage};
}
