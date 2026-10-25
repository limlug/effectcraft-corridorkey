// Independent EffectCraft wrapper; external CorridorKey retains its own licence.
// Requires the local bridge; EffectCraft scripts cannot start system processes.
(function (host) {
    var i18n = createCorridorKeyI18n(app, typeof $ !== "undefined" ? $ : {});
    var t = i18n.t;
    var ui = host instanceof Panel ? host : new Window("palette", "CorridorKey");
    ui.orientation = "column";
    ui.alignChildren = ["fill", "top"];
    ui.spacing = 8;
    ui.margins = 12;
    function add(parent, type, name, text, props) {
        props = props || {};
        props.name = name;
        return parent.add(type, undefined, text, props);
    }
    function field(parent, label, name, value) {
        var row = parent.add("group");
        row.alignChildren = ["fill", "center"];
        row.add("statictext", undefined, label);
        var control = add(row, "edittext", name, value);
        control.characters = 20;
        control.displayName=label;
        return control;
    }
    function section(title) {
        var panel = tabs.add("tab", undefined, title);
        panel.orientation = "column";
        panel.alignChildren = ["fill", "top"];
        panel.margins = 10;
        // v0.16 draws the first tab row against the header; leave an empty row.
        panel.add("statictext",undefined," ");
        return panel;
    }
    function setting(key, fallback) {
        try { return app.settings.haveSetting("CorridorKey", key) ? app.settings.getSetting("CorridorKey", key) : fallback; }
        catch (error) { return fallback; }
    }
    function save(key, value) {
        try { app.settings.saveSetting("CorridorKey", key, String(value)); } catch (error) {}
    }
    function choice(parent, label, name, items, initial) {
        parent.add("statictext", undefined, label);
        var list = add(parent, "dropdownlist", name, items);
        list.selection = isFinite(initial) && initial >= 0 && initial < items.length ? Math.floor(initial) : 0;
        return list;
    }
    add(ui, "statictext", "intro", t("intro"));
    if(i18n.georgianFallback)add(ui,"statictext","languageNotice",t("This EffectCraft version does not support Georgian. English is used instead."),{multiline:true});
    var connection = add(ui, "statictext", "connection", t("Looking for the local service…"));
    var connect = add(ui, "button", "connect", t("Reconnect"));
    var selection = add(ui, "statictext", "selection", t("Select a video layer."), {multiline: true});
    var tabs = add(ui, "tabbedpanel", "tabs", "");
    tabs.alignChildren = ["fill", "top"];
    var settings = section(t("Clip"));
    var despill = choice(settings, t("Remove green spill"), "despill", [t("Off"), t("Low"), t("Medium"), t("High")], Number(setting("despill", "2")));
    add(settings, "statictext", "despillHelp", t("Reduces green around hair and edges."));
    var useHint = add(settings, "checkbox", "useHint", t("Use a starting mask"));
    var hintGroup = settings.add("group");
    hintGroup.orientation = "column";
    hintGroup.alignChildren = ["fill", "top"];
    hintGroup.visible = false;
    var hint = field(hintGroup, t("Image path"), "hint", "");
    var quality = choice(hintGroup, t("Mask accuracy"), "quality", [t("Precise mask"), t("Rough mask")], 0);
    add(hintGroup, "statictext", "hintHelp", t("PNG/JPG of the first frame in the range.\nWhite stays; black is removed."), {multiline: true});
    add(settings, "statictext", "rangeHelp", t("Different frame rates may need extra frames\nfor accurate import timing."), {multiline:true});
    var range = choice(settings, t("Time range"), "range", [t("Entire source file"), t("Trimmed layer"), t("Work area")], 0);
    var format = choice(settings, t("Output"), "format", [t("MOV with transparency"), t("EXR sequence · Half"), t("EXR sequence · Float")], 0);
    var hintVideo = add(hintGroup, "checkbox", "hintVideo", t("Use a mask video"));
    var layerMask = add(hintGroup, "checkbox", "layerMask", t("Use the layer's closed Add mask"));
    var browse = add(hintGroup, "button", "browse", t("Choose mask…"));
    var finish = section(t("Edges"));
    add(finish, "statictext", "matteHelp", t("Black/white in percent; edges in output pixels."), {multiline:true});
    var black = field(finish, t("Black point %"), "black", "0");
    var white = field(finish, t("White point %"), "white", "100");
    var expand = field(finish, t("Expand / contract px"), "expand", "0");
    var feather = field(finish, t("Feather px"), "feather", "0");
    var refine = add(finish,"button","refine",t("Apply correction without running AI"));
    var presets = choice(finish, t("My presets"), "presets", [t("Default")], 0);
    var presetName = field(finish, t("Name"), "presetName", t("My preset"));
    var presetSave = add(finish, "button", "presetSave", t("Save preset"));
    var presetDelete = add(finish, "button", "presetDelete", t("Delete preset"));
    var previewTab = section(t("Preview"));
    var preview = add(previewTab, "button", "preview", t("Short preview from playhead"));
    var previewSeconds = field(previewTab, t("Duration in seconds"), "previewSeconds", "2");
    var previewOpen = add(previewTab, "button", "previewOpen", t("Open preview video"));
    var previewView = choice(previewTab, t("View"), "previewView", [t("Checkerboard"), t("Matte"), t("Before / after"), t("Original")], 0);
    var play = add(previewTab,"button","play",t("Play"));
    var scrub = add(previewTab,"slider","scrub",0);
    scrub.minvalue=0;scrub.maxvalue=1000;scrub.value=0;
    var playerTime=add(previewTab,"statictext","playerTime",t("Select a finished job, then press Play."));
    var previewImage = add(previewTab, "image", "previewImage", "");
    previewImage.preferredSize = [280, 180];
    add(previewTab, "statictext", "previewHelp", t("Preview uses half the model resolution.\nRemove background creates full quality.\nThe mask must match the range's first frame."), {multiline:true});
    var queueTab = section(t("Jobs"));
    var queueList = choice(queueTab, t("Saved jobs"), "queueList", [], 0);
    var retry=add(queueTab,"button","retry",t("Repeat job unchanged"));
    var retrySettings=add(queueTab,"button","retrySettings",t("Run with current settings"));
    var loadSettings=add(queueTab,"button","loadSettings",t("Load job settings"));
    var insertAll = add(queueTab, "button", "insertAll", t("Insert latest finished results"));
    var cancelAll = add(queueTab, "button", "cancelAll", t("Cancel all pending jobs"));
    var files=section(t("Files"));
    var storageInfo=add(files,"statictext","storageInfo",t("Measuring storage…"),{multiline:true});
    var resourceActions=files.add("group");
    var storageRefresh=add(resourceActions,"button","storageRefresh",t("Refresh storage"));
    var estimateSpace=add(resourceActions,"button","estimateSpace",t("Estimate required space"));
    var estimateInfo=add(files,"statictext","estimateInfo","",{multiline:true});
    var cleanScope=choice(files,t("Clean up"),"cleanScope",[t("Selected job"),t("All finished jobs")],0);
    var cleanCache=add(files,"checkbox","cleanCache",t("Also delete correction data"));
    add(files,"statictext","cleanHelp",t("Deleting correction data requires a new AI run.\nFinished videos and project media are kept."),{multiline:true});
    var cleanActions=files.add("group");
    var planClean=add(cleanActions,"button","planClean",t("Preview cleanup"));
    var doClean=add(cleanActions,"button","doClean",t("Clean up"));doClean.enabled=false;
    var packageCache=add(files,"checkbox","packageCache",t("Include correction data in package"));packageCache.value=true;
    var packageButton=add(files,"button","package",t("Collect project and media…"));
    var fileActions=files.add("group");
    var openPackage=add(fileActions,"button","openPackage",t("Open package folder"));openPackage.enabled=false;
    var cancelFile=add(fileActions,"button","cancelFile",t("Stop file operation"));cancelFile.enabled=false;
    var fileStatus=add(files,"edittext","fileStatus","",{multiline:true,readonly:true});fileStatus.preferredSize=[280,55];
    var actions = ui.add("group");
    var start = add(actions, "button", "start", t("Remove background"));
    var cancel = add(actions, "button", "cancel", t("Cancel"));
    var status = add(ui, "statictext", "status", t("Preparing connection…"), {multiline: true});
    var insert = add(ui, "button", "insert", t("Insert result"));
    insert.enabled = false;
    var reset = add(ui, "button", "reset", t("Prepare new job"));
    reset.visible = false;
    var advanced = add(ui, "checkbox", "advanced", t("Settings and details"));
    var extra = section(t("Service"));
    extra.visible = true;
    advanced.visible = false;
    var warm = add(extra, "checkbox", "warm", t("Keep AI in GPU memory"));
    warm.value = setting("warm", "true") === "true";
    warm.visible=false;
    var keepCache=add(extra,"checkbox","keepCache",t("Keep correction data for later edits"));
    keepCache.value=setting("keepCache","true")==="true";
    var unload = add(extra, "button", "unload", t("Release GPU memory"));
    unload.visible=false;
    var low = add(extra, "checkbox", "low", t("Reduce memory usage"));
    low.value = setting("low", "false") === "true";
    var hide = add(extra, "checkbox", "hide", t("Hide original picture after insertion"));
    hide.value = setting("hide", "true") === "true";
    var manual = add(extra, "checkbox", "manual", t("Configure connection manually"));
    var manualGroup = extra.add("group");
    manualGroup.orientation = "column";
    manualGroup.visible = false;
    var port = field(manualGroup, t("Port"), "port", "9878");
    var token = field(manualGroup, t("Access token"), "token", "");
    var language=choice(extra,t("Language"),"language",[t("EffectCraft language")].concat(i18n.names),0);
    for(var languageIndex=0;languageIndex<i18n.codes.length;languageIndex++)if(i18n.stored===i18n.codes[languageIndex])language.selection=languageIndex+1;
    language.onChange=function(){save("language",index(language)?i18n.codes[index(language)-1]:"auto");status.text=t("Reopen the panel to apply a language change.");};
    var refresh = add(extra, "button", "refresh", t("Refresh now"));
    var details = add(extra, "edittext", "details", "", {multiline: true, readonly: true});
    details.preferredSize = [220, 110];
    var heartbeat = add(ui, "button", "heartbeat", "");
    heartbeat.visible = false;
    tabs.selection = settings;
    var projectSeen = "";
    var records = [], pickerId = null, pickerPurpose="hint", restoring = false, presetData = {};
    var playback=null, playing=false, playOrigin=0, playAnchor=0, playerWaiting=false, lastFramePath="", lastPlayerStep=0;
    var fileTask=null, fileTaskKind="", cleanPlan=null, lastPackage="", packagePresets=null, fileTaskRestored=false;
    try { presetData = JSON.parse(setting("presets", "{}")); } catch (ignore) {}
    var pending = null, connected = false, ticks = 0, task = null, closed = false, lastTick = 0;
    var connectionPath = typeof CORRIDORKEY_CONNECTION_FILE !== "undefined" ? CORRIDORKEY_CONNECTION_FILE : setting("connectionFile", "");

    function owns(object,key){return Object.prototype.hasOwnProperty.call(object,key);}
    function trim(text) { return String(text).replace(/^\s+|\s+$/g, ""); }
    function index(control) { return control.selection ? control.selection.index : 0; }
    function credentials() {
        if (manual.value) return {port: Number(port.text), token: trim(token.text)};
        if (!connectionPath) throw new Error(t("Install the panel with install.py. Manual connection is available under Service."));
        var file = new File(connectionPath);
        try {
            if (!file.open("r")) throw new Error(t("Start CorridorKey for EffectCraft using the shared launcher. The panel connects automatically."));
            return JSON.parse(file.read());
        } finally { file.close(); }
    }
    function request(method, params) {
        var config = credentials(), n = config.port;
        if (!isFinite(n) || n < 1 || n > 65535 || Math.floor(n) !== n)
            throw new Error(t("Invalid port."));
        var socket = new Socket();
        socket.timeout = 0.5;
        try {
            if (!socket.open("127.0.0.1:" + n, "UTF-8"))
                throw new Error(t("Start CorridorKey for EffectCraft using the shared launcher. The panel connects automatically."));
            if (!socket.writeln(JSON.stringify({method: method, params: params || {}, token: config.token})))
                throw new Error(t("Could not send the job."));
            var line = socket.readln();
            if (!line) throw new Error(t("No response from the service."));
            var reply = JSON.parse(line);
            if (!reply.ok) throw i18n.serviceError(reply.error);
            return reply.result;
        } finally { socket.close(); }
    }
    function guarded(action) {
        return function () {
            try { action(); }
            catch (error) { status.text = t("Notice: ") + error.message; if(error.diagnostic) details.text=error.diagnostic; }
        };
    }
    function remember() {
        var saved = [];
        try{saved=JSON.parse(setting("records","[]"));}catch(ignore){}
        for (var i=0;i<records.length;i++) {
            var r=records[i];
            for(var j=saved.length-1;j>=0;j--)if(saved[j].id===r.job.id)saved.splice(j,1);
            saved.push({id:r.job.id,project:r.project,comp:r.comp.id,layer:r.layer.id,path:r.path,
                inserted:r.inserted,insertedLayer:r.insertedLayer});
        }
        if(saved.length>200)saved=saved.slice(saved.length-200);
        save("records", JSON.stringify(saved));
        save("pending", pending ? JSON.stringify({id:pending.job.id,project:pending.project,comp:pending.comp.id,
            layer:pending.layer.id,path:pending.path,inserted:pending.inserted,insertedLayer:pending.insertedLayer}) : "");
    }
    function terminal(job) { return job.state === "completed" || job.state === "failed" || job.state === "cancelled"; }
    function refreshQueue() {
        var selectedId = pending ? pending.job.id : "";
        queueList.removeAll();
        for (var i=0;i<records.length;i++) {
            var r=records[i], label = r.inserted ? t("Inserted") : r.job.preview ? t("Preview") : r.job.state;
            var labels={queued:t("Queued"),running:t("Running"),completed:t("Finished"),failed:t("Failed"),cancelled:t("Cancelled"),cancelling:t("Stopping")};
            queueList.add("item", (labels[label] || label) + " · " + r.layer.name);
            if (r.job.id === selectedId) queueList.selection=i;
        }
    }
    function showPreview() {
        if(playback && pending && playback.jobId===pending.job.id)return;
        if(playback)stopPlayer();
        if (!pending || !pending.job.thumbnails) { previewImage.image=null; return; }
        var path=pending.job.thumbnails[["checker","matte","comparison","original"][index(previewView)]];
        if (path && typeof ScriptUI !== "undefined") previewImage.image=ScriptUI.newImage(new File(path));
    }
    function elapsed(seconds) {
        seconds = Math.max(0, Math.floor(seconds || 0));
        return Math.floor(seconds / 60) + ":" + (seconds % 60 < 10 ? "0" : "") + seconds % 60;
    }
    function chosenLayer(at) {
        var comp = app.project.activeItem;
        if (!(comp instanceof CompItem) || comp.selectedLayers.length < 1)
            throw new Error(t("Select a video layer in the timeline."));
        if (!app.project.file) throw new Error(t("Save the project first."));
        var layer = comp.selectedLayers[at || 0], source = layer.source;
        if (!(source instanceof FootageItem) || !source.file || source.mainSource.isStill || !layer.hasVideo)
            throw new Error(t("Select a video file. Precomps and image sequences are not supported yet."));
        if (layer.locked) throw new Error(t("Unlock the selected layer first."));
        if (!/\.(mov|mp4|mkv|avi|webm|m4v|mxf)$/i.test(source.file.fsName))
            throw new Error(t("Select a supported video file."));
        if (/^0\.16\./.test(app.version)) checkLegacyLayer(layer);
        return {comp: comp, layer: layer, source: source};
    }
    function updateSelection() {
        var valid = false;
        try {
            var selected = chosenLayer(), name = selected.layer.name;
            selection.text = t("Selected ({count}):\n{name}", {count:selected.comp.selectedLayers.length,name:name});
            valid = true;
        }
        catch (error) { selection.text = error.message; }
        start.enabled = connected && valid;
        preview.enabled = connected && valid && app.project.activeItem.selectedLayers.length === 1;
        if (!pending && connected) status.text = valid ? t("Ready. Choose the range and output in Clip.") : t("No suitable layer selected.");
    }
    function update(job) {
        pending.job = job;
        details.text = (job.error ? job.error + "\n" : "") + (job.detail || "").replace(/\r/g, "\n") + t("\nLog: ") + job.log + (job.output ? t("\nResult: ") + job.output : "");
        var labels = {queued: t("Waiting for GPU · position ") + (job.position || 1), running: job.progress ? i18n.progress(job.progress) : t("Removing background"), cancelling: t("Stopping processing…"), cancelled: t("Cancelled. You can start a new job."),
                      completed: t("Finished. Choose Insert result to use the cutout."), failed: job.notice ? t(job.notice) : job.error ? i18n.failure(job) : t("Processing failed. Please check Details.")};
        status.text = pending.inserted ? t("Result inserted. The original remains in the project.") : (labels[job.state] || job.state);
        if (job.state === "running") status.text += " · " + elapsed(job.elapsed);
        insert.enabled = job.state === "completed" && !pending.inserted && !job.preview;
        cancel.enabled = job.state === "running" || job.state === "queued";
        reset.visible = job.state === "completed" || job.state === "cancelled" || job.state === "failed";
        settings.enabled = true;
        if (job.preview && job.state === "completed") status.text = t("Preview ready in Preview. Remove background creates the final clip.");
        refine.enabled=job.state==="completed" && !!job.can_refine;
        retry.enabled=terminal(job);retrySettings.enabled=terminal(job);loadSettings.enabled=true;
        play.enabled=job.state==="completed";
        showPreview();
        updateSelection();
    }
    function copyProperty(from, to) {
        // v0.16 has no AVLayer.replaceSource. Rebuild an independent layer with
        // the documented property API; don't alter the shared original footage.
        if (!to) throw new Error(t("Cannot copy property: ") + from.name);
        if (from.numProperties !== undefined) {
            for (var i = 1; i <= from.numProperties; i++) {
                var child = from.property(i), target;
                if (child.isEffect || child.isMask) target = to.addProperty(child.matchName);
                else target = to.property(child.matchName) || to.property(child.name);
                copyProperty(child, target);
                if (child.isMask) {
                    target.maskMode = child.maskMode;
                    target.inverted = child.inverted;
                    target.locked = child.locked;
                }
                if ((child.isEffect || child.isMask) && target.name !== child.name) target.name = child.name;
                if (child.canSetEnabled) target.enabled = child.enabled;
            }
            return;
        }
        if (from.isSeparationLeader) to.dimensionsSeparated = from.dimensionsSeparated;
        while (to.numKeys) to.removeKey(to.numKeys);
        if (!from.numKeys) to.setValue(from.valueAtTime(0, true));
        else {
            for (var k = 1; k <= from.numKeys; k++) to.setValueAtTime(from.keyTime(k), from.keyValue(k));
            for (var n = 1; n <= from.numKeys; n++) {
                var inEase = from.keyInTemporalEase(n), outEase = from.keyOutTemporalEase(n);
                if (inEase.length && outEase.length) to.setTemporalEaseAtKey(n, inEase, outEase);
                to.setInterpolationTypeAtKey(n, from.keyInInterpolationType(n), from.keyOutInterpolationType(n));
                to.setTemporalContinuousAtKey(n, from.keyTemporalContinuous(n));
                to.setTemporalAutoBezierAtKey(n, from.keyTemporalAutoBezier(n));
                if (from.isSpatial) {
                    to.setSpatialTangentsAtKey(n, from.keyInSpatialTangent(n), from.keyOutSpatialTangent(n));
                    if (from.keySpatialContinuous(n)) to.setSpatialContinuousAtKey(n, true);
                    if (from.keySpatialAutoBezier(n)) to.setSpatialAutoBezierAtKey(n, true);
                }
            }
            if (from.isSpatial) for (var r = 1; r <= from.numKeys; r++)
                if (from.keyRoving(r)) to.setRovingAtKey(r, true);
        }
        if (from.canSetExpression && from.expression) {
            to.expression = from.expression;
            to.expressionEnabled = from.expressionEnabled;
        }
    }
    function checkLegacyLayer(layer) {
        // Advanced layer relationships need native source replacement. Refuse
        // these cases instead of silently producing a different composition.
        var styles = layer.property("ADBE Layer Styles");
        if (layer.threeDLayer || layer.timeRemapEnabled || layer.hasTrackMatte || layer.isTrackMatte ||
            (styles && styles.isModified))
            throw new Error(t("EffectCraft 0.16: render 3D, time remapping, track mattes and active layer styles to video first."));
    }
    function copyLegacyLayer(from, to, timing) {
        to.stretch = from.stretch;
        to.startTime = timing ? timing.start : from.startTime;
        to.inPoint = timing ? timing.begin : from.inPoint;
        to.outPoint = timing ? timing.end : from.outPoint;
        if (from.parent) to.setParentWithJump(from.parent);
        var switches = ["blendingMode", "motionBlur", "effectsActive", "guideLayer", "collapseTransformation",
                        "preserveTransparency", "quality", "samplingQuality", "frameBlendingType",
                        "solo", "shy", "label", "autoOrient", "comment"];
        for (var i = 0; i < switches.length; i++) {
            var key = switches[i];
            if (from[key] !== undefined) to[key] = from[key];
        }
        var groups = ["ADBE Transform Group", "ADBE Effect Parade", "ADBE Mask Parade"];
        for (var g = 0; g < groups.length; g++) {
            var group = from.property(groups[g]);
            if (group) copyProperty(group, to.property(groups[g]));
        }
        for (var m = 1; m <= from.marker.numKeys; m++)
            to.marker.setValueAtTime(from.marker.keyTime(m), from.marker.keyValue(m));
    }
    function connectNow() {
        var hello = request("hello");
        if (hello.api !== 1 || hello.backend !== "stock-cli") throw new Error(t("Unsupported service version."));
        connected = true;
        connection.text = hello.auto_updates === false && /^0\.16\./.test(app.version) ?
            t("Connected · for automatic updates:\nopen EffectCraft through CorridorKey") : t("Connected · ready locally");
        connect.visible = false;
        updateSelection();
    }
    connect.onClick = guarded(connectNow);
    function numeric(control, lo, hi) {
        var value=Number(trim(control.text).replace(",", "."));
        if (!trim(control.text) || !isFinite(value) || value<lo || value>hi) throw new Error(t("{field}: enter a number between {min} and {max}.",{field:control.displayName||control.name,min:lo,max:hi}));
        return value;
    }
    function optionsFor(selected, isPreview) {
        var layer=selected.layer, source=selected.source, comp=selected.comp;
        var fps=source.frameRate, nativeFps=source.mainSource.nativeFrameRate || fps;
        var a=0, b=null, ratio=layer.stretch/100, trimIn=layer.inPoint, trimOut=layer.outPoint;
        if (index(range) || isPreview) {
            checkLegacyLayer(layer);
            if (ratio<=0 || layer.timeRemapEnabled) throw new Error(t("Time ranges require positive speed without time remapping."));
            var begin=layer.inPoint, end=layer.outPoint;
            if (index(range) === 2) { begin=Math.max(begin,comp.workAreaStart); end=Math.min(end,comp.workAreaStart+comp.workAreaDuration); }
            if (isPreview) begin=Math.max(begin,comp.time);
            if (begin>=end) throw new Error(t("The playhead or work area is outside the layer."));
            var compFps=comp.frameRate || fps;
            begin=Math.ceil(begin*compFps-1e-6)/compFps;
            end=Math.ceil(end*compFps-1e-6)/compFps;
            trimIn=begin;trimOut=end;
            a=Math.max(0,(begin-layer.startTime)/ratio*fps/nativeFps);
            b=(end-layer.startTime)/ratio*fps/nativeFps;
        }
        if(!isPreview && index(range)) {
            // EffectCraft snaps startTime to composition frames. Include a short
            // source preroll until the source offset lands exactly on that grid.
            var firstFrame=Math.floor(a*nativeFps+1e-6), aligned=firstFrame;
            var factor=(comp.frameRate || fps)/fps*ratio, searched=0;
            while(aligned>0 && Math.abs(aligned*factor-Math.round(aligned*factor))>1e-6 && searched<10000){aligned--;searched++;}
            if(aligned>0 && Math.abs(aligned*factor-Math.round(aligned*factor))>1e-6)aligned=0;
            a=aligned/nativeFps;
        }
        var bw=numeric(black,0,100)/100, ww=numeric(white,0,100)/100, ex=numeric(expand,-32,32);
        if (bw>=ww) throw new Error(t("Black point must be lower than white point."));
        if (Math.floor(ex)!==ex) throw new Error(t("Enter edge expansion in whole pixels."));
        if (useHint.value && !layerMask.value && !trim(hint.text)) throw new Error(t("Choose a mask image path or disable the starting mask."));
        var exportedMask=null;
        if(useHint.value && layerMask.value) {
            var masks=layer.property("ADBE Mask Parade"), m=masks && masks.numProperties===1?masks.property(1):null;
            if(!m || m.maskMode!==MaskMode.ADD)throw new Error(t("Create exactly one closed Add mask on the layer."));
            var time=layer.startTime+Math.floor(a*nativeFps+1e-6)/fps*ratio;
            var shape=m.property("ADBE Mask Shape").valueAtTime(time,true);
            if(!shape.closed || shape.featherRadii && shape.featherRadii.length)throw new Error(t("Use a closed mask without variable feather points."));
            exportedMask={vertices:shape.vertices,inTangents:shape.inTangents,outTangents:shape.outTangents,
                width:source.width,height:source.height,inverted:!!m.inverted,
                opacity:m.property("ADBE Mask Opacity").valueAtTime(time,true),
                feather:m.property("ADBE Mask Feather").valueAtTime(time,true),
                expansion:m.property("ADBE Mask Offset").valueAtTime(time,true)};
        }
        return {input:source.file.fsName,layer_mask:exportedMask,hint:useHint.value && !layerMask.value && !hintVideo.value ? trim(hint.text) : "",
            hint_video:useHint.value && !layerMask.value && hintVideo.value ? trim(hint.text) : "",hint_quality:index(quality)===1?.75:.95,
            despill:[0,.25,.5,1][index(despill)],low_vram:!!low.value,keep_warm:!!warm.value,keep_cache:!!keepCache.value,
            range_start:a,range_end:b,preview:!!isPreview,preview_seconds:numeric(previewSeconds,.04,10),preview_scale:.5,
            matte_black:bw,matte_white:ww,matte_expand:ex,matte_feather:numeric(feather,0,16),
            output_format:index(format)?"exr":"video",exr_dtype:index(format)===2?"float":"half",
            context:{project:app.project.file.fsName,comp:comp.id,layer:layer.id,path:source.file.fsName,name:layer.name,
                fps:fps,native_fps:nativeFps,start:layer.startTime,"in":layer.inPoint,out:layer.outPoint,stretch:layer.stretch,trim_in:trimIn,trim_out:trimOut}};
    }
    function submit(isPreview) {
        stopPlayer();
        var first=chosenLayer(), count=first.comp.selectedLayers.length;
        if (isPreview && count!==1) throw new Error(t("Select exactly one video layer for preview."));
        var selected=[], options=[];
        for (var i=0;i<(isPreview?1:count);i++) { selected.push(chosenLayer(i)); options.push(optionsFor(selected[i],isPreview)); }
        var jobs=count===1 ? [request("submit",options[0])] : request("submit_batch",{items:options});
        for (var n=0;n<jobs.length;n++) {
            var item=selected[n];
            pending={job:jobs[n],layer:item.layer,source:item.source,comp:item.comp,path:item.source.file.fsName,
                project:app.project.file.fsName,inserted:false};
            records.push(pending);
        }
        remember(); refreshQueue(); update(pending.job);
    }
    function adopt(job,reference){
        stopPlayer();
        pending={job:job,layer:reference.layer,source:reference.source,comp:reference.comp,path:reference.path,project:reference.project,inserted:false};
        records.push(pending);remember();refreshQueue();update(job);
    }
    function finishing(){
        var b=numeric(black,0,100)/100,w=numeric(white,0,100)/100,e=numeric(expand,-32,32);
        if(b>=w)throw new Error(t("Black point must be lower than white point."));
        if(Math.floor(e)!==e)throw new Error(t("Enter edge expansion in whole pixels."));
        return {despill:[0,.25,.5,1][index(despill)],matte_black:b,matte_white:w,matte_expand:e,
            matte_feather:numeric(feather,0,16),output_format:index(format)?"exr":"video",exr_dtype:index(format)===2?"float":"half",keep_warm:!!warm.value};
    }
    refine.onClick=guarded(function(){
        if(!pending)throw new Error(t("Select a finished job first."));
        var reference=pending;adopt(request("refine",{id:pending.job.id,changes:finishing()}),reference);
    });
    retry.onClick=guarded(function(){
        if(!pending)throw new Error(t("Select a job first."));
        var reference=pending;adopt(request("retry",{id:pending.job.id}),reference);
    });
    retrySettings.onClick=guarded(function(){
        if(!pending)throw new Error(t("Select a job first."));
        var selected=chosenLayer();
        if(selected.layer!==pending.layer || selected.comp!==pending.comp)throw new Error(t("Select the job's original layer."));
        var reference={layer:selected.layer,source:selected.source,comp:selected.comp,path:selected.source.file.fsName,project:app.project.file.fsName};
        adopt(request("retry",{id:pending.job.id,changes:optionsFor(selected,!!pending.job.preview)}),reference);
    });
    loadSettings.onClick=guarded(function(){
        if(!pending)throw new Error(t("Select a job first."));
        var o=request("job.options",{id:pending.job.id}),d=[0,.25,.5,1],nearest=0;
        for(var i=1;i<d.length;i++)if(Math.abs(d[i]-o.despill)<Math.abs(d[nearest]-o.despill))nearest=i;
        despill.selection=nearest;black.text=String(o.matte_black*100);white.text=String(o.matte_white*100);
        expand.text=String(o.matte_expand);feather.text=String(o.matte_feather);low.value=o.low_vram;warm.value=o.keep_warm;
        keepCache.value=o.keep_cache!==false;format.selection=o.output_format==="exr"?(o.exr_dtype==="float"?2:1):0;
        useHint.value=!!(o.hint||o.hint_video||o.layer_mask);hintVideo.value=!!o.hint_video;layerMask.value=!!o.layer_mask;
        hint.text=o.hint||o.hint_video||"";hintGroup.visible=useHint.value;quality.selection=o.hint_quality<.9?1:0;
        status.text=t("Job settings loaded. Apply Edges corrections or run again.");
        ui.layout.layout(true);
    });
    function stopPlayer(){
        playing=false;play.text=t("Play");playerWaiting=false;lastFramePath="";
        if(playback){try{request("player.close",{id:playback.id});}catch(ignore){}playback=null;}
    }
    function ensurePlayer(){
        if(!pending || pending.job.state!=="completed")throw new Error(t("Select a finished job first."));
        if(playback && (playback.jobId!==pending.job.id || Date.now()-playback.lastUse>55000))stopPlayer();
        if(!playback){playback=request("player.open",{id:pending.job.id});playback.jobId=pending.job.id;playback.lastUse=Date.now();scrub.value=0;}
    }
    function playerStep(now){
        if(!playback)return;
        var wasWaiting=playerWaiting;
        var seconds=playing && !playerWaiting?playOrigin+(now-playAnchor)/1000:Number(scrub.value)/1000*playback.duration;
        if(seconds>=playback.duration){seconds=Math.max(0,playback.duration-1/playback.fps);playing=false;play.text=t("Play");}
        var frame=request("player.frame",{id:playback.id,seconds:seconds,view:["checker","matte","comparison","original"][index(previewView)],playing:playing});
        playback.lastUse=now;playerWaiting=frame.state!=="ready";
        if(playerWaiting){
            playerTime.text=t("Preparing preview…");
            if(playing){playOrigin=Number(scrub.value)/1000*playback.duration;playAnchor=now;}
        }else{
            if(wasWaiting && playing){playOrigin=frame.seconds;playAnchor=now;}
            scrub.value=Math.round(frame.seconds/playback.duration*1000);
            playerTime.text=t("{time} / {duration} s · {fps} fps",{time:frame.seconds.toFixed(2),duration:playback.duration.toFixed(2),fps:playback.fps});
            if(frame.path!==lastFramePath && typeof ScriptUI!=="undefined"){previewImage.image=ScriptUI.newImage(new File(frame.path));lastFramePath=frame.path;}
        }
        lastPlayerStep=now;
    }
    play.onClick=guarded(function(){ensurePlayer();playing=!playing;play.text=playing?t("Pause"):t("Play");
        playOrigin=Number(scrub.value)/1000*playback.duration;
        if(playing && playOrigin>=playback.duration-1/playback.fps){scrub.value=0;playOrigin=0;}
        playAnchor=Date.now();playerStep(playAnchor);
    });
    scrub.onChanging=scrub.onChange=guarded(function(){var position=scrub.value;ensurePlayer();scrub.value=position;playing=false;play.text=t("Play");playerStep(Date.now());});
    function bytes(n){return n>=1073741824?(n/1073741824).toFixed(2)+" GB":(n/1048576).toFixed(1)+" MB";}
    function references(){
        var paths=[];
        for(var i=1;i<=app.project.numItems;i++){var item=app.project.item(i);if(item instanceof FootageItem && item.file)paths.push(item.file.fsName);}
        return paths;
    }
    function updateStorage(){
        var data=request("storage.report");
        if(data.error){storageInfo.text=i18n.serviceError(data.error).message;return;}
        if(data.total_bytes===undefined){storageInfo.text=t("Measuring storage…");return;}
        storageInfo.text=t("Job files: {total} · free: {free}\nPreview: {preview} · corrections: {cache}",{total:bytes(data.total_bytes),free:bytes(data.free_bytes),preview:bytes(data.preview_bytes),cache:bytes(data.cache_bytes)})+
            (data.gpu?t("\nGPU memory: {used} / {total}",{used:bytes(data.gpu.used_bytes),total:bytes(data.gpu.total_bytes)}):"");
    }
    storageRefresh.onClick=guarded(updateStorage);
    estimateSpace.onClick=guarded(function(){
        var first=chosenLayer(),total=0,frames=0;
        for(var i=0;i<first.comp.selectedLayers.length;i++){
            var selected=chosenLayer(i),source=selected.source,o=optionsFor(selected,false);
            var fps=source.mainSource.nativeFrameRate||source.frameRate;
            var count=Math.round(source.duration*source.frameRate),begin=Math.floor(o.range_start*fps+1e-6);
            var end=o.range_end===null?count:Math.min(count,Math.ceil(o.range_end*fps-1e-6));
            if(end<=begin)throw new Error(t("The range contains no source frames."));
            frames+=end-begin;total+=(end-begin)*source.width*source.height*(16+(o.output_format==="exr"&&o.exr_dtype==="float"?16:8));
        }
        if(!isFinite(total))throw new Error(t("Could not determine source dimensions."));
        estimateInfo.text=t("{frames} frames · raw data: {size}\nBefore compression; actual size depends on footage.",{frames:frames,size:bytes(total)});
    });
    planClean.onClick=guarded(function(){
        if(index(cleanScope)===0 && !pending)throw new Error(t("Select a job or choose all finished jobs."));
        cleanPlan=request("storage.plan",{ids:index(cleanScope)===0?[pending.job.id]:null,include_cache:!!cleanCache.value,references:references()});
        doClean.text=t("Remove {size} of temporary data",{size:bytes(cleanPlan.bytes)});doClean.enabled=cleanPlan.folders>0;
        fileStatus.text=cleanPlan.folders?t("Active previews and project media are protected."):t("No unused temporary data in this selection.");
    });
    function invalidatePlan(){cleanPlan=null;doClean.enabled=false;doClean.text=t("Clean temporary data");}
    cleanScope.onChange=cleanCache.onClick=invalidatePlan;
    doClean.onClick=guarded(function(){
        if(!cleanPlan)throw new Error(t("Preview the cleanup first."));
        fileTask=request("storage.clean",{id:cleanPlan.id});fileTaskKind="cleanup";rememberFileTask();invalidatePlan();cancelFile.enabled=true;
    });
    function startPackage(destination){
        if(!app.project.file)throw new Error(t("Save the project first."));
        var snapshot=request("package.prepare");
        app.run("file.saveCopy",{path:snapshot.path});
        var ids=[];for(var i=0;i<records.length;i++)if(records[i].job.state==="completed" && !records[i].job.preview)ids.push(records[i].job.id);
        fileTask=request("package.start",{id:snapshot.id,destination:destination,project:app.project.file.fsName,
            jobs:ids,include_cache:!!packageCache.value,presets:JSON.stringify(presetData)});
        fileTaskKind="package";rememberFileTask();cancelFile.enabled=true;fileStatus.text=t("Copying and verifying project package…");
    }
    packageButton.onClick=guarded(function(){
        if(!app.project.file)throw new Error(t("Save the project first."));
        if(fileTask && fileTask.state==="running")throw new Error(t("A file operation is already running."));
        pickerId=request("picker.start",{kind:"folder",language:i18n.language}).id;pickerPurpose="package";
    });
    cancelFile.onClick=guarded(function(){if(fileTask)request("task.cancel",{id:fileTask.id});});
    openPackage.onClick=guarded(function(){if(lastPackage && !new Folder(lastPackage).execute())throw new Error(t("Could not open package folder: ")+lastPackage);});
    function rememberFileTask(){save("fileTask",JSON.stringify({id:fileTask?fileTask.id:null,kind:fileTaskKind,package:lastPackage}));}
    function restoreFileTask(){
        if(fileTaskRestored)return;fileTaskRestored=true;
        try{var saved=JSON.parse(setting("fileTask","{}"));lastPackage=saved.package||"";openPackage.enabled=!!lastPackage;
            if(saved.id){fileTask=request("task.status",{id:saved.id});fileTaskKind=saved.kind||"";cancelFile.enabled=fileTask.state==="running";
                if(fileTask.state!=="running"){if(fileTask.state==="completed" && fileTaskKind==="package"){lastPackage=fileTask.result.path;openPackage.enabled=true;fileStatus.text=t("Project package ready: ")+lastPackage;}else fileStatus.text=i18n.taskMessage(fileTask);}}
        }catch(ignore){save("fileTask","");fileTask=null;}
    }
    function pollFiles(){
        if(!fileTask || fileTask.state!=="running")return;
        fileTask=request("task.status",{id:fileTask.id});
        if(fileTask.error)details.text=fileTask.error;
        fileStatus.text=i18n.taskMessage(fileTask)+(fileTask.total?" · "+Math.round(fileTask.done/fileTask.total*100)+" %":"");
        if(fileTask.state!=="running"){
            cancelFile.enabled=false;
            if(fileTask.state==="completed"){
                if(fileTaskKind==="package"){lastPackage=fileTask.result.path;openPackage.enabled=true;fileStatus.text=t("Project package ready: ")+lastPackage;}
                else fileStatus.text=t("Removed {size} of temporary data. Finished media is kept.",{size:bytes(fileTask.result.bytes)});
                updateStorage();
                if(fileTaskKind==="cleanup" && pending)update(request("status",{id:pending.job.id}));
            }
            rememberFileTask();
        }
    }
    start.onClick=guarded(function(){submit(false);});
    preview.onClick=guarded(function(){submit(true);});
    refresh.onClick = guarded(function () { if (pending) update(request("status", {id: pending.job.id})); else connectNow(); });
    cancel.onClick = guarded(function () {
        if (pending) update(request("cancel", {id: pending.job.id}));
    });
    function insertResult() {
        if (!pending || pending.inserted) return;
        update(request("status", {id: pending.job.id}));
        if (pending.job.preview) throw new Error(t("Previews cannot be inserted. Run Remove background first."));
        if (pending.job.state !== "completed") throw new Error(t("The result is not ready yet."));
        if (!app.project.file || app.project.file.fsName !== pending.project ||
            app.project.itemByID(pending.comp.id) !== pending.comp)
            throw new Error(t("The original project was changed or reopened. Import the result manually."));
        var layer = pending.layer;
        if (layer.locked || layer.source !== pending.source || layer.source.file.fsName !== pending.path)
            throw new Error(t("The original layer was removed, locked or its source changed."));
        var c=pending.job.context || {}, changed=false;
        if (c.start !== undefined) changed=Math.abs(layer.startTime-c.start)>1e-6 || Math.abs(layer.inPoint-c["in"])>1e-6 || Math.abs(layer.outPoint-c.out)>1e-6 || Math.abs(layer.stretch-c.stretch)>1e-6 || Math.abs(pending.source.frameRate-c.fps)>1e-6;
        if (changed) throw new Error(t("The original layer's range changed. Process it again."));
        var timing=null;
        if (pending.job.cropped || c.trim_in !== undefined && (Math.abs(c.trim_in-layer.inPoint)>1e-6 || Math.abs(c.trim_out-layer.outPoint)>1e-6)) {
            var offset=(pending.job.first_frame || 0)/pending.source.frameRate*layer.stretch/100;
            var origin=layer.startTime+offset, duration=pending.job.frame_count/pending.source.frameRate*layer.stretch/100;
            timing={start:origin,begin:Math.max(layer.inPoint,origin,c.trim_in===undefined?layer.inPoint:c.trim_in),end:Math.min(layer.outPoint,origin+duration,c.trim_out===undefined?layer.outPoint:c.trim_out)};
        }
        var duplicate = null, footage = null, wasEnabled = layer.enabled, segments=[], replaced=[];
        app.beginUndoGroup(t("Insert CorridorKey"));
        try {
            var opts = new ImportOptions(new File(pending.job.output));
            opts.sequence = !!pending.job.sequence;
            var alphaPreference=app.run("prefs.get",{key:"import.unlabeledAlpha"});
            try {
                if(!opts.sequence && typeof alphaPreference==="string")app.run("prefs.set",{key:"import.unlabeledAlpha",value:"straight"});
                footage=app.project.importFile(opts);
            } finally {
                if(!opts.sequence && typeof alphaPreference==="string")app.run("prefs.set",{key:"import.unlabeledAlpha",value:alphaPreference});
            }
            // Cutout MOV is display-coded sRGB with straight alpha. Match the source's
            // interpreted frame rate so conformed footage keeps its original timing.
            var interpretation={items:[footage.id],alpha:"straight",frameRate:pending.source.frameRate,colorProfile:"srgb",linearLight:!!pending.job.sequence};
            if (pending.job.sequence) interpretation.linearLight=true;
            app.run("file.interpretFootage", interpretation);
            duplicate = layer.duplicate();
            if (!duplicate) throw new Error(t("Could not duplicate the layer."));
            try { if(timing) throw new Error("replaceSource is not supported yet"); duplicate.replaceSource(footage, false); }
            catch (replaceError) {
                if (String(replaceError.message).indexOf("replaceSource is not supported yet") < 0) throw replaceError;
                checkLegacyLayer(layer);
                duplicate.remove();
                duplicate = null;
                duplicate = pending.comp.layers.add(footage);
                copyLegacyLayer(layer, duplicate, timing);
            }
            if (timing && duplicate.startTime !== timing.start) {
                duplicate.startTime=timing.start; duplicate.inPoint=timing.begin; duplicate.outPoint=timing.end;
            }
            duplicate.name = layer.name + " – CorridorKey";
            duplicate.audioEnabled = false;
            duplicate.enabled = true;
            duplicate.moveBefore(layer);
            if (hide.value && timing && wasEnabled) {
                // Preserve the original picture outside a partial work-area render.
                var bounds=[[layer.inPoint,timing.begin,t(" before")],[timing.end,layer.outPoint,t(" after")]];
                for(var z=0;z<bounds.length;z++) if(bounds[z][1]-bounds[z][0]>1e-6){
                    var segment=layer.duplicate();segments.push(segment);
                    segment.name=layer.name+t(" – Original")+bounds[z][2];
                    segment.inPoint=bounds[z][0];segment.outPoint=bounds[z][1];segment.audioEnabled=false;
                }
            }
            if (hide.value) layer.enabled = false;
            // A corrected version must not stack its alpha over the preceding version.
            for(var v=0;v<records.length;v++){
                var older=records[v];
                if(older===pending || older.comp!==pending.comp || older.layer!==pending.layer || !older.inserted || older.insertedLayer===undefined)continue;
                for(var q=1;q<=pending.comp.numLayers;q++){
                    var previous=pending.comp.layer(q);
                    if(previous.id===older.insertedLayer && previous.enabled && previous.source && previous.source.file && previous.source.file.fsName===older.job.output &&
                        Math.abs(previous.inPoint-duplicate.inPoint)<1e-6 && Math.abs(previous.outPoint-duplicate.outPoint)<1e-6){
                        previous.enabled=false;replaced.push(previous);
                    }
                }
            }
            pending.inserted = true;
            pending.insertedLayer = duplicate.id;
            remember();
            insert.enabled = false;
            status.text = t("CorridorKey layer inserted. Original audio stays on the source layer.");
        } catch (error) {
            // Undo groups collect commands but don't roll back a partial script failure.
            for(var v=0;v<replaced.length;v++)replaced[v].enabled=true;
            for(var z=0;z<segments.length;z++)segments[z].remove();
            if (duplicate) duplicate.remove();
            layer.enabled = wasEnabled;
            if (footage) footage.remove();
            throw error;
        } finally { app.endUndoGroup(); }
    }
    insert.onClick=guarded(insertResult);
    insertAll.onClick=guarded(function(){
        var previous=pending, count=0;
        try {
            for(var u=0;u<records.length;u++)records[u].job=request("status",{id:records[u].job.id});
            for(var i=0;i<records.length;i++){
                pending=records[i];var newer=false;
                for(var j=i+1;j<records.length;j++)if(records[j].comp===pending.comp && records[j].layer===pending.layer &&
                    !records[j].job.preview && records[j].job.state==="completed")newer=true;
                if(!newer && !pending.inserted && !pending.job.preview && pending.job.state==="completed"){insertResult();count++;}
            }
        } finally { pending=previous; refreshQueue(); if(pending) update(pending.job); }
        status.text=t("Inserted {count} results.",{count:count});
    });
    cancelAll.onClick=guarded(function(){for(var i=0;i<records.length;i++) if(!terminal(records[i].job)) records[i].job=request("cancel",{id:records[i].job.id}); refreshQueue(); if(pending) update(pending.job);});
    queueList.onChange=guarded(function(){stopPlayer();invalidatePlan();var n=index(queueList);if(records[n]){pending=records[n];update(request("status",{id:pending.job.id}));remember();}});
    previewView.onChange=guarded(function(){if(pending && pending.job.state==="completed"){ensurePlayer();playerStep(Date.now());}else showPreview();});
    previewOpen.onClick=guarded(function(){
        if(!pending || !pending.job.preview || pending.job.state!=="completed")throw new Error(t("Create a short preview first."));
        if(!new File(pending.job.output).execute())throw new Error(t("Could not open the video. Find its path under Details."));
    });
    browse.onClick=guarded(function(){pickerPurpose="hint";pickerId=request("picker.start",{kind:hintVideo.value?"video":"image",language:i18n.language}).id;status.text=t("File picker opened…");});
    keepCache.onClick=function(){save("keepCache",!!keepCache.value);};
    warm.onClick=function(){save("warm",!!warm.value);};
    unload.onClick=guarded(function(){request("release_memory");status.text=t("GPU memory released. AI reloads for the next job.");});
    advanced.onClick = function () { extra.visible = !!advanced.value; ui.layout.layout(true); };
    useHint.onClick = function () { hintGroup.visible = !!useHint.value; ui.layout.layout(true); };
    manual.onClick = function () {
        manualGroup.visible = !!manual.value;
        connected = false;
        connect.visible = true;
        ui.layout.layout(true);
    };
    despill.onChange = function () { save("despill", index(despill)); };
    low.onClick = function () { save("low", !!low.value); };
    hide.onClick = function () { save("hide", !!hide.value); };
    reset.onClick = function () {
        if (!pending || pending.job.state === "running" || pending.job.state === "cancelling") return;
        stopPlayer();
        pending = null;
        remember();
        insert.enabled = false;
        cancel.enabled = false;
        reset.visible = false;
        details.text = "";
        settings.enabled = true;
        updateSelection();
    };
    function restore() {
        if(!app.project.file) return;
        var saved=[], data, all;
        try { saved=JSON.parse(setting("records","[]")); } catch(ignore){}
        if(!saved.length && setting("pending","")) {try{saved=[JSON.parse(setting("pending",""))];}catch(ignore){}}
        try {
            var pack=new File(new File(app.project.file.fsName).parent.fsName+"/corridorkey-package.json");
            if(pack.exists){var imported=request("package.restore",{project:app.project.file.fsName});packagePresets=imported.presets;
                if(packagePresets && typeof packagePresets==="object"){
                    for(var key in packagePresets)if(owns(packagePresets,key) && key!=="__proto__" && key!=="constructor" && !owns(presetData,key))presetData[key]=packagePresets[key];
                    save("presets",JSON.stringify(presetData));presetMenu();
                }}
        } catch(packageError){fileStatus.text=t("Package data: ")+packageError.message;}
        all=request("queue");
        if(!(all instanceof Array)) all=[];
        for(var j=0;j<all.length;j++) {
            var c=all[j].context;
            if(c && c.project===app.project.file.fsName){
                var exists=false;for(var z=0;z<saved.length;z++) if(saved[z].id===all[j].id) exists=true;
                if(!exists)saved.push({id:all[j].id,project:c.project,comp:c.comp,layer:c.layer,path:c.path});
            }
        }
        for(var n=0;n<saved.length;n++) {
            data=saved[n];
            if(data.project!==app.project.file.fsName)continue;
            var comp=app.project.itemByID(data.comp);
            if(!(comp instanceof CompItem))continue;
            for(var i=1;i<=comp.numLayers;i++) {
                var layer=comp.layer(i),source=layer.source;
                if(layer.id===data.layer && source && source.file && source.file.fsName===data.path){
                    var job;
                    try{job=request("status",{id:data.id});}catch(error){if(String(error.diagnostic||error.message).indexOf("Unknown job")>=0)continue;throw error;}
                    var record={job:job,comp:comp,layer:layer,source:source,path:data.path,project:data.project,
                        inserted:!!data.inserted,insertedLayer:data.insertedLayer};
                    if(!record.inserted){
                        for(var q=1;q<=comp.numLayers;q++){
                            var existing=comp.layer(q),footage=existing.source;
                            if(existing!==layer && footage && footage.file && footage.file.fsName===job.output){record.inserted=true;record.insertedLayer=existing.id;break;}
                        }
                    }
                    records.push(record);pending=record;break;
                }
            }
        }
        refreshQueue();
        if(pending)update(pending.job);
    }
    function presetValues() {
        return {despill:index(despill),low:!!low.value,warm:!!warm.value,black:black.text,white:white.text,
            expand:expand.text,feather:feather.text,format:index(format),quality:index(quality)};
    }
    function presetMenu() {
        presets.removeAll();presets.add("item",t("Default"));
        for(var key in presetData)if(owns(presetData,key))presets.add("item",key);
        presets.selection=0;
    }
    presetSave.onClick=guarded(function(){
        var name=trim(presetName.text);
        if(!name || name.length>60 || name===t("Default") || name==="Standard" || name==="__proto__" || name==="constructor")throw new Error(t("Choose another preset name, up to 60 characters."));
        if(numeric(black,0,100)>=numeric(white,0,100))throw new Error(t("Black point must be lower than white point."));
        var ex=numeric(expand,-32,32);if(Math.floor(ex)!==ex)throw new Error(t("Enter edge expansion in whole pixels."));numeric(feather,0,16);
        presetData[name]=presetValues();save("presets",JSON.stringify(presetData));presetMenu();status.text=t("Preset saved: ")+name;
    });
    presets.onChange=guarded(function(){
        var keys=[t("Default")];for(var key in presetData)if(owns(presetData,key))keys.push(key);
        var key=keys[index(presets)],v=index(presets)?presetData[key]:{despill:2,low:false,warm:true,black:"0",white:"100",expand:"0",feather:"0",format:0,quality:0};
        if(!v)return;despill.selection=v.despill;low.value=v.low;warm.value=v.warm;
        black.text=v.black;white.text=v.white;expand.text=v.expand;feather.text=v.feather;format.selection=v.format;quality.selection=v.quality;presetName.text=index(presets)?key:t("My preset");
    });
    presetDelete.onClick=guarded(function(){
        var key=presets.selection?presets.selection.text:"";
        if(key && index(presets)>0){delete presetData[key];save("presets",JSON.stringify(presetData));presetMenu();status.text=t("Preset deleted.");}
    });
    presetMenu();
    function tick() {
        if (closed) return;
        lastTick = Date.now();
        ticks++;
        var currentProject=app.project.file?app.project.file.fsName:"";
        if(projectSeen!==currentProject){stopPlayer();if(projectSeen)remember();records=[];pending=null;restoring=false;projectSeen=currentProject;insert.enabled=false;refreshQueue();}
        updateSelection();
        try {
            if (!connected) {
                if (ticks % 5 !== 1) return;
                connectNow();
            }
            if (pickerId) {
                var pick=request("picker.status",{id:pickerId});
                if(pick.state!=="pending"){pickerId=null;if(pick.state==="selected"){if(pickerPurpose==="package")startPackage(pick.path);else{hint.text=pick.path;useHint.value=true;hintGroup.visible=true;ui.layout.layout(true);}}else if(pick.state==="error")throw i18n.serviceError(pick.error);}
            }
            if (!restoring && currentProject) { restore(); restoring=true; }
            var queueChanged=false;
            for(var q=0;q<records.length;q++) if(records[q]!==pending && !terminal(records[q].job)) {
                records[q].job=request("status",{id:records[q].job.id});queueChanged=true;
            }
            if(queueChanged) refreshQueue();
            restoreFileTask();pollFiles();
            if(ticks%5===1)updateStorage();
            if (pending && pending.inserted && pending.insertedLayer !== undefined &&
                app.project.file && app.project.file.fsName === pending.project &&
                app.project.itemByID(pending.comp.id) === pending.comp) {
                var found = false;
                for (var l = 1; l <= pending.comp.numLayers; l++)
                    if (pending.comp.layer(l).id === pending.insertedLayer) found = true;
                if (!found) { pending.inserted = false; remember(); update(pending.job); }
            }
            if (pending && !terminal(pending.job))
                { update(request("status", {id: pending.job.id})); refreshQueue(); }
        } catch (error) {
            if (String(error.diagnostic||error.message).indexOf("Unknown job") >= 0) {
                if (pending) {
                    pending.job.state = "failed";
                    pending.job.notice = "The service restarted. Start a new job; existing outputs are kept.";
                    update(pending.job);
                } else {
                    save("pending", "");
                    status.text = t("The previous job is unavailable. Existing outputs are kept.");
                }
            } else {
                connected = false;
                start.enabled = false;
                connection.text = t("Local service disconnected");
                connect.visible = true;
                status.text = error.message;
                if(error.diagnostic)details.text=error.diagnostic;
            }
        }
    }
    heartbeat.onClick = function () {
        if(playback && (playing || playerWaiting) && Date.now()-lastPlayerStep>=100){
            try{playerStep(Date.now());}catch(error){stopPlayer();playerTime.text=error.message;}
        }
        if (connected) connection.text = t("Connected · ready locally");
        if (Date.now() - lastTick >= 800) tick();
    };
    $.global.__corridorKeyTick = tick;
    ui.onClose = function () {
        closed = true;
        stopPlayer();
        if (task !== null) app.cancelTask(task);
    };
    cancel.enabled = false;
    if (ui instanceof Window) ui.show(); else ui.layout.layout(true);
    tick();
    task = app.scheduleTask("$.global.__corridorKeyTick()", 1000, true);
})(this);
